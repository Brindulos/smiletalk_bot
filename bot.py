from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8075264265:AAHojOOYSZJB3s9ahH2sYi2_c3ZbFo6SUNY"
WEBHOOK_URL = "https://smiletalk-bot-1.onrender.com/webhook"

app = FastAPI()
bot_app = ApplicationBuilder().token(TOKEN).build()

# Quand on tape /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue dans le Smile Talk Training Bot !")

bot_app.add_handler(CommandHandler("start", start))

# Point d'entrée webhook pour Telegram
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(url=WEBHOOK_URL)
    print("✅ Bot démarré avec webhook")

@app.on_event("shutd_

