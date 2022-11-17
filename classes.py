from pydantic import BaseModel
from enum import Enum

class PowerplantEnum(Enum):
    gasfired = "gasfired"
    turbojet = "turbojet"
    windturbine = "windturbine"

class FuelEnum(Enum):
    gas = "gas(euro/MWh)"
    kerosine = "kerosine(euro/MWh)"
    co2 = "co2(euro/ton)"
    wind = "wind(%)"

class Powerplant(BaseModel):
    name: str
    type: PowerplantEnum
    efficiency: float
    pmin: float
    pmax: float

class Payload(BaseModel):
    load: float
    fuels: dict[FuelEnum, float]
    powerplants: list[Powerplant]

class UCproblem():

    def __init__(self, payload: Payload) :
        self.load = payload.load
        self.fuels = payload.fuels
        self.powerplants = payload.powerplants