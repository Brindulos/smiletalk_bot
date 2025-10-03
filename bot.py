import os
import random
import pandas as pd
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# ✅ Clés API depuis variables Render
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ✅ Lecture des situations
df = pd.read_csv("SITUATIONS.csv", sep=";")

# ✅ Mémoire temporaire
user_sessions = {}

# ✅ Analyse par GPT-4
def evaluer_reponse(user_response, situation, relance=""):
    prompt = f"""
Tu es formateur au Parc des Princes. Tu évalues la réponse d’un agent d’accueil à une situation difficile avec un spectateur.

Situation initiale : "{situation}"
Relance éventuelle : "{relance}"
Réponse de l'agent : "{user_response}"

1. Donne un feedback pédagogique (3-5 lignes max) sur la réponse.
2. Propose un exemple de réponse attendue.
3. Donne une note globale entre 0 et 3 étoiles selon :
- Empathie / Reformulation de la frustration
- Absence de confrontation (pas de “mais”, “cependant”, “en revanche”, “par contre”, “toutefois”, “néanmoins”, pas de ton sec)
- Absence d'accusation du spectateur (pas de “vous auriez dû”, "vous êtes")
- Absence de justification
- Absence de l'utilisation de l'impératif
- Proposition de solution claire et polie

Réponds sous ce format :
📋 Feedback pédagogique :
[...]
💬 Exemple attendu 
(doit respecter ces contraintes :
 - Empathie / Reformulation de la frustration
- Absence de confrontation (pas de “mais”, “cependant”, “en revanche”, “par contre”, “toutefois”, “néanmoins”, pas de ton sec)
- Absence d'accusation du spectateur (pas de “vous auriez dû”)
- Absence de justification
- Absence de l'utilisation de l'impératif
- Proposition de solution claire et polie):
[...]
⭐ Score : X/3
    """

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=600
        )
        response = completion.choices[0].message["content"]

        feedback = response.split("💬 Exemple attendu :")[0].replace("📋 Feedback pédagogique :", "").strip()
        exemple = response.split("💬 Exemple attendu :")[1].split("⭐")[0].strip()
        score_line = response.split("⭐ Score :")[1].strip()
        return feedback, exemple, score_line
    except Exception as e:
        return f"❌ Erreur API OpenAI : {str(e)}", "", ""

# ✅ /start = envoi situation aléatoire
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    situation_row = df.sample().iloc[0]
    user_sessions[user_id] = {
        "situation": situation_row["situation"],
        "relance": situation_row.get("relance", ""),
        "etat": "attente_reponse1"
    }
    await update.message.reply_text(f"🎯 Situation :\n{situation_row['situation']}\n\n💬 Que répondez-vous ?")

# ✅ Messages utilisateurs
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message.text.strip()

    if user_id not in user_sessions:
        await update.message.reply_text("Tape /start pour lancer une situation.")
        return

    session = user_sessions[user_id]
    etat = session["etat"]

    if etat == "attente_reponse1":
        session["reponse1"] = message
        session["etat"] = "attente_reponse2"
        await update.message.reply_text(f"🙋‍♂️ Le spectateur insiste :\n{session['relance']}\n\n💬 Et vous, vous dites quoi maintenant ?")

    elif etat == "attente_reponse2":
        session["reponse2"] = message
        feedback, exemple, score = evaluer_reponse(session["reponse2"], session["situation"], session["relance"])
        await update.message.reply_text(
            f"📋 Voici ton feedback pédagogique :\n{feedback}\n\n💬 Exemple attendu :\n{exemple}\n\n⭐ Score : {score}"
        )
        del user_sessions[user_id]

# ✅ Lancement Webhook (Render)
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("✅ Bot Smile Talk en ligne")
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}"
    )
