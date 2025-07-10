from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from smiletalk_engine import df, analyser_reponse_chatgpt as analyser_reponse
import time
import os
import sys

# --- Configuration initiale ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # 🔐 Définie dans .env ou Render
WEBHOOK_URL = "https://smiletalk-bot-1.onrender.com/webhook"

if not TOKEN:
    print("❌ ERREUR : TELEGRAM_BOT_TOKEN n’est pas défini dans les variables d’environnement.")
    sys.exit(1)

app = FastAPI()
bot_app = ApplicationBuilder().token(TOKEN).updater(None).build()  # ✅ Pas de Updater (incompatible Python 3.13)

# --- Sessions utilisateurs ---
user_sessions = {}

# --- Commande /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue dans le Smile Talk Training Bot !")

# --- Commande /entrainement ---
async def entrainement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = df.sample(1).iloc[0]
    user_sessions[user_id] = {
        "row": row,
        "timestamp": time.time(),
        "relance_envoyee": False
    }
    await update.message.reply_text(f"🎯 Situation à traiter ({row['public']}):\n\n{row['situation']}")

# --- Réception de messages utilisateur ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)

    if not session or time.time() - session["timestamp"] > 300:
        await update.message.reply_text("👉 Envoie d'abord /entrainement pour démarrer.")
        return

    row = session["row"]
    relance_envoyee = session.get("relance_envoyee", False)
    texte_de_reference = row["relance"] if relance_envoyee and row.get("relance", "").strip() else row["situation"]

    feedback_list, bonne_reponse, info_op = analyser_reponse(update.message.text, row, texte_de_reference)
    feedback = "\n".join(feedback_list)

    exemple_attendu = row["bonne-reponse-relance"] if relance_envoyee and row.get("bonne-reponse-relance", "").strip() else row["bonne-reponse"]
    info_op = info_op if not relance_envoyee else ""

    if relance_envoyee:
        await update.message.reply_text(
            f"📋 Voici ton 2e feedback pédagogique (sur la relance) :\n{feedback}\n\n"
            f"💬 Exemple attendu :\n{exemple_attendu}"
        )
        user_sessions.pop(user_id, None)
    else:
        message = f"📋 Voici ton feedback pédagogique :\n{feedback}\n\n" \
                  f"💬 Exemple attendu :\n{exemple_attendu}"
        if info_op:
            message += f"\n\nℹ️ Info opérationnelle :\n{info_op}"
        await update.message.reply_text(message)

        if row.get("relance", "").strip():
            session["relance_envoyee"] = True
            await update.message.reply_text(f"🙋‍♂️ Le spectateur insiste :\n\n\"{row['relance']}\"")
        else:
            user_sessions.pop(user_id, None)

# --- Ajout des Handlers ---
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("entrainement", entrainement))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook FastAPI ---
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

@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()
