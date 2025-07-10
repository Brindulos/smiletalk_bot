import os
import random
import pandas as pd
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import openai

# 🔧 Logging
logging.basicConfig(level=logging.INFO)

# ✅ Chargement du fichier CSV
df = pd.read_csv("SITUATIONS.csv", sep=";")

# ✅ Mémoire temporaire pour les utilisateurs
user_state = {}

# ✅ API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # 🔀 Choix aléatoire d’une situation
    row = df.sample().iloc[0]

    user_state[user_id] = {
        "step": 1,
        "situation": row["situation"],
        "relance": row["relance"]
    }

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎯 Situation à gérer :\n\n{row['situation']}\n\nQue répondez-vous ?"
    )

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text

    if user_id not in user_state:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Utilise la commande /start pour commencer une situation."
        )
        return

    state = user_state[user_id]

    # 🧠 Étape 1 : réponse à la situation initiale
    if state["step"] == 1:
        feedback, exemple = analyse_reponse(message, state["situation"], "")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📋 Feedback pédagogique :\n{feedback}\n\n💬 Exemple attendu :\n{exemple}"
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🙋‍♂️ Le spectateur insiste :\n\n\"{state['relance']}\"\n\nQue lui répondez-vous ?"
        )

        state["step"] = 2

    # 🧠 Étape 2 : réponse à la relance
    elif state["step"] == 2:
        feedback, exemple = analyse_reponse(message, state["situation"], state["relance"])

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"📋 Feedback pédagogique :\n{feedback}\n\n💬 Exemple attendu :\n{exemple}"
        )

        # 🔁 Fin de la situation
        del user_state[user_id]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ Situation terminée. Tape /start pour une nouvelle."
        )

def analyse_reponse(user_response, situation, relance):
    prompt = f"""
Tu es formateur au Parc des Princes. Tu évalues la réponse d’un agent d’accueil à une situation difficile avec un spectateur. Voici le contexte :

Situation initiale : "{situation}"
Relance éventuelle : "{relance}"
Réponse de l'agent : "{user_response}"

1. Donne un feedback pédagogique sur la réponse de l’agent (en 3-5 lignes), en pointant les erreurs éventuelles (empathie, reformulation, ton, mots de confrontation, proposition de solution).
2. Puis propose un exemple de réponse attendue dans ce contexte.

Ta réponse doit contenir deux parties :
📋 Feedback pédagogique :
💬 Exemple attendu :
"""

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # tu peux passer à gpt-4 si souhaité
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )
        texte = completion["choices"][0]["message"]["content"]

        if "💬 Exemple attendu :" in texte:
            feedback, exemple = texte.split("💬 Exemple attendu :", 1)
            feedback = feedback.replace("📋 Feedback pédagogique :", "").strip()
            exemple = exemple.strip()
        else:
            feedback = texte.strip()
            exemple = ""

        return feedback, exemple

    except Exception as e:
        return f"❌ Erreur OpenAI : {e}", ""

# ✅ Main
if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_response))

    # Webhook version (Render)
    import flask
    from flask import Flask, request

    flask_app = Flask(__name__)

    @flask_app.route(f"/{token}", methods=["POST"])
    def webhook():
        update = Update.de_json(request.get_json(force=True), app.bot)
        app.update_queue.put(update)
        return "OK"

    app.run_webhook(
        listen="0.0.0.0",
        port=10000,
        webhook_url=f"https://smiletalk-bot.onrender.com/{token}",
        web_app=flask_app,
    )
