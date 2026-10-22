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
Dans la phase d'empathie, privilégie autant que possible une reformulation de la situation vécue plutôt qu'une formulation qui pointe directement le spectateur avec « vous ».
Par exemple, préfère « Je comprends, ça fait beaucoup d'allers-retours » à « Je comprends, ça fait beaucoup d'allers-retours pour vous ».
Le mot « vous » n'est pas interdit : il reste parfaitement naturel lorsqu'il sert ensuite la prise en charge, par exemple « je vais vous orienter » ou « je peux vous proposer ».

=== 2. SOLUTION PROPOSÉE ===
Après l'empathie, l'agent doit orienter la conversation vers une solution concrète, réaliste et polie.
La prise en charge de la solution appartient à l'agent : ce n'est pas au spectateur de chercher lui-même une solution.
Privilégie des formulations où l'agent assume clairement l'action, par exemple :
- « Maintenant, je vais voir ce que je peux faire pour vous trouver une solution. »
- « Je vais vérifier ce qu'il est possible de faire. »
- « Ce que je peux vous proposer, c'est... »
- « Je vais vérifier votre billet pour voir quelle solution je peux vous proposer. »
Ces formulations sont des exemples, pas des mots-clés obligatoires.
Une simple déclaration d'intention comme « on fait le maximum » n'est pas à elle seule une solution concrète proposée.

=== POINTS DE VIGILANCE ===
Entre l'empathie et la solution, éviter les transitions qui annulent ou contredisent l'empathie, notamment :
« mais », « cependant », « toutefois », « néanmoins », « en revanche », « par contre ».

RÈGLE OBLIGATOIRE SUR « MAIS » :
Si la réponse de l'agent utilise « mais » pour passer de l'empathie à une justification, une explication, une objection ou une solution, le feedback doit obligatoirement le signaler explicitement.
Ne te contente pas d'en tenir compte dans la note : explique à l'agent que ce « mais » risque d'annuler l'effet de l'empathie qui précède.
Dans l'exemple attendu, reformule alors la réponse sans « mais ».
Cette règle n'impose pas une pénalité chiffrée automatique : la note reste fondée sur la qualité globale de la réponse.

Éviter l'accusation du spectateur, par exemple :
« vous auriez dû », « vous vous êtes trompé », « c'est votre faute ».
Ne sanctionne pas automatiquement le simple emploi du mot « vous » : analyse le sens de la phrase.

Éviter les justifications inutiles qui défendent le règlement, l'organisation, le PSG, un collègue ou l'agent au lieu de prendre en charge la situation, par exemple :
« c'est le règlement », « ce n'est pas nous qui décidons », « je n'y peux rien », « on nous a donné des consignes », « c'est comme ça », « je vous prie de croire qu'on fait le maximum ».

Éviter autant que possible toutes les formes impératives, y compris les impératifs inclusifs comme « regardons », « voyons » ou « essayons ».
Exemples à éviter : « allez à la billetterie », « attendez ici », « suivez-moi », « faites le tour », « regardons ensemble », « voyons ce qu'on peut faire ».
Même lorsqu'un impératif inclusif est poli et collaboratif, il ne correspond pas au modèle Smile Talk recherché.
Préférer une formulation où l'agent prend en charge l'action : « je vais vérifier... », « je vais voir... », « je peux vous proposer... ».

=== ÉVALUATION ===
Évalue la réponse selon ces critères :
1. Empathie réelle et si possible contextualisée.
2. Passage clair de l'empathie vers la solution.
3. Absence de transition contradictoire du type « mais », « cependant » ou « toutefois ».
4. Absence d'accusation.
5. Absence de justification inutile et d'impératif, y compris inclusif.
6. Présence d'une solution concrète et polie prise en charge par l'agent.

Les deux critères les plus importants sont EMPATHIE + SOLUTION.
Une réponse ne peut pas obtenir 3/3 si l'une de ces deux dimensions manque.
La simple présence formelle des deux étapes ne suffit pas à dépasser 1,5/3 : pour obtenir 2/3 ou davantage, l'empathie doit être suffisamment explicite, développée ou contextualisée pour montrer au spectateur que sa difficulté a réellement été comprise. Une réponse très courte avec seulement « je comprends » ou une formule équivalente, même suivie d'une intention de chercher une solution, reste au maximum à 1,5/3 si l'empathie n'est pas davantage exprimée.
Toutefois, ne juge pas l'empathie uniquement sur les premiers mots : une réponse qui commence par un « je comprends » minimal peut montrer ensuite, par une reformulation précise de la situation ou par la manière dont la solution est formulée, que l'agent a réellement compris le problème. Dans ce cas, elle peut dépasser 1,5/3.

N'attribue pas mécaniquement des points à partir de la présence ou de l'absence de certains mots. Évalue la qualité globale, le sens et l'effet probable de la réponse sur le spectateur.
Une excellente réponse peut utiliser d'autres formulations que les exemples donnés.

=== BARÈME ===
Le score doit être choisi uniquement parmi : 0 ; 0,5 ; 1 ; 1,5 ; 2 ; 2,5 ; 3.

3/3 — MAÎTRISÉ
Empathie réelle et contextualisée + solution claire et adaptée, prise en charge par l'agent. La réponse suit naturellement EMPATHIE → SOLUTION, sans maladresse significative.

2,5/3 — TRÈS BON
Empathie + solution sont clairement présentes et la réponse fonctionne très bien. La compréhension de la situation est perceptible dans l'ensemble de la réponse, mais l'expression explicite de l'empathie peut rester un peu trop pauvre ou une petite maladresse subsiste. Il manque peu de chose pour atteindre 3/3.

2/3 — BON MAIS PERFECTIBLE
Empathie + solution sont présentes et réellement exprimées, mais une maladresse significative affaiblit la réponse : justification inutile, transition contradictoire, formulation maladroite, solution encore trop vague, etc. Une empathie réduite à une formule minimale comme « je comprends » ne suffit pas pour obtenir 2/3 si rien d'autre dans la réponse ne montre une compréhension réelle de la situation.

1,5/3 — PARTIELLEMENT ACQUIS
Les deux briques Smile Talk — EMPATHIE et SOLUTION — sont au moins identifiables, mais l'une d'elles reste minimale ou une faiblesse importante dégrade la réponse. Par exemple : empathie trop mécanique du type « Je comprends » sans reformulation réelle ni autre indice de compréhension ; réponse très courte avec une empathie minimale suivie d'une intention de chercher une solution ; empathie suivie d'un « mais » qui l'annule puis d'une justification ; solution trop directive ; ou plusieurs maladresses malgré une intention correcte.

1/3 — INSUFFISANT
Une seule des deux briques Smile Talk est réellement présente. Il peut notamment y avoir une prise en charge correcte et polie de la situation, mais aucune empathie ni reconnaissance de ce que le spectateur vient de vivre. Inversement, l'agent peut exprimer de l'empathie sans proposer de prise en charge. La réponse contient donc un élément positif réel, mais la structure EMPATHIE → SOLUTION n'est pas constituée.

0,5/3 — TRÈS INSUFFISANT
Très peu d'éléments conformes à Smile Talk, avec néanmoins un élément positif identifiable.

0/3 — INADAPTÉ
La réponse ne contient ni véritable empathie ni prise en charge adaptée, ou elle est accusatrice, conflictuelle et susceptible d'aggraver nettement la situation.

Repères d'étalonnage importants :
- « Je comprends votre frustration, mais c'est le règlement. Allez à la billetterie. » correspond à 1,5/3.
- « Je comprends. Vous pouvez aller à la billetterie. » correspond à 1,5/3 car l'empathie est trop mécanique.
- « Oui effectivement je comprends. Je vais voir ce que je peux faire. » correspond à 1,5/3 : les deux étapes sont présentes, mais l'empathie est vraiment minimale, non contextualisée, et l'ensemble est trop succinct pour obtenir 2/3.
- « OK je peux voir votre billet ? » correspond à 1/3 : la demande est polie et commence une prise en charge concrète, mais l'empathie est totalement absente. Une prise en charge correcte sans aucune reconnaissance de ce que le spectateur vient de vivre ne suffit pas pour atteindre 1,5/3.
- « Oui effectivement je comprends. C'est rageant. Maintenant je vous prie de croire qu'on fait le maximum pour vous, pour vous trouver une solution. » correspond à 2/3 : l'empathie est réelle, mais « on fait le maximum » est une justification et une déclaration d'intention plutôt qu'une solution concrète.
- « Ok je comprends. Je peux voir votre billet, je vais vérifier et essayer de vous orienter au mieux pour éviter les kilomètres. » correspond à 2,5/3 : l'empathie explicite commence de façon mécanique, mais la fin de la réponse montre une compréhension concrète du problème avec « éviter les kilomètres » et l'agent prend clairement en charge la solution. Une empathie plus explicitement contextualisée ferait passer la réponse à 3/3.
- « Bien sûr monsieur je comprends, on vous fait faire des kilomètres... Je regarde ça tout de suite et je vérifie pour vous donner une information la plus sûre possible. Puis-je voir votre billet ? » correspond à 3/3 : l'empathie est contextualisée, l'agent prend immédiatement en charge la situation avec une action concrète, sans accusation, justification ni impératif, et demande le billet de façon polie.
- Une empathie réelle et contextualisée suivie directement d'une solution prise en charge par l'agent, sans maladresse significative, correspond à 3/3.

=== FEEDBACK ===
Le feedback doit être pédagogique, concret et court.
Commence par dire ce qui fonctionne dans la réponse de l'agent.
Puis indique un ou deux éléments maximum à améliorer.
Si un « mais » relie l'empathie à une justification, une explication, une objection ou une solution, le feedback doit impérativement faire partie des éléments à améliorer et signaler explicitement ce « mais ».
Ne récite pas tous les critères.
Adresse-toi directement à l'agent en le tutoyant.

=== EXEMPLE ATTENDU ===
Propose une meilleure réponse que l'agent aurait pu réellement prononcer face au spectateur.
Elle doit être courte et naturelle, suivre EMPATHIE → SOLUTION, éviter accusation et justification, éviter les transitions contradictoires et éviter les formes impératives, y compris inclusives comme « regardons », « voyons » ou « essayons ».
Dans l'empathie, privilégie la description de la situation plutôt qu'une formulation qui pointe directement le spectateur avec « vous ». Par exemple : « Je comprends, ça fait beaucoup d'allers-retours » plutôt que « ça fait beaucoup d'allers-retours pour vous ».
La solution doit être prise en charge par l'agent : ne fais pas porter au spectateur la recherche de solution.
Préfère « je vais vérifier », « je vais voir ce que je peux faire » ou « je peux vous proposer » à « regardons ensemble ».
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
