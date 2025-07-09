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
    import unicodedata
    from sklearn.feature_extraction.text import CountVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    def nettoyer(texte):
        return texte.lower().replace("’", "'").strip()

    def normaliser(texte):
        return unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode("utf-8").strip().lower()

    def contient_mots(texte, mots):
        return any(m in texte for m in mots)

    def similarite_reformulation(texte1, texte2):
        vect = CountVectorizer().fit_transform([texte1, texte2])
        return cosine_similarity(vect[0], vect[1])[0][0]

    user_response = nettoyer(user_response)
    feedback = []

    solution_text = normaliser(str(row['solution']))
    solutionnable = "oui" in solution_text
    info_op = row['informations opérationnelles']
    bonne_reponse = nettoyer(row['bonne-reponse'])

    # ✅ Choix du texte de référence (relance ou situation)
    if row.get("relance_utilisee", False) and isinstance(row.get("relance"), str) and row["relance"].strip():
        texte_ref = nettoyer(row["relance"])
    else:
        texte_ref = nettoyer(row["situation"])

    marqueurs_empathie = ["désolé", "navré", "je comprends", "vraiment désolé", "vraiment navré", "bien sûr", "mince", "c'est embetant"]
    mots_conflit = ["mais", "en revanche", "par contre", "néanmoins", "toutefois"]
    formes_imperatives = ["il faut", "vous n'avez qu'à", "il suffit de"]
    formulations_douces = ["je vous invite", "je vous conseille", "peut-être pouvez-vous", "je peux vous proposer"]
    formules_finales = ["ok pour vous", "c'est bon pour vous", "c'est bon", "ça vous va"]

    # ✅ Empathie
    if not contient_mots(user_response, marqueurs_empathie):
        feedback.append("🙁 Il manque une expression d’empathie explicite (‘désolé’, ‘je comprends’…).")

    # ✅ Reformulation (via similarité souple)
    similarite = similarite_reformulation(user_response, texte_ref)
    if similarite < 0.2:
        feedback.append("🔁 La situation n’est pas reformulée : essaye de montrer que tu as compris ce que vit le spectateur.")

    # ✅ Mots de confrontation
    if contient_mots(user_response, mots_conflit):
        feedback.append("⚠️ Tu utilises des mots de confrontation (‘mais’, ‘par contre’…). Essaie plutôt ‘après’, ‘justement’…")

    # ✅ Forme impérative
    if contient_mots(user_response, formes_imperatives):
        feedback.append("📏 Attention à ne pas imposer la solution (‘il faut’, ‘vous n’avez qu’à’…). Propose-la avec tact.")

    # ✅ Présence d’une solution formulée avec tact
    if solutionnable:
        if not contient_mots(user_response, formulations_douces + formules_finales):
            feedback.append("💡 La solution devrait être proposée de façon douce et terminer par une question (‘OK pour vous ?’).")
    else:
        if not contient_mots(user_response, ["désolé", "malheureusement", "je n’ai pas", "je suis embêté", "c’est compliqué"]):
            feedback.append("🧱 Ce litige n’a pas de solution : il faut le dire honnêtement, avec tact.")

    return feedback, row["bonne-reponse"], info_op

