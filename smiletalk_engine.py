import os
import pandas as pd
from openai import OpenAI

# Initialisation du client OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Chargement du fichier CSV
df = pd.read_csv("SITUATIONS.csv", sep=";")

def analyser_reponse_chatgpt(user_response, row, texte_de_reference):
    """
    Analyse conversationnelle intelligente basée sur OpenAI v1.0+
    """
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
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500,
        )
        texte = completion.choices[0].message.content

        # Découper le texte selon les balises
        if "💬 Exemple attendu :" in texte:
            feedback, exemple = texte.split("💬 Exemple attendu :", 1)
            feedback = feedback.replace("📋 Feedback pédagogique :", "").strip()
            exemple = exemple.strip()
        else:
            feedback = texte.strip()
            exemple = ""

        return [feedback], exemple, ""  # info_op non utilisé ici

    except Exception as e:
        return [f"❌ Erreur API OpenAI : {str(e)}"], "", ""
