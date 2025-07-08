from fastapi import FastAPI
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8075264265:AAHojOOYSZJB3s9ahH2sYi2_c3ZbFo6SUNY"

app = FastAPI()
bot_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue dans le Smile Talk Training Bot !")

bot_app.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def startup():
    await bot_app.initialize()
    await bot_app.start()
    print("Bot démarré")

@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()
