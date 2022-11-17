from fastapi import FastAPI
from classes import *

app = FastAPI()

@app.post("/productionplan")
def productionplan(payload: Payload):
    problem = UCproblem(payload)
    if problem.compute_UC():
        return problem.get_solution()
    else :
        return []