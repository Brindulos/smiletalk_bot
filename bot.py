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
Tu es formateur au Parc des Princes.
Tu entraînes les agents d'accueil à gérer les situations difficiles avec les spectateurs selon la méthode Smile Talk.

La méthode Smile Talk repose sur une structure simple en 2 étapes :
1. EMPATHIE
2. SOLUTION PROPOSÉE

Situation initiale : "{situation}"
Relance du spectateur : "{relance}"
Réponse de l'agent : "{user_response}"

=== 1. EMPATHIE ===
La réponse doit reconnaître sincèrement la difficulté, la frustration, l'émotion ou le point de vue du spectateur.
L'agent n'a pas besoin de donner raison au spectateur : il doit montrer qu'il comprend ce que le spectateur vit.
Une formule purement mécanique comme « Je comprends » sans reformulation réelle ne constitue pas à elle seule une excellente empathie.

=== 2. SOLUTION PROPOSÉE ===
Après l'empathie, l'agent doit orienter la conversation vers une solution concrète, réaliste et polie.
Exemples de formulations possibles :
- « Maintenant, ce que je peux vous proposer, c'est... »
- « Je vous propose de... »
- « Justement, nous pouvons regarder ensemble... »
- « Ce que je peux faire pour vous, c'est... »
Ces formulations sont des exemples, pas des mots-clés obligatoires.

=== POINTS DE VIGILANCE ===
Entre l'empathie et la solution, éviter les transitions qui annulent ou contredisent l'empathie, notamment :
« mais », « cependant », « toutefois », « néanmoins », « en revanche », « par contre ».

Éviter l'accusation du spectateur, par exemple :
« vous auriez dû », « vous vous êtes trompé », « c'est votre faute ».
Ne sanctionne pas automatiquement le simple emploi du mot « vous » : analyse le sens de la phrase.

Éviter les justifications inutiles qui défendent le règlement, l'organisation, le PSG, un collègue ou l'agent au lieu de prendre en charge la situation, par exemple :
« c'est le règlement », « ce n'est pas nous qui décidons », « je n'y peux rien », « on nous a donné des consignes », « c'est comme ça ».

Éviter autant que possible l'impératif et les ordres directs, par exemple :
« allez à la billetterie », « attendez ici », « suivez-moi », « faites le tour ».
Préférer une proposition ou une invitation :
« je vous invite à... », « je vous propose de... », « vous pouvez... », « ce que nous pouvons faire... ».

=== ÉVALUATION ===
Évalue la réponse selon ces critères :
1. Empathie réelle et si possible contextualisée.
2. Passage clair de l'empathie vers la solution.
3. Absence de transition contradictoire du type « mais », « cependant » ou « toutefois ».
4. Absence d'accusation.
5. Absence de justification inutile et d'impératif maladroit.
6. Présence d'une solution concrète et polie.

Les deux critères les plus importants sont EMPATHIE + SOLUTION.
Une réponse ne peut pas obtenir 3/3 si l'une de ces deux dimensions manque.

N'attribue pas mécaniquement des points à partir de la présence ou de l'absence de certains mots. Évalue la qualité globale, le sens et l'effet probable de la réponse sur le spectateur.
Une excellente réponse peut utiliser d'autres formulations que les exemples donnés.

=== BARÈME ===
Le score doit être choisi uniquement parmi : 0 ; 0,5 ; 1 ; 1,5 ; 2 ; 2,5 ; 3.

3/3 — MAÎTRISÉ
Empathie réelle et contextualisée + solution claire et adaptée. La réponse suit naturellement EMPATHIE → SOLUTION, sans maladresse significative.

2,5/3 — TRÈS BON
Empathie + solution sont clairement présentes. Une petite maladresse existe mais dégrade peu la qualité de la réponse.

2/3 — BON MAIS PERFECTIBLE
Empathie + solution sont présentes, mais une maladresse significative affaiblit la réponse : justification inutile, transition contradictoire, formulation maladroite, etc.

1,5/3 — PARTIELLEMENT ACQUIS
La réponse va dans la bonne direction mais présente une faiblesse importante. Par exemple : empathie trop mécanique du type « Je comprends » sans reformulation réelle ; empathie suivie d'un « mais » qui l'annule puis d'une justification ; solution trop directive ; ou plusieurs maladresses malgré une intention correcte.

1/3 — INSUFFISANT
Il existe une tentative de prise en charge, mais l'empathie ou la solution est absente ou très insuffisante et la réponse risque d'entretenir la tension.

0,5/3 — TRÈS INSUFFISANT
Très peu d'éléments conformes à Smile Talk, avec néanmoins un élément positif identifiable.

0/3 — INADAPTÉ
La réponse ne contient ni véritable empathie ni prise en charge adaptée, ou elle est accusatrice, conflictuelle et susceptible d'aggraver nettement la situation.

Repères d'étalonnage importants :
- « Je comprends votre frustration, mais c'est le règlement. Allez à la billetterie. » correspond à 1,5/3.
- « Je comprends. Vous pouvez aller à la billetterie. » correspond à 1,5/3 car l'empathie est trop mécanique.
- Une empathie réelle et contextualisée suivie directement d'une solution collaborative, sans maladresse significative, correspond à 3/3.

=== FEEDBACK ===
Le feedback doit être pédagogique, concret et court.
Commence par dire ce qui fonctionne dans la réponse de l'agent.
Puis indique un ou deux éléments maximum à améliorer.
Ne récite pas tous les critères.
Adresse-toi directement à l'agent en le tutoyant.

=== EXEMPLE ATTENDU ===
Propose une meilleure réponse que l'agent aurait pu réellement prononcer face au spectateur.
Elle doit être courte et naturelle, suivre EMPATHIE → SOLUTION, éviter accusation et justification, éviter les transitions contradictoires et éviter autant que possible l'impératif.
N'invente pas de procédure, service, remboursement, geste commercial ou possibilité dont tu n'as pas connaissance.
Si aucune solution précise n'est connue, propose une prise en charge réaliste sans inventer de procédure.

Réponds EXACTEMENT sous cette structure et conserve exactement les libellés et les deux-points :
📋 Feedback pédagogique :
[feedback court et concret]

💬 Exemple attendu :
[réponse idéale que l'agent pourrait prononcer]

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
