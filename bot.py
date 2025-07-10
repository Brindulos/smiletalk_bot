import os
import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Chargement des clés depuis les variables d’environnement
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
PORT = int(os.environ.get("PORT", 10000))
RENDER_URL = os.getenv("RENDER_EXTERNAL_HOSTNAME")

# Configuration des logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Flask app pour Render
app = Flask(__name__)

# Création de l'application Telegram
telegram_app = ApplicationBuilder().token(TOKEN).build()


# === HANDLERS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bonjour, je suis le bot SmileTalk 🤖")


# Ajout du handler à l’application
telegram_app.add_handler(CommandHandler("start", start))


# === FLASK ROUTES POUR RENDER ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telegram_app.bot._parse_update(request.get_json(force=True))
    telegram_app.update_queue.put_nowait(update)
    return "OK"


@app.route("/", methods=["GET"])
def index():
    return "Bienvenue sur le bot SmileTalk (Render Web Service est actif)"


# === LANCEMENT DU WEBHOOK ===
if __name__ == "__main__":
    telegram_app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"https://{RENDER_URL}/{TOKEN}"
    )
