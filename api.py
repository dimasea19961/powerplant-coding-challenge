from fastapi import FastAPI

app = FastAPI()

@app.get("/productionplan")
def productionplan():
    return {"Message": "Hello World!"}