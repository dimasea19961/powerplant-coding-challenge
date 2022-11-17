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

    def __init__(self, payload: Payload):
        self.load = payload.load
        self.fuels = payload.fuels
        self.powerplants = payload.powerplants
        self.merit_order_val = None
    
    def compute_cost(self, powerplant: Powerplant, fuels: dict[FuelEnum, float]):
        if powerplant.type == PowerplantEnum.windturbine:
            return 0
        elif powerplant.type == PowerplantEnum.gasfired:
            return fuels[FuelEnum.gas] / powerplant.efficiency
        elif powerplant.type == PowerplantEnum.turbojet:
            return fuels[FuelEnum.kerosine] / powerplant.efficiency
        else:
            raise Exception("Trying to compute the cost for an unsupported type of powerplant.")

    def compute_merit_order(self):
        ordered_powerplants = [self.powerplants[0]]
        self.merit_order_val = [self.compute_cost(self.powerplants[0], self.fuels)]
        for i in range(1,len(self.powerplants)) :
            cost = self.compute_cost(self.powerplants[i], self.fuels)
            j = 0
            inserted = False
            while not inserted and j < len(self.merit_order_val):
                if cost <= self.merit_order_val[j]:
                    self.merit_order_val.insert(j, cost)
                    ordered_powerplants.insert(j, self.powerplants[i])
                    inserted = True
                j += 1
            if not inserted:
                self.merit_order_val.append(cost)
                ordered_powerplants.append(self.powerplants[i])
        self.powerplants = ordered_powerplants
