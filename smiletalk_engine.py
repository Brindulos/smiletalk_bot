import pandas as pd
import openai

# Chargement des situations
df = pd.read_csv("SITUATIONS.csv", sep=";")

def analyser_reponse_chatgpt(user_response, row, texte_ref):
    public = row['public']
    situation = row['situation']
    relance = row.get("relance", "").strip()
    bonne_reponse = row['bonne-reponse']
    bonne_reponse_relance = row.get("bonne-reponse-relance", "").strip()
    info_op = row.get("informations opérationnelles", "").strip()

    # Détection si on est en réponse à la relance
    en_reponse_a_la_relance = texte_ref.strip() == relance and relance != ""

    # Choix du texte d’exemple attendu
    exemple_attendu = bonne_reponse_relance if en_reponse_a_la_relance and bonne_reponse_relance else bonne_reponse

    prompt = f"""
Tu es formateur Smile Talk pour les équipes d’accueil du Paris Saint-Germain. Tu évalues la qualité d’une réponse donnée par un agent dans une situation difficile avec un spectateur.

Situation initiale : {situation}

Relance du spectateur : {relance if relance else 'Aucune'}

Réponse de l’agent : {user_response}

Ta mission :
- Commence par écrire un feedback pédagogique synthétique sur la réponse (maximum 4 lignes).
- Si l’agent répond à la relance, ton analyse doit se concentrer uniquement sur la relance.
- Commente la présence ou non d’empathie, la reformulation, la qualité de la solution et la manière de la formuler (pas d’impératif).
- Sois formateur, précis, bienveillant mais sans compliment inutile.

Ensuite, donne un exemple de réponse attendue adaptée à ce cas précis (pas une réponse générique). Termine par ce format :

📋 Feedback :
[ton analyse]

💬 Exemple attendu :
[exemple adapté]
    """

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un assistant expert en formation relationnelle en contexte sportif (Parc des Princes)."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )

        texte = completion['choices'][0]['message']['content'].strip()

        # Séparation feedback / exemple
        if "💬 Exemple attendu :" in texte:
            feedback, exemple = texte.split("💬 Exemple attendu :", 1)
            feedback = feedback.replace("📋 Feedback :", "").strip()
            exemple = exemple.strip()
        else:
            feedback = texte
            exemple = exemple_attendu

        return [feedback], exemple, ""  # pas besoin d'info opérationnelle ici
    except Exception as e:
        return [f"Erreur lors de l’analyse avec ChatGPT : {e}"], exemple_attendu, ""
