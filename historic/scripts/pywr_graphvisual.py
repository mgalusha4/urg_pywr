import json
import graphviz
import pandas as pd 
import numpy as np 
import matplotlib.pyplot as plt

folder = "../jsons"
filename = "model.json"

with open("{}/{}".format(folder, filename)) as f:
    model = json.load(f)

def search_includes(parent_file_url, includes_list=[]):
    # read the parent file 
    parent_folder = "/".join(parent_file_url.split("/")[:-1])
    with open(parent_file_url) as f:
        model = json.load(f)
    # search the parent file for "includes"
    # if there is none, we just append the parent file to includes_list, and return includes_list
    if "includes" not in model.keys():
        return includes_list
    # else, we loop through the list of names in the "includes"
    # for each name, we run the search_includes algorithm, and delete it from the "includes"    
    else:
        for url in ["{}/{}".format(parent_folder, uu) for uu in model["includes"]]:
            if url in includes_list:
                pass
            else:
                includes_list.append(url)
            search_includes(parent_file_url=url, includes_list=includes_list)
    return includes_list

parent_file = "{}/{}".format(folder, filename)
c = search_includes(parent_file_url=parent_file, includes_list=[parent_file])
all_nodes = []
all_edges = []
for file in c:
    with open(file) as f:
        model = json.load(f)
    all_nodes.append([n["name"] for n in model["nodes"]])
    all_edges.append([e for e in model["edges"]])

all_nodes_flat = [i for j in all_nodes for i in j]
all_edges_flat = [i for j in all_edges for i in j]
nodes = list({e[0] for e in all_edges_flat})
from_nodes = [e[0] for e in all_edges_flat]
to_nodes = [e[1] for e in all_edges_flat]
graph_build  = {}
for node in nodes:
    indices = [index for index, element in enumerate(from_nodes) if element == node]
    # print(node, np.array(to_nodes)[indices])
    graph_build[node] = np.array(to_nodes)[indices]            

fill_colors = {
    'storage': 'navy',
    'catchment': 'green',
    'input': 'deepskyblue',
    'output': 'red',
    'link': 'hotpink',
    'piecewiselink' : 'orange'
}

font_colors = {
    'storage': 'white',
    'catchment': 'white',
    'input': 'white',
    'output': 'white',
    'link': 'white',
    'piecewiselink' : 'white'
}

shapes = {
    'storage': 'ellipse',
    'catchment': 'ellipse',
    'input': 'ellipse',
    'output': 'ellipse',
    'link': 'rectangle',
    'piecewiselink' : 'rectangle'
}

subgraph_attrs = {
    'style': 'filled',
    'color': '#f0f0f0'
}    

dot = graphviz.Digraph(comment='RioGrande')
for section_file in c:
    section_name = section_file.split("/")[-1].split(".")[0]
    with open(section_file) as f:
        model = json.load(f)    
    with dot.subgraph(name=section_name) as sectn:
        current_nodes = [n for n in model["nodes"]]
        current_edges = [e for e in model["edges"]]
        for node in current_nodes:
            sectn.node(name=node["name"], color=fill_colors[node["type"]], 
                       shape=shapes[node["type"]], style='filled', 
                       fontcolor=font_colors.get(node["type"]))        
        sectn.edges(current_edges)
        sectn.attr(label=section_name)       

dot.format = 'svg'
dot.render(directory='doctest-output').replace('\\', '/')