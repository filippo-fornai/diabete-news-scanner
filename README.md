# Medical-News Summarizer Bot

A Telegram bot that scrapes selected Italian medical‑news websites and returns concise summaries on demand.

## Features

- **/scan** — headless Selenium crawl of configured sources (*Aemmedi*, *Diabete Italia*). Builds a numbered list of titles, sends it to every owner in `owners.json`, and shows a reply‑keyboard so the user can pick an article.
- **Interactive reply** — selecting a number calls the OpenAI summariser and returns the *title*, the generated *summary*, and a direct *link* to the article.
- **/cancel** — gracefully aborts any step of the conversation.

## Project layout
```
bot.py                – conversation flow, /scan entry‑point
pages_scripts/
│  ├─ aemmedi_news.py – headless scraper 1
│  └─ diabete_news.py – headless scraper 2
summerize_openai.py   – async summariser (map‑reduce)
owners.json           – Telegram IDs allowed to receive scans
.env                  – secrets (BOT_TOKEN, OPENAI_API_KEY)
```

## Quick‑start

```bash
pip install python-telegram-bot selenium tiktoken openai python-dotenv
# configure .env
echo "BOT_TOKEN=<your-telegram-bot-token>"   >> .env
echo "OPENAI_API_KEY=<your-openai-api-key>" >> .env

python bot.py
```

Requires Python ≥ 3.10 and Chrome/Chromium with matching chromedriver.

---

