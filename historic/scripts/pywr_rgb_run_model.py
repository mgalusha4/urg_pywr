# THIS SCRIPT IS THE MAIN SCRIPT THAT RUNS THE PYWR MODEL FOR THE RIO GRANDE 
# run this from the urg_pywr/historic/scripts folder

#IMPORT PACKAGES
import pandas as pd
import numpy as np
import datetime
import os
import json

# IMPORT PYWR MODULE FUNCTIONS
from pywr.core import Model

model_json_file = "../jsons/model.json"
model = Model.load(model_json_file)
model.run()
results = model.to_dataframe()
results.index.name = 'date'
results.to_csv("../output/results.csv")