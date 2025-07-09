import random
import pandas as pd
import unicodedata
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df = pd.read_csv("SITUATIONS.csv", sep=";")

def nettoyer(texte):
    return texte.lower().replace("’", "'").strip()

def normaliser(texte):
    return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("utf-8").strip().lower()

def contient_mots(texte, mots):
    return any(m in texte for m in mots)

def similarite_reformulation(texte1, texte2):
    vect = CountVectorizer().fit_transform([texte1, texte2])
    return cosine_similarity(vect[0], vect[1])[0][0]

def analyser_reponse(user_response, row):
    user_response = nettoyer(user_response)

    feedback = []
    bonne_reponse = nettoyer(row['bonne-reponse'])

    solution_text = normaliser(str(row['solution']))
    solutionnable = "oui" in solution_text

    info_op = row['informations opérationnelles']

    marqueurs_empathie = ["désolé", "navré", "je comprends", "vraiment désolé", "vraiment navré", "bien sûr", "mince", "c'est embetant"]
    mots_conflit = ["mais", "en revanche", "par contre", "néanmoins", "toutefois"]
    mots_adoucis = ["maintenant", "après", "justement"]
    formes_imperatives = ["il faut", "vous n'avez qu'à", "il suffit de"]
    formulations_douces = ["je vous invite", "je vous conseille", "peut-être pouvez-vous", "je peux vous proposer"]
    formules_finales = ["ok pour vous", "c'est bon pour vous", "c'est bon", "ça vous va"]

    # Vérifie présence empathie
    if not contient_mots(user_response, marqueurs_empathie):
        feedback.append("🙁 Il manque une expression d’empathie explicite (‘désolé’, ‘je comprends’…).")
    
    # Vérifie reformulation plus souple
    similarite = similarite_reformulation(user_response, nettoyer(row['situation']))
    if similarite < 0.2:
        feedback.append("🔁 La situation n’est pas reformulée : essaye de montrer que tu as compris ce que vit le spectateur.")

    # Vérifie mots de confrontation
    if contient_mots(user_response, mots_conflit):
        feedback.append("⚠️ Tu utilises des mots de confrontation (‘mais’, ‘par contre’…). Essaie plutôt ‘après’, ‘justement’…")

    # Vérifie si la solution est adoucie
    if contient_mots(user_response, formes_imperatives):
        feedback.append("📏 Attention à ne pas imposer la solution (‘il faut’, ‘vous n’avez qu’à’…). Propose-la avec tact.")
    
    if solutionnable:
        if not contient_mots(user_response, formulations_douces + formules_finales):
            feedback.append("💡 La solution devrait être proposée de façon douce et terminer par une question (‘OK pour vous ?’).")
    else:
        if not contient_mots(user_response, ["désolé", "malheureusement", "je n’ai pas", "je suis embêté", "c’est compliqué"]):
            feedback.append("🧱 Ce litige n’a pas de solution : il faut le dire honnêtement, avec tact.")

    return feedback, row["feedback"], info_op
