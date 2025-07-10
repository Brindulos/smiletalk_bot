import os
import pandas as pd
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

openai.api_key = os.getenv("OPENAI_API_KEY")

# Chargement du CSV (si tu en as besoin)
df = pd.read_csv("SITUATIONS.csv", sep=";")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue sur SmileTalk ! Envoie ta réponse quand tu es prêt.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = f"Réponds comme un formateur du Parc : {update.message.text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    feedback = response.choices[0].message.content
    await update.message.reply_text(feedback)

def main():
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot SmileTalk lancé...")
    app.run_polling()

if __name__ == "__main__":
    main()
