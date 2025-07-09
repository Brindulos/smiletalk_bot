from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from smiletalk_engine import df, analyser_reponse
import time

user_sessions = {}

TOKEN = "8075264265:AAHojOOYSZJB3s9ahH2sYi2_c3ZbFo6SUNY"  # 🔒 à remplacer par ton token
WEBHOOK_URL = "https://smiletalk-bot-1.onrender.com/webhook"

app = FastAPI()
bot_app = ApplicationBuilder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue dans le Smile Talk Training Bot !")

async def entrainement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    row = df.sample(1).iloc[0]
    user_sessions[user_id] = {
        "row": row,
        "timestamp": time.time(),
        "relance_envoyee": False
    }
    await update.message.reply_text(f"🎯 Situation à traiter ({row['public']}):\n\n{row['situation']}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)

    if session is None or "timestamp" not in session or (time.time() - session["timestamp"] > 300):
        await update.message.reply_text("👉 Commence par envoyer la commande /entrainement pour recevoir une situation.")
        return

    row = session["row"]
    relance_envoyee = session.get("relance_envoyee", False)

    # Choix du texte de référence
    texte_de_reference = row["relance"] if relance_envoyee and isinstance(row.get("relance"), str) and row["relance"].strip() else row["situation"]

    feedback_list, bonne_reponse, info_op = analyser_reponse(update.message.text, row, texte_de_reference)
    feedback = "\n".join(feedback_list)

    # Sélection de l'exemple attendu en fonction de la relance
    if relance_envoyee and isinstance(row.get("bonne-reponse-relance"), str) and row["bonne-reponse-relance"].strip():
        exemple_attendu = row["bonne-reponse-relance"]
    else:
        exemple_attendu = row["bonne-reponse"]

    if relance_envoyee:
        await update.message.reply_text(
            f"📋 Voici ton 2e feedback pédagogique (sur la relance) :\n{feedback}\n\n"
            f"💬 Exemple attendu :\n{exemple_attendu}"
        )
        user_sessions.pop(user_id, None)  # Session terminée
    else:
        await update.message.reply_text(
            f"📋 Voici ton feedback pédagogique :\n{feedback}\n\n"
            f"💬 Exemple attendu :\n{exemple_attendu}\n\n"
            f"ℹ️ Info opérationnelle :\n{info_op}"
        )
        relance = str(row.get("relance", "")).strip()
        if relance:
            session["relance_envoyee"] = True
            await update.message.reply_text(f"🙋‍♂️ Le spectateur insiste :\n\n\"{relance}\"")
        else:
            user_sessions.pop(user_id, None)

# Handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("entrainement", entrainement))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook
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
