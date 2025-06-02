from dotenv import load_dotenv
from pages_scripts.aemmedi_news import aemmedi_news
from pages_scripts.diabate_news import diabete_news
from telegram import ReplyKeyboardMarkup, Update,ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ChatMemberHandler, Application,ContextTypes,ConversationHandler
import logging
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import os
import json
import asyncio
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import signal
from summerize_openai import summarise

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def chunk_list(lst, n=3):
    return [lst[i:i+n] for i in range(0, len(lst), n)]

def triage(input_list):
    return chunk_list(input_list, 3)

load_dotenv(".env")
load_dotenv("config.env")

CHOOSING_ARTICLE = 1

with open("owners.json", "r") as file:
    owners = json.load(file)

async def app_start(application: Application):
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

def signal_handler(signum, frame):
    print("Received signal: ", signum)
    loop = asyncio.get_event_loop()
    loop.call_soon_threadsafe(stop.set)
stop = asyncio.Event()

async def scan_handler(update: Update, context:ContextTypes.DEFAULT_TYPE):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=options)

    results=[]
    results.append(aemmedi_news(driver))
    results.append(diabete_news(driver))

    message = f'*{escape_markdown("Ultime notizie\n",version=2)}*'
    counter = 0
    counter_list = []
    for result in results:
        message += f'```{escape_markdown(f"Sito {result['source']}\n",version=2)}```'
        message += escape_markdown('\n',version=2)

        for n in result['articles']:
            counter_list.append(str(counter))

            message += f'*[{counter}  {escape_markdown(f"{n['title']}",version=2)}]'
            message += f'({escape_markdown(f"{n['link']}",version=2)})*'
            message += escape_markdown('\n\n',version=2)

            counter += 1


        message += escape_markdown('\n',version=2)

    all_articles = []
    for result in results:
        all_articles.extend(result['articles'])

    context.user_data['articles'] = all_articles
    
    for owner in owners:
        await update.message.reply_text(
            text=message,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
            reply_markup=ReplyKeyboardMarkup(keyboard=triage(counter_list),
                                            resize_keyboard=True,
                                            one_time_keyboard=True,
                                            input_field_placeholder='Seleziona un numero per riassumere l\'articolo',

                                            )
        )
        
    driver.close()
    driver.quit()

    return CHOOSING_ARTICLE

    
async def choose_article(update:Update, context:ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    article = context.user_data['articles'][int(number)]
    message=''

    # print(f"Selected article: {article['title']}")
    # message = f"*{escape_markdown(article['title'], version=2)}*\n\n"
    # message += escape_markdown(article['description'][:9999], version=2) + '\n\n'
    message = f"*{escape_markdown(article['title'], version=2)}*"
    message += escape_markdown('\n\n', version=2)
    message += escape_markdown(await summarise(article['description']), version=2)
    message += escape_markdown('\n\n', version=2)
    message += f"[{escape_markdown('Link all\'articolo', version=2)}]({escape_markdown(article['link'], version=2)})"

    await update.message.reply_text(
        text=message,
        parse_mode=ParseMode.MARKDOWN_V2,
        disable_web_page_preview=True,
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

# Cancel handler
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def app_add_handlers(application: Application):

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("scan", scan_handler)],
        states={
            CHOOSING_ARTICLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_article)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    await application.bot.set_my_commands([
        ("scan", "Scan sites for the latest news"),
    ])


async def main():
    try:
        application = (ApplicationBuilder().token(os.getenv('BOT_TOKEN'))
            .get_updates_read_timeout(30)
            .get_updates_connect_timeout(30)
            .get_updates_write_timeout(30)
            .build())
        
        await app_add_handlers(application)
        
        await app_start(application)

        while not stop.is_set():
            try:
                await asyncio.sleep(2)
            except (KeyboardInterrupt,asyncio.CancelledError):
                break
        
        # scheduler.shutdown(wait=True)
        try:
            # Stop the other asyncio frameworks here
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

        except Exception as e:
            print(e)
            
    except Exception as e:
        print(e)
        logging.error(f"Error in main: {e}")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())


    
    

    
