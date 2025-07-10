import os
import pandas as pd
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ✅ Initialisation de l'API OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Chargement du fichier CSV
df = pd.read_csv("SITUATIONS.csv", sep=";")

# ✅ Variable d'état pour l’utilisateur
user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_state[user_id] = {"index": 0}
    
    situation = df.iloc[0]
    await update.message.reply_text(
        f"🎯 Situation {user_state[user_id]['index']}:\n"
        f"{situation['situation']}\n\n"
        f"Relance éventuelle : {situation.get('relance', '')}\n"
        "💬 À vous !"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_state:
        await update.message.reply_text("Envoie /start pour commencer.")
        return

    index = user_state[user_id]["index"]
    row = df.iloc[index]
    user_response = update.message.text

    prompt = f"""
Tu es formateur au Parc des Princes. Tu évalues la réponse d’un agent d’accueil à une situation difficile avec un spectateur. Voici le contexte :

Situation initiale : "{row['situation']}"
Relance éventuelle : "{row.get('relance', '')}"
Réponse de l'agent : "{user_response}"

1. Donne un feedback pédagogique sur la réponse de l’agent (en 3-5 lignes maximum), en pointant les erreurs éventuelles (empathie, reformulation, ton, mots de confrontation, proposition de solution).
2. Puis propose un exemple de réponse attendue dans ce contexte.

Ta réponse doit contenir deux parties :
📋 Feedback pédagogique :
💬 Exemple attendu :
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=500
        )

        texte = response.choices[0].message['content']
        if "💬 Exemple attendu :" in texte:
            feedback, exemple = texte.split("💬 Exemple attendu :", 1)
            feedback = feedback.replace("📋 Feedback pédagogique :", "").strip()
            exemple = exemple.strip()
        else:
            feedback = texte.strip()
            exemple = ""

        await update.message.reply_text(f"📋 Feedback pédagogique :\n{feedback}\n\n💬 Exemple attendu :\n{exemple}")

    except Exception as e:
        await update.message.reply_text(f"❌ Erreur OpenAI : {str(e)}")

# ✅ Lancement du bot
if __name__ == "__main__":
    import asyncio

    TOKEN = os.getenv("TELEGRAM_TOKEN")  # Assure-toi que cette variable est bien définie dans Render
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot démarré...")
    asyncio.run(app.run_polling())
