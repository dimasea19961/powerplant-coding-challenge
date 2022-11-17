# powerplant-coding-challenge

## Description

This is the implementation of the Powerplant Coding Challenge by Negru Dumitru. The original Github repository can be found [here](https://github.com/gem-spaas/powerplant-coding-challenge).

## Launch

The requirements to run the project can be found in "requirements.txt". After installing `FastAPI` and `Pydantic`, one can launch the API by opening a terminal in the directory containing the "api.py" file and running the folowing command:

`uvicorn api:app --port 8888`

## The API

After launching the server, the automatically generated documentation of the API can be found at URL `http://127.0.0.1:8888/docs`. It also allows one to manually test API endpoints.

## Project Structure

The file "api.py" contains the implementation of the specified endpoint : `/productionplan`.

The file "classes.py" contains the implementation of the main algorithm, which is encapsulated into the `UCproblem` class.

The file "tests.py" contains the unit tests that were implemented for the `UCproblem` class.

