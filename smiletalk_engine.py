
import pandas as pd

df = pd.read_csv("SITUATIONS.csv", sep=";")

def analyser_reponse_gpt(user_response, row, texte_de_reference):
    feedback = []

    situation = row.get("situation", "").strip()
    relance = row.get("relance", "").strip()
    solution = str(row.get("solution", "")).strip().lower()
    solutionnable = "oui" in solution
    bonne_reponse = row.get("bonne-reponse", "").strip()
    bonne_reponse_relance = row.get("bonne-reponse-relance", "").strip()
    info_op = row.get("informations opérationnelles", "").strip()

    # 🧠 Analyse conversationnelle par ChatGPT
    evaluation = []

    # 1. Empathie
    if any(x in user_response.lower() for x in ["désolé", "je comprends", "c’est dur", "j’imagine", "pas de chance", "courage"]):
        evaluation.append("✅ Une forme d'empathie est bien présente.")
    else:
        feedback.append("🙁 Il manque une marque d’empathie explicite ou implicite.")

    # 2. Reformulation implicite
    if any(mot in user_response.lower() for mot in situation.lower().split()[:10]) or any(x in user_response.lower() for x in ["vous venez de loin", "avec vos enfants", "le billet ne passe pas", "place occupée", "c’est cher"]):
        evaluation.append("✅ La reformulation est présente, même de façon implicite.")
    else:
        feedback.append("🔁 Il manque une reformulation du problème : essaye de montrer que tu as compris ce que vit le spectateur.")

    # 3. Tonalité et tact
    if any(x in user_response.lower() for x in ["je vous invite", "je peux", "je vous conseille", "peut-être", "ok pour vous", "ça vous va", "on peut essayer"]):
        evaluation.append("✅ La solution est proposée avec tact.")
    else:
        if solutionnable:
            feedback.append("💡 La solution devrait être formulée avec douceur et finir sur une ouverture (‘OK pour vous ?’).")
        else:
            if not any(x in user_response.lower() for x in ["désolé", "malheureusement", "je ne peux pas", "je suis embêté", "c’est compliqué"]):
                feedback.append("🧱 Ce litige n’a pas de solution : il faut le dire avec tact et franchise.")

    # 4. Éviter les formulations dures
    if any(x in user_response.lower() for x in ["il faut", "vous devez", "vous n’avez qu’à"]):
        feedback.append("📏 Attention à ne pas imposer la solution (‘il faut’, ‘vous devez’…). Propose-la avec tact.")

    return feedback, bonne_reponse_relance if row.get("relance_utilisee", False) else bonne_reponse, info_op
