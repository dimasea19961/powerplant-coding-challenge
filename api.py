from fastapi import FastAPI
from classes import *

app = FastAPI()

@app.post("/productionplan")
def productionplan(payload: Payload):
    problem = UCproblem(payload)
    return {"Given_payload": payload}