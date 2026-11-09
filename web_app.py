"""Interface web mobile de Smile Talk.

Réutilise le moteur pédagogique existant de bot.py sans démarrer Telegram.
Pas de compte individuel ni de base de données : sessions temporaires en mémoire.
"""
from __future__ import annotations

import hmac
import os
import secrets
import threading
import time
from datetime import timedelta

import pandas as pd
from flask import Flask, jsonify, render_template, request, session

from bot import df, evaluer_reponse

ACCESS_CODE = os.environ.get("SMILETALK_ACCESS_CODE", "")
SESSION_SECRET = os.environ.get("SMILETALK_SESSION_SECRET", "")
if not ACCESS_CODE or not SESSION_SECRET:
    raise RuntimeError(
        "Configurer SMILETALK_ACCESS_CODE et SMILETALK_SESSION_SECRET sur le service web Render."
    )

app = Flask(__name__)
app.secret_key = SESSION_SECRET
app.config.update(
    MAX_CONTENT_LENGTH=20 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7),
)

STAGE_FIRST = "first"
STAGE_SECOND = "second"
STAGE_PROCESSING = "processing"
STAGE_DONE = "done"

SESSION_TTL = 2 * 3600
MAX_EVALUATIONS_PER_HOUR = 30
MAX_ANSWER_LENGTH = 1800
_store = {}
_lock = threading.RLock()


def _cleanup():
    now = time.monotonic()
    for key in list(_store):
        if now - _store[key]["updated"] > SESSION_TTL:
            del _store[key]


def _authorized():
    return bool(session.get("authorized") and session.get("sid"))


def _error(message, code=400):
    return jsonify({"error": message}), code


def _state_payload(item):
    if not item:
        return {"stage": "welcome"}
    state = {
        "stage": item["stage"],
        "situation": item["situation"],
        "relance": item["relance"] if item["stage"] != STAGE_FIRST else "",
    }
    if item["stage"] in (STAGE_SECOND, STAGE_PROCESSING, STAGE_DONE):
        state["first_answer"] = item.get("first_answer", "")
    if item["stage"] == STAGE_DONE:
        state["second_answer"] = item.get("second_answer", "")
        state["result"] = item.get("result", {})
    return state


@app.after_request
def security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; base-uri 'none'; "
        "object-src 'none'; frame-ancestors 'none'; form-action 'self'"
    )
    return response


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/state")
def state():
    if not _authorized():
        return jsonify({"authorized": False})
    with _lock:
        _cleanup()
        item = _store.get(session["sid"])
        if item:
            item["updated"] = time.monotonic()
        return jsonify({"authorized": True, **_state_payload(item)})


@app.post("/api/login")
def login():
    if not request.is_json:
        return _error("Requête invalide.")
    data = request.get_json(silent=True) or {}
    candidate = data.get("code", "")
    if not isinstance(candidate, str) or len(candidate) > 150:
        return _error("Code invalide.")
    if not hmac.compare_digest(candidate, ACCESS_CODE):
        return _error("Ce code d'accès n'est pas reconnu.", 403)
    session.clear()
    session["authorized"] = True
    session["sid"] = secrets.token_urlsafe(24)
    session.permanent = True
    return jsonify({"authorized": True, "stage": "welcome"})


@app.post("/api/start")
def start():
    if not _authorized():
        return _error("Code d'accès nécessaire.", 401)
    row = df.sample(n=1).iloc[0]
    relance = row.get("relance", "")
    if pd.isna(relance):
        relance = ""
    item = {
        "stage": STAGE_FIRST,
        "situation": str(row["situation"]),
        "relance": str(relance),
        "first_answer": "",
        "second_answer": "",
        "result": None,
        "evaluations": [],
        "updated": time.monotonic(),
    }
    with _lock:
        _cleanup()
        previous = _store.get(session["sid"])
        if previous:
            item["evaluations"] = previous["evaluations"]
        _store[session["sid"]] = item
    return jsonify(_state_payload(item))


@app.post("/api/answer")
def answer():
    if not _authorized():
        return _error("Code d'accès nécessaire.", 401)
    if not request.is_json:
        return _error("Requête invalide.")
    data = request.get_json(silent=True) or {}
    value = data.get("answer", "")
    if not isinstance(value, str):
        return _error("La réponse doit être du texte.")
    value = value.strip()
    if not value or len(value) > MAX_ANSWER_LENGTH:
        return _error("Écris une réponse de 1 à 1 800 caractères.")

    sid = session["sid"]
    with _lock:
        _cleanup()
        item = _store.get(sid)
        if not item:
            return _error("Cette session a expiré. Lance une nouvelle situation.", 409)
        item["updated"] = time.monotonic()
        if item["stage"] == STAGE_FIRST:
            item["first_answer"] = value
            item["stage"] = STAGE_SECOND
            return jsonify(_state_payload(item))
        if item["stage"] != STAGE_SECOND:
            return _error("Réponse déjà enregistrée ou analyse en cours.", 409)

        now = time.monotonic()
        item["evaluations"] = [t for t in item["evaluations"] if now - t < 3600]
        if len(item["evaluations"]) >= MAX_EVALUATIONS_PER_HOUR:
            return _error("Limite horaire atteinte. Reviens un peu plus tard.", 429)
        item["stage"] = STAGE_PROCESSING
        item["second_answer"] = value
        first = item["first_answer"]
        situation = item["situation"]
        relance = item["relance"]

    try:
        feedback, exemple, score = evaluer_reponse(first, value, situation, relance)
        if feedback.startswith("❌") or not score or not exemple:
            app.logger.error("Évaluation Smile Talk indisponible : %s", feedback[:180])
            raise RuntimeError("Évaluation indisponible")
    except Exception:
        app.logger.exception("Échec de l'évaluation pédagogique")
        with _lock:
            if _store.get(sid) is item:
                item["stage"] = STAGE_SECOND
                item["updated"] = time.monotonic()
        return _error("L'analyse est momentanément indisponible. Réessaie ta deuxième réponse.", 502)

    with _lock:
        if _store.get(sid) is not item:
            return _error("Une nouvelle situation a été lancée entre-temps.", 409)
        item["result"] = {"feedback": feedback, "example": exemple, "score": score}
        item["evaluations"].append(time.monotonic())
        item["stage"] = STAGE_DONE
        item["updated"] = time.monotonic()
        return jsonify(_state_payload(item))


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8080)
