# THIS SCRIPT IS THE MAIN SCRIPT THAT RUNS THE PYWR MODEL FOR THE RIO GRANDE 
# run this from the urg_pywr/historic/scripts folder

# IMPORT HELPER FUNCTIONS
from pywr_calibration_fitness import initialize_storage_volumes

#IMPORT PACKAGES
import pandas as pd
import numpy as np
import datetime
import os
import json

# IMPORT PYWR MODULE FUNCTIONS
from pywr.core import Model
# FUNCTIONS FOR RESERVOIR VOLUME TO AREA
from pywr_class_reservoir_volume_area import VolumeAreaCurve
VolumeAreaCurve.register()
# FUNCTIONS FOR OBS RELEASE
from pywr_class_sim_release import SimulatedRelease
SimulatedRelease.register()
# import the custom parameter for el vado max release
from pywr_class_elvado_max_release import ElVado_max_relase
ElVado_max_relase.register()
# LFCC MODEL
from pywr_class_lfcc_simulation import LFCCSimulation
LFCCSimulation.register()
# RETURN FLOW WILDLIFE REFUGE
from pywr_class_lfcc_simulation import ReturnFlowNWR
ReturnFlowNWR.register()




# file path to the mother json file
model_json_file = "../jsons/model.json"
# initiate the model
model = Model.load(model_json_file)
# initialize the reservoir storage values 
initialize_storage_volumes(model)
# RUN THE MODEL!! WAHOO
model.run()
# save the results 
results = model.to_dataframe()
results.columns = results.columns.get_level_values(0)
results.index.name = 'date'
results.to_csv("../output/results.csv")