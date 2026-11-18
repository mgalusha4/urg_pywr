import json
import pandas as pd
import numpy as np

def get_reservoir_names(json_object):
    reservoir_names = [n["name"] for n in json_object["nodes"] if n["type"].lower() == "storage"]
    return ["_".join(r.split("_")[:-1]) for r in reservoir_names]

def create_borg_parameter_vector(size=2, number=7):
    # size = size of the control curve
    # number = number of reservoirs in the model
    cc = size * number
    vv = (size + 2) * number
    cc_lb = [0] * cc; vv_lb = [-10000] * vv; cc_lb.extend(vv_lb)
    cc_ub = [1] * cc; vv_ub = [10000] * vv; cc_ub.extend(vv_ub)
    return [cc_lb, cc_ub]

def _split_(cost_curve):
    """ generalised method to find the index
    where we split the cost curve into
    control curve and cost values """
    assert len(cost_curve) % 2 == 0, "check cost curve"
    return int( (len(cost_curve) - 2) / 2 )

def initialize_storage_volumes(pywr_model_object, future=False):
    initial_date = pywr_model_object.timestepper.start.date()
    month = initial_date.month
    year = initial_date.year
    if month == 1:
        month = 12; year = year-1
    else:
        month = month-1
    # SET THE INITIAL VOLUME OF ALL RESERVOIRS
    all_reservoirs = [r for r in [i.name for i in pywr_model_object.nodes] if "reservoir" in r]
    # print(all_reservoirs)
    for reservoir_model_name in all_reservoirs:
        res_object = pywr_model_object.nodes["{}".format(reservoir_model_name)]
        res_name = "_".join(reservoir_model_name.split("_")[:-1])
        # read initial volume from obesrvations
        try:
            obs_storage = pd.read_csv("../input/reservoirs/{}/obs_storage.csv".format(res_name), index_col=[0], parse_dates=True).dropna()
        except FileNotFoundError:
            res_name = "_".join(res_name.split("_")[:-1])
            obs_storage = pd.read_csv("../input/reservoirs/{}/obs_storage.csv".format(res_name), index_col=[0], parse_dates=True).dropna()
        try:
            init_vol = obs_storage.loc["{}-{}-01".format(initial_date.year, initial_date.month)].values[0]
        except KeyError:
            if future:
                init_vol = obs_storage.values[-1]
                print("future init vol", init_vol)
        res_object.initial_volume = init_vol
        # print(res_name, init_vol)
    return

def setup_cost_curve_dictionary(pywr_model_object, raw_borg_parameters):
    all_reservoirs = sorted(["_".join(r.split("_")[:-1]) for r in [i.name for i in pywr_model_object.nodes] if "reservoir" in r])
    rbg = len(raw_borg_parameters); ar = len(all_reservoirs)
    assert (rbg >= ar) & (rbg%ar == 0), "check length of raw borg parameter vector"
    # print(rbg, ar, rbg/ar, rbg%ar)
    control_curve_ix = int( (( ( rbg / ar ) - 2 ) / 2 ) * ar )
    # print("control_curve_ix", control_curve_ix)
    # set up a dictionary whose keys as the reservoir names
    # assign different sections of the parameter vector
    # to different keys in the dictionary
    ccp = np.array(raw_borg_parameters[:control_curve_ix]).reshape(ar, -1)
    for i in range(ccp.shape[1]-1):
        ccp[:, i+1] = ccp[:, i] + ((1 - ccp[:, i])*(ccp[:, i+1]))
    # ccp = ccp[:1, 0] * np.cumsum(ccp, axis=1)/np.sum(ccp, axis=1, keepdims=1)
    # print("ccp", ccp, "\n", ccp[:1, 0] * np.cumsum(ccp, axis=1)/np.sum(ccp, axis=1, keepdims=1))
    vp = np.array(raw_borg_parameters[control_curve_ix:]).reshape(ar, -1)
    return { all_reservoirs[i]:{"control_curve": ccp[i, :], "values": vp[i, :] } for i in range(ar)}

def set_storage_cost(pywr_model_object, cost_curve_dictionary):
    all_reservoirs = cost_curve_dictionary.keys()
    # print(all_reservoirs)
    for reservoir_name in all_reservoirs:
        pywr_model_object.parameters["cost_{}_storage".format(reservoir_name)].control_curves = cost_curve_dictionary[reservoir_name]["control_curve"]
        pywr_model_object.parameters["cost_{}_storage".format(reservoir_name)].values = cost_curve_dictionary[reservoir_name]["values"]
    return

def search_json_for_includes(parent_file_url, includes_list=[]):
    """recursive function to return the list
    containing the file paths of all model sections"""
    # read the parent file
    parent_folder = "/".join(parent_file_url.split("/")[:-1])
    with open(parent_file_url) as f:
        model = json.load(f)
    # search the parent file for "includes"
    # if there is none, we just return includes_list
    if "includes" not in model.keys():
        return includes_list
    # else, we loop through the list of names in the "includes"
    # for each name, we append it to includes_list and
    # recursively run the search algorithm
    else:
        for url in ["{}/{}".format(parent_folder, uu) for uu in model["includes"]]:
            if url in includes_list:
                pass
            else:
                includes_list.append(url)
            search_json_for_includes(parent_file_url=url, includes_list=includes_list)
    return includes_list

def load_json_file(jsonfile):
    with open(jsonfile) as f:
        json_object_in_memory = json.load(f)
    return json_object_in_memory

def instantiate_pwyr(parent_json_file):
    # IMPORT PYWR MODULE FUNCTIONS
    from pywr.core import Model
    # FUNCTIONS FOR RESERVOIR VOLUME TO AREA
    from pywr_class_reservoir_volume_area import VolumeAreaCurve, CurrentStorageMaxStorageGap
    VolumeAreaCurve.register()
    CurrentStorageMaxStorageGap.register()
    # FUNCTIONS FOR IRRIGATION DELIVERIES
    from pywr_class_get_irrigation_delivery import ComputeIrrigationReturn
    ComputeIrrigationReturn.register()
    from pywr_class_correctriochama import CorrectRioChamaFlow
    CorrectRioChamaFlow.register()
    from pywr_class_compact import RioGrandeCompactEBEIS
    RioGrandeCompactEBEIS.register()

    pywr_model_object = Model.load(parent_json_file)
    initialize_storage_volumes(pywr_model_object)
    return pywr_model_object

# def run_pywr(model_object):
#     # run model
#     model_object.run()

def get_number_reservoirs(parent_json_file):
    subfiles_list = search_json_for_includes(parent_file_url=parent_json_file, includes_list=[parent_json_file])
    i = 0
    for subfile in subfiles_list:
        json_object = load_json_file(jsonfile=subfile)
        # get reservoir names
        reservoir_names_in_subfile = get_reservoir_names(json_object=json_object)
        i += len(reservoir_names_in_subfile)
    return i

def setup_model(parent_json_file, reservoir_parameters=[0.5, 0, -100, -500]):
    # search for all subfiles of the system
    subfiles_list = search_json_for_includes(parent_file_url=parent_json_file, includes_list=[parent_json_file])
    # for each subfile # load json file into memory
    for subfile in subfiles_list:
        json_object = load_json_file(jsonfile=subfile)
        # get reservoir names
        reservoir_names_in_subfile = get_reservoir_names(json_object=json_object)
        # set storage cost curves for the reservoirs in the subfile
        for reservoir in reservoir_names_in_subfile:
            set_storage_cost(reservoir_name=reservoir, json_object=json_object, cost_curve=reservoir_parameters)
    # save newly setup model
    with open('{}'.format(subfile), 'w') as outfile:
        json.dump(json_object, outfile)
    return

def save_results(model_object, filename):
    results = model_object.to_dataframe()
    results.columns = results.columns.get_level_values(0)
    results.to_csv(filename)
