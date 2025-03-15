import pandas as pd
import numpy as np
import calendar
from joblib import load
# IMPORT PYWR MODULE FUNCTIONS
from pywr.parameters import Parameter

class SimulatedRelease(Parameter):
    def __init__(self, model, folder, reservoir_name, predictors, _type):
        super().__init__(model)
        self._model = model
        self._reservoir_name = reservoir_name; print(self._reservoir_name)
        self._release_model = load("{}/reservoirs/{}/release_model_013122.joblib".format(folder, reservoir_name))
        self._x_transformer = load("{}/reservoirs/{}/x_transformer_013122.joblib".format(folder, reservoir_name))
        self._y_transformer = load("{}/reservoirs/{}/y_transformer_013122.joblib".format(folder, reservoir_name))
        # LOAD INDEPENDENT RELEASE INFO
        self._predictors = predictors
        if _type:
            self._release_predictors = pd.read_csv("{}/reservoirs/{}/{}_release_predictors.csv".format(folder, reservoir_name, reservoir_name), parse_dates=True, index_col=[0])
        else:
            pass
        self._type = _type

    def value(self, timestep, scenario_index):
        # print("solving", self._reservoir_name)
        curr_date = "{}-{:02}-{:02}".format(self._model.timestep.year, self._model.timestep.month, self._model.timestep.day)
        if self._type:
            X_dataset = self._release_predictors.loc[curr_date, self._predictors].values
        else:
            current_storage = self._model.nodes["{}_reservoir".format(self._reservoir_name)].volume[0]
            current_inflow = self._model.nodes["{}_inflow".format(self._reservoir_name)].prev_flow[0]
            doy = pd.to_datetime(curr_date).dayofyear
            X_dataset = np.array([current_storage, current_inflow, doy])
        # print(X_dataset)
        # ADD CURRENT STORAGE VALUE
        # self._model.nodes['{}_inflow'.format(self._reservoir_name)].prev_flow
        # current_storage = self._model.nodes["{}_reservoir".format(self._reservoir_name)].volume[0]
        # X_raw = np.insert(X_dataset, 0, current_storage).reshape(1, -1)
        X_raw = X_dataset.reshape(1, -1)
        X_transform = self._x_transformer.transform(X_raw)
        y_hat = self._release_model.predict(X_transform)
        release = self._y_transformer.inverse_transform([y_hat])
        return release / 1.983

    @classmethod
    def load(cls, model, data):
        # print(data)
        folder = data["url"]["folder"]
        name = data["url"]["name"]
        predictors = data["url"]["predictors"]
        _type_ = data["url"]["type"]
        # print("reservoir_name", name, "predictors", predictors, _type_ )
        c = cls(model=model, folder=folder, reservoir_name=name, predictors=predictors, _type=_type_)
        return c
