from fastapi import FastAPI
from classes import *

app = FastAPI()

@app.post("/productionplan")
def productionplan(payload: Payload):
    problem_instance = UCproblem(payload)
    if problem_instance.compute_UC():
        return problem_instance.get_solution()
    else :
        return []