from fastapi import FastAPI
from pydantic import BaseModel
from analyst import cricket_analyst

app = FastAPI()


class Query(BaseModel):
    player1: str
    player2: str
    language: str = "en"
    format: str = "combined"
    stats_mode: str = "batting"   # "batting" | "bowling"


@app.get("/")
def home():
    return {"message": "CricketMind AI is running 🚀"}


@app.post("/analyze")
def analyze(query: Query):
    answer = cricket_analyst(
        query.player1, query.player2,
        query.language, query.format,
        query.stats_mode,
    )
    return answer