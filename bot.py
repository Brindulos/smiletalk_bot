from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from smiletalk_engine import df, analyser_reponse
import time

# Dictionnaire pour stocker les situations envoyées par utilisateur
user_sessions = {}

TOKEN = "8075264265:AAHojOOYSZJB3s9ahH2sYi2_c3ZbFo6SUNY"  # 🔒 À masquer pour production
WEBHOOK_URL = "https://smiletalk-bot-1.onrender.com/webhook"

app = FastAPI()
bot_app = ApplicationBuilder().token(TOKEN).build()

# Commande /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue dans le Smile Talk Training Bot !")

# Commande /entrainement
async def entrainement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = df.sample(1).iloc[0]
    user_sessions[user_id] = {
        "row": row,
        "timestamp": time.time(),
        "relance_envoyee": False
    }
    await update.message.reply_text(f"🎯 Situation à traiter ({row['public']}):\n\n{row['situation']}")

# Réponse utilisateur
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)

    if session is None or "timestamp" not in session or (time.time() - session["timestamp"] > 300):
        await update.message.reply_text("👉 Commence par envoyer la commande /entrainement pour recevoir une situation.")
        return

    row = session["row"]
    relance_envoyee = session.get("relance_envoyee", False)
    relance = str(row.get("relance", "")).strip()

    # Si relance déjà envoyée → feedback sur la relance
    if relance_envoyee:
        row["relance_utilisee"] = True
        texte_de_reference = relance
    else:
        texte_de_reference = row['situation']

    # Appel à l'analyse avec la bonne base de comparaison
    feedback_list, feedback_ideal, info_op = analyser_reponse(update.message.text, row, texte_de_reference)
    feedback = "\n".join(feedback_list)

    await update.message.reply_text(
        f"📋 Voici ton feedback pédagogique :\n{feedback}\n\n"
        f"💬 Exemple attendu :\n{row['bonne-reponse']}\n\n"
        f"ℹ️ Info opérationnelle :\n{info_op}"
    )

    # 🔁 Envoie la relance si elle existe et pas encore envoyée
    if relance and not relance_envoyee:
        await update.message.reply_text(f"🙋‍♂️ Le spectateur insiste :\n\n\"{relance}\"")
        session["relance_envoyee"] = True
    else:
        # Fin de session si relance déjà faite ou absente
        user_sessions.pop(user_id, None)

# 🎯 Brancher les handlers à l'app Telegram
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("entrainement", entrainement))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# 🌐 Route webhook pour Telegram
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"status": "ok"}

# 🚀 Démarrage du bot
@app.on_event("startup")
async def startup():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(url=WEBHOOK_URL)
    print("✅ Bot démarré avec webhook")

@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()

async def shutdown():
    await bot_app.stop()
