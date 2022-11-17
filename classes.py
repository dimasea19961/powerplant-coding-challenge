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

    def __init__(self, payload: Payload) -> None :
        # Attributes directly related to the provided payload.
        self.load = payload.load
        self.fuels = payload.fuels
        self.powerplants = payload.powerplants
        # A list of costs of producing 1 MWh for each powerplant,
        # in ascending order (merit order).
        self.merit_order_val = None
        # The solution for the unit commitement problem.
        self.solution = None
        # The sum of delivered power by the powerplants, as
        # currently specified in the solution.
        self.current_load = 0
    
    def compute_cost(self, powerplant: Powerplant, fuels: dict[FuelEnum, float]) -> float :
        if powerplant.type == PowerplantEnum.windturbine:
            return 0
        elif powerplant.type == PowerplantEnum.gasfired:
            return fuels[FuelEnum.gas] / powerplant.efficiency
        elif powerplant.type == PowerplantEnum.turbojet:
            return fuels[FuelEnum.kerosine] / powerplant.efficiency
        else:
            raise Exception("Trying to compute the cost for an unsupported type of powerplant.")

    def compute_merit_order(self) -> None :

        ordered_powerplants = [self.powerplants[0]]
        self.merit_order_val = [self.compute_cost(self.powerplants[0], self.fuels)]

        for i in range(1,len(self.powerplants)) :
            # The cost of producing one MWh for the current powerplant.
            cost = self.compute_cost(self.powerplants[i], self.fuels)
            # Insertion of the powerplant according to the merit order
            # (ascending order, i.e. the powerplant having the lowest operating
            # cost will be at index 0 in self.powerplants).
            j = 0
            inserted = False
            while not inserted and j < len(self.merit_order_val):
                if cost <= self.merit_order_val[j]:
                    self.merit_order_val.insert(j, cost)
                    ordered_powerplants.insert(j, self.powerplants[i])
                    inserted = True
                j += 1
            # Append at the end of the list if the current cost is the highest.
            if not inserted:
                self.merit_order_val.append(cost)
                ordered_powerplants.append(self.powerplants[i])
        self.powerplants = ordered_powerplants
    
    def compute_UC(self) -> list[dict] :
        # Solution initialization.
        self.compute_merit_order()
        self.solution = []
        for i in range(len(self.powerplants)) :
            self.solution.append(0)
        return self.build_solution()
    
    def get_p_min(self, powerplant: Powerplant) -> float :
        if powerplant.type == PowerplantEnum.windturbine :
            return powerplant.pmax * self.fuels[FuelEnum.wind] / 100
        else :
            return powerplant.pmin
    
    def get_p_max(self, powerplant: Powerplant) -> float :
        if powerplant.type == PowerplantEnum.windturbine :
            return powerplant.pmax * self.fuels[FuelEnum.wind] / 100
        else :
            return powerplant.pmax
    
    def decrease_total_load(self, powerplant: int) -> bool :
        # we copy the current solution values and work on the copies.
        new_load = self.current_load
        new_solution = []
        for power in self.solution :
            new_solution.append(power)
        while powerplant >= 0:
            # Check if it is possible to decrease the power provided
            # by the currently considered powerplant.
            if self.get_p_min(self.powerplants[powerplant]) < new_solution[powerplant] :
                possible_decrease = new_solution[powerplant] - self.get_p_min(self.powerplants[powerplant])
                # If we can decrease up to the goal load, than a solution is found.
                if new_load - possible_decrease <= self.load :
                    # We register the solution.
                    new_solution[powerplant] = new_solution[powerplant] - (new_load - self.load)
                    self.current_load = sum(new_solution)
                    self.solution = new_solution
                    return True
                # The amount we can decrease is not sufficiant to reach the goal load.
                # We decrease as much as possible and consider the following powerplant.
                else:
                    new_solution[powerplant] = new_solution[powerplant] - possible_decrease
                    new_load -= possible_decrease
            powerplant -= 1

        return False
    
    def build_solution(self, powerplant: int = 0) -> bool :
        # At each iteration there are 3 possible scenarios
        # (1) By adding the Pmax of the current powerplant,
        # we do not reach the desired load.
        if self.current_load + self.get_p_max(self.powerplants[powerplant]) < self.load :
            # We set the delivered power to Pmax.
            self.solution[powerplant] = self.get_p_max(self.powerplants[powerplant])
            self.current_load += self.get_p_max(self.powerplants[powerplant])
            # We try to complete the current solution by making a recursiv
            # call to the next powerplant in the merit order.
            if self.build_solution(powerplant+1) :
                return True
            else :
                self.solution[powerplant] = 0
                self.current_load -= self.get_p_max(self.powerplants[powerplant])
                return False

        # (2) If by adding the Pmin we exceed the desired load, than we try
        # to build a solution by reducing the amount of power delivered by 
        # powerplants which appear earlier in the merit order.
        elif self.current_load + self.get_p_min(self.powerplants[powerplant]) > self.load :
            self.solution[powerplant] = self.get_p_min(self.powerplants[powerplant])
            self.current_load += self.solution[powerplant]
            if self.decrease_total_load(powerplant-1) :
                return True
            else :
                self.solution[powerplant] = 0
                self.current_load -= self.get_p_min(self.powerplants[powerplant])
                return False
        # (3) Otherwise it means that we can add the desired power to reach the goal load.
        else:
            self.solution[powerplant] = self.load - self.current_load
            self.current_load += self.solution[powerplant]
            return True
        
    def get_solution(self) -> list[dict] :
        result = []
        for i in range(len(self.powerplants)) :
            result.append({'name' : self.powerplants[i].name,
                'p' :self.solution[i]})
        return result
