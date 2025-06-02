from typing import List
import tiktoken
from openai import AsyncOpenAI
import asyncio

from dotenv import load_dotenv
load_dotenv(".env")

_MODEL_NAME = "gpt-3.5-turbo"      # 128 k context, low latency
_MAX_TOK = 8192                  # max input tokens you want to feed
_MAX_OUT = 200                   # ≃ 1–2 paragraphs
_client = AsyncOpenAI()

_enc = tiktoken.encoding_for_model("gpt-3.5-turbo")  # works for all chat models

def _tokens(s: str) -> int:
    return len(_enc.encode(s))

def _split_sentences(text: str, max_tok: int) -> List[str]:
    out, buff = [], []
    tok_total = 0
    for sent in text.split(". "):
        tok = _tokens(sent)
        if tok_total + tok > max_tok and buff:
            out.append(". ".join(buff))
            buff, tok_total = [], 0
        buff.append(sent)
        tok_total += tok
    if buff:
        out.append(". ".join(buff))
    return out

async def _one_call(chunk: str) -> str:
    sys = "You are an expert medical editor. Provide a concise, fact-focused summary."
    usr = f"Summarise the following article section:\n\n{chunk}"
    rsp = await _client.chat.completions.create(
        model=_MODEL_NAME,
        messages=[{"role": "system", "content": sys},
                  {"role": "user", "content": usr}],
        max_tokens=_MAX_OUT,
        temperature=0.3,
    )
    return rsp.choices[0].message.content.strip()

async def summarise(text: str) -> str:
    if _tokens(text) <= _MAX_TOK:
        return await _one_call(text)

    # map phase
    chunks = _split_sentences(text, _MAX_TOK - 1024)   # leave headroom
    partials = await asyncio.gather(*[_one_call(c) for c in chunks])

    # reduce phase – single final call
    joined = "\n".join(f"- {p}" for p in partials)
    return await _one_call(joined)
