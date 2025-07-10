from fastapi import FastAPI
from pydantic import BaseModel
from smiletalk_engine import analyser_reponse_chatgpt
import pandas as pd

# Chargement des situations
df = pd.read_csv("SITUATIONS.csv", sep=";")

app = FastAPI()

class AnalyseRequest(BaseModel):
    user_response: str
    index: int
    texte_de_reference: str = ""

@app.post("/analyse")
def analyse(request: AnalyseRequest):
    try:
        row = df.iloc[request.index]
        feedback, exemple, info_op = analyser_reponse_chatgpt(
            request.user_response, row, request.texte_de_reference
        )
        return {
            "feedback": feedback,
            "exemple": exemple,
            "info_op": info_op
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def root():
    return {"message": "SmileTalk Bot API is running."}
