from pydantic import BaseModel
from enum import Enum

# Enumerations for accessing dictionaries.
class PowerplantEnum(Enum):
    gasfired = "gasfired"
    turbojet = "turbojet"
    windturbine = "windturbine"

class FuelEnum(Enum):
    gas = "gas(euro/MWh)"
    kerosine = "kerosine(euro/MWh)"
    co2 = "co2(euro/ton)"
    wind = "wind(%)"

# Models corresponding to the data provided in the POST request.
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

# The class representing a unit commitment problem.
class UCproblem():

    def __init__(self, payload: Payload) -> None :
        # Attributes directly related to the provided payload.
        self.load = payload.load
        self.fuels = payload.fuels
        self.powerplants = payload.powerplants
        # A list of costs of producing 1 MWh for each powerplant,
        # in ascending merit order (from the lowest to the highest costs).
        # self.merit_order_val[i] is the cost for self.powerplants[i]
        self.merit_order_val = None
        # The solution for the unit commitment problem. It is encoded
        # a list of floats, each float represing the power that needs to
        # be delivered by each powerplant. self.solution[i] corresponds 
        # to the power delivered by self.powerplants[i].
        self.solution = None
        # The sum of delivered power by the powerplants, as
        # currently specified in the solution.
        self.current_load = 0
    
    def compute_cost(self, powerplant: Powerplant, fuels: dict[FuelEnum, float]) -> float :
        """ The function computes the cost of 1 MWh produced by a given powerplant.

        Args:
            powerplant (Powerplant): the powerplant for which the cost needs to be computed.
            fuels (dict[FuelEnum, float]): the dictionary giving fuels costs. 

        Raises:
            Exception: attept to compute the cost for an unsupported type of powerplant.

        Returns:
            float: the cost to produce 1 MWh by the given powerplant.
        """
        if powerplant.type == PowerplantEnum.windturbine:
            return 0
        elif powerplant.type == PowerplantEnum.gasfired:
            return fuels[FuelEnum.gas] / powerplant.efficiency
        elif powerplant.type == PowerplantEnum.turbojet:
            return fuels[FuelEnum.kerosine] / powerplant.efficiency
        else:
            raise Exception("Trying to compute the cost for an unsupported type of powerplant.")

    def compute_merit_order(self) -> None :
        """ Orders self.powerplants by the ascending merit order (from the lowest to the highest
            cost). Also stores the costs in self.merit_order_val list.
        """
        ordered_powerplants = [self.powerplants[0]]
        self.merit_order_val = [self.compute_cost(self.powerplants[0], self.fuels)]

        for i in range(1,len(self.powerplants)) :
            # The cost of producing 1 MWh for the current powerplant.
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
    
    def compute_UC(self) -> bool :
        """ Computes the solution to the unit commitment problem.

        Returns:
            bool: True if a solution was found/computed.
        """
        # Solution initialization.
        self.compute_merit_order()
        self.solution = []
        for i in range(len(self.powerplants)) :
            self.solution.append(0)
        return self.build_solution()
    
    def get_p_min(self, powerplant: Powerplant) -> float :
        """ Provides the minimum power that a given powerplant 
            produces when it is turned on.

        Args:
            powerplant (Powerplant): the given powerplant.

        Returns:
            float: the minimum power.
        """
        if powerplant.type == PowerplantEnum.windturbine :
            return powerplant.pmax * self.fuels[FuelEnum.wind] / 100
        else :
            return powerplant.pmin
    
    def get_p_max(self, powerplant: Powerplant) -> float :
        """ Provides the maximum power that a given powerplant 
            produces when it is turned on.

        Args:
            powerplant (Powerplant): the given powerplant.

        Returns:
            float: the maximum power.
        """
        if powerplant.type == PowerplantEnum.windturbine :
            return powerplant.pmax * self.fuels[FuelEnum.wind] / 100
        else :
            return powerplant.pmax
    
    def decrease_total_load(self, powerplant: int) -> bool :
        """ If the load of the solution we are currently building 
            exceeds the goal load, we call this function to attempt to
            build a valid solution by decreasing the amount of power
            produced by the powerplants that come earlier in the merit order.

        Args:
            powerplant (int): the index of the powerplant from which we need
                                to start decreasing the delivered power.

        Returns:
            bool: True if a solution was found.
        """
        # we copy the current solution values and work on the copies.
        new_load = self.current_load
        new_solution = []
        for power in self.solution :
            new_solution.append(power)
        # We iterativelly try to decrease the power provided by the plants.
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
        """ A recursive function that builds the solution using the backtraking method.

        Args:
            powerplant (int, optional): The index of the powerplant we are currently 
                trying to add to the solution. We try to increase the power delivered
                by this powerplant to reach a solution.

        Returns:
            bool: True if a solution is found/computed.
        """
        # At each iteration there are 3 possible scenarios.
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
        """ Returns the solution in the format of the challenge specifications.

        Returns:
            list[dict]: of dictionaries specifying how much power each powerplant
                needs to provide to reach the goal load.
        """
        result = []
        for i in range(len(self.powerplants)) :
            result.append({'name' : self.powerplants[i].name,
                'p' :self.solution[i]})
        return result
