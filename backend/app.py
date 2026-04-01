from fastapi import FastAPI
from pydantic import BaseModel
from analyst import cricket_analyst

app = FastAPI()


class Query(BaseModel):
    question: str


@app.get("/")
def home():
    return {"message": "CricketMind AI is running 🚀"}


@app.post("/analyze")
def analyze(query: Query):
    answer = cricket_analyst(query.question)
    return {"answer": answer}