"""Tests hors ligne : aucun appel API OpenAI et aucune connexion Telegram."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SMILETALK_ACCESS_CODE", "code-de-test-reserve")
os.environ.setdefault("SMILETALK_SESSION_SECRET", "cle-de-test-qui-ne-sera-pas-utilisee-en-production")

import web_app


class WebAppTests(unittest.TestCase):
    def setUp(self):
        self.client = web_app.app.test_client()
        with web_app._lock:
            web_app._store.clear()
            web_app._login_failures.clear()
            web_app._global_evaluations.clear()

    def post(self, path, data):
        return self.client.post(path, json=data, base_url="https://localhost")

    def get(self, path):
        return self.client.get(path, base_url="https://localhost")

    def login(self):
        result = self.post("/api/login", {"code": "code-de-test-reserve"})
        self.assertEqual(result.status_code, 200)
        return result

    def test_unauthorized_access(self):
        self.assertFalse(self.get("/api/state").json["authorized"])
        self.assertEqual(self.post("/api/start", {}).status_code, 401)
        self.assertEqual(self.post("/api/answer", {"answer": "Bonjour"}).status_code, 401)

    def test_incorrect_code(self):
        result = self.post("/api/login", {"code": "errone"})
        self.assertEqual(result.status_code, 403)

    def test_login_throttling(self):
        for _ in range(web_app.MAX_LOGIN_FAILURES):
            self.assertEqual(self.post("/api/login", {"code": "incorrect"}).status_code, 403)
        self.assertEqual(self.post("/api/login", {"code": "incorrect"}).status_code, 429)

    def test_complete_exercise(self):
        self.login()
        start = self.post("/api/start", {})
        self.assertEqual(start.status_code, 200)
        self.assertEqual(start.json["stage"], "first")
        self.assertTrue(start.json["situation"])
        self.assertEqual(start.json["relance"], "")
        answer1 = self.post("/api/answer", {"answer": "Je comprends la difficulté. Je vais vérifier."})
        self.assertEqual(answer1.status_code, 200)
        self.assertEqual(answer1.json["stage"], "second")
        self.assertIn("relance", answer1.json)
        with patch.object(web_app, "evaluer_reponse", return_value=("Feedback test", "Modèle test", "2,5/3")) as mock:
            answer2 = self.post("/api/answer", {"answer": "Je vais regarder votre billet."})
        self.assertEqual(answer2.status_code, 200)
        self.assertEqual(answer2.json["stage"], "done")
        self.assertEqual(answer2.json["result"]["score"], "2,5/3")
        self.assertEqual(mock.call_count, 1)
        self.assertEqual(self.get("/api/state").json["stage"], "done")
        self.assertEqual(self.post("/api/answer", {"answer": "Encore"}).status_code, 409)
        self.assertEqual(self.post("/api/start", {}).json["stage"], "first")

    def test_api_failure_does_not_count_and_allows_retry(self):
        self.login()
        self.post("/api/start", {})
        self.post("/api/answer", {"answer": "Je vais voir ce que je peux faire."})
        with patch.object(web_app, "evaluer_reponse", return_value=("❌ Erreur API", "", "")):
            resp = self.post("/api/answer", {"answer": "Je vais vérifier votre billet."})
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(self.get("/api/state").json["stage"], "second")
        self.assertEqual(web_app._global_evaluations, [])

    def test_length_validation(self):
        self.login()
        self.post("/api/start", {})
        self.assertEqual(self.post("/api/answer", {"answer": ""}).status_code, 400)
        self.assertEqual(self.post("/api/answer", {"answer": "a" * 1801}).status_code, 400)

    def test_home_and_health(self):
        self.assertEqual(self.get("/").status_code, 200)
        self.assertIn("SMILE", self.get("/").get_data(as_text=True))
        self.assertEqual(self.get("/health").json["status"], "ok")


if __name__ == "__main__":
    unittest.main()
