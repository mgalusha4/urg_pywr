import numpy as np
from joblib import load
import time 
# IMPORT PYWR MODULE FUNCTIONS
from pywr.parameters import Parameter


class LFCCSimulation(Parameter):
    def __init__(self, model, folder):
        super().__init__(model)
        self._model = model 
        self._lfcc_model = load("{}/lfcc_model.joblib".format(folder))
        self._x_transformer = load("{}/x_transformer.joblib".format(folder))
        self._y_transformer = load("{}/y_transformer.joblib".format(folder))
        # PREDICTORS ARE RIOGRANDE AT SAN ACACIA 
        # NODE NAME IS rio_grande_sanacacia
        # DIVERSION TO SOCORRO | NODE NAME IS SNADV_irrigation
        # 
    def value(self, timestep, scenario_index):
        x1 = self._model.nodes["rio_grande_sanacacia"].prev_flow[0]
        x2 = self._model.nodes["SNADV_irrigation"].prev_flow[0]
        x3 = time.strptime("{}-{:02}-{:02}".format(self._model.timestep.year, self._model.timestep.month, self._model.timestep.day), "%Y-%m-%d").tm_yday
        X_dataset = np.array([x1, x2, x3])
        X_raw = X_dataset.reshape(1, -1)
        X_transform = self._x_transformer.transform(X_raw)
        y_hat = self._lfcc_model.predict(X_transform)
        release = self._y_transformer.inverse_transform([y_hat])[0][0]
        return np.max([0, release])

    @classmethod
    def load(cls, model, data):
        folder = data["url"]["folder"]
        c = cls(model=model, folder=folder)
        return c

class ReturnFlowNWR(Parameter):

    def __init__(self, model):
        super().__init__(model)   
        self.fraction_rf = 0.137 # Improvement - make it an input to the model
        

    def value(self, timestep, scenario_index):
    
        deliveries_to_district = \
            self.model.nodes['COCDV_irrigation'].prev_flow[0] \
            + self.model.nodes['ANGDV_irrigation'].prev_flow[0] \
            + self.model.nodes['ISLDV_irrigation'].prev_flow[0] \
            + self.model.nodes['SNADV_irrigation'].prev_flow[0]
            
        return self.fraction_rf * deliveries_to_district
        
    @classmethod
    def load(cls, model, data):
        return cls(model, **data)        