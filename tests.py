import unittest
from classes import *

class TestClasses(unittest.TestCase):

    def setUp(self):
        self.prblm_inst = UCproblem(Payload.parse_obj(
            {
            "load": 480,
            "fuels":
            {
                "gas(euro/MWh)": 13.4,
                "kerosine(euro/MWh)": 50.8,
                "co2(euro/ton)": 20,
                "wind(%)": 60
            },
            "powerplants": [
                {
                "name": "gasfiredbig1",
                "type": "gasfired",
                "efficiency": 0.53,
                "pmin": 100,
                "pmax": 460
                },
                {
                "name": "gasfiredbig2",
                "type": "gasfired",
                "efficiency": 0.53,
                "pmin": 100,
                "pmax": 460
                },
                {
                "name": "gasfiredsomewhatsmaller",
                "type": "gasfired",
                "efficiency": 0.37,
                "pmin": 40,
                "pmax": 210
                },
                {
                "name": "tj1",
                "type": "turbojet",
                "efficiency": 0.3,
                "pmin": 0,
                "pmax": 16
                },
                {
                "name": "windpark1",
                "type": "windturbine",
                "efficiency": 1,
                "pmin": 0,
                "pmax": 150
                },
                {
                "name": "windpark2",
                "type": "windturbine",
                "efficiency": 1,
                "pmin": 0,
                "pmax": 36
                }
            ]
            }))

    def test_compute_cost(self):
        cost = self.prblm_inst.compute_cost(
            self.prblm_inst.powerplants[1], 
            self.prblm_inst.fuels)
        self.assertEqual(cost, 13.4 / 0.53)
    
    def test_compute_merit_order(self):
        self.prblm_inst.compute_merit_order()
        # Check that the computed costs are good.
        self.assertEqual(
            self.prblm_inst.merit_order_val, 
            [0, 0, 25.28301886792453, 25.28301886792453, 36.21621621621622, 169.33333333333334])
        # Check that the powerplants were reordered correctly.
        powerplants_names = []
        for powerplant in self.prblm_inst.powerplants :
            powerplants_names.append(powerplant.name)
        self.assertEqual(
            powerplants_names,
            ['windpark2', 'windpark1', 'gasfiredbig2', 'gasfiredbig1', 'gasfiredsomewhatsmaller', 'tj1'])

if __name__ == '__main__':
    unittest.main()