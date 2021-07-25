'''
Script to automatize the process of generate instances, given certain parameters as input
'''

import pandas as pd
import numpy as np
import os

# ---------------------------------------------
# ----------- INSTANCE PARAMETERS -------------
# ---------------------------------------------

# ------ Variable parameters
# Number of agents
N = 5
# Capacity ratio: high/low
cap_ratio = 'low'
# Number of instances to generate
num_instances = 5

# ------ Fixed parameters
# Number of vertices
V = 7
# Intervals specifying min and max values for the edges and commodities values
edges_cost = [3,6]
commodities_revenue = [1,2]
commodities_units = [0,5]
if cap_ratio == 'high':
    # High capacity 
    edges_capacity = [5,12]
elif cap_ratio == 'low':
    # Low capacity
    edges_capacity = [2,8]


for inst in range(num_instances):
    # Instance name
    instance_name = '%d_%s_%d' %(N,cap_ratio,inst)

    # -----------------------------
    # ---- INSTANCE GENERATION ----
    # -----------------------------

    commodities = {i:pd.DataFrame(columns = ['origin','terminal','owner','units','revenue'])for i in range(N)}
    edges = {i:pd.DataFrame(columns=['head','tail','owner','cost','capacity']) for i in range(N)}

    for i in range(N):
        for v in range(V):
            for w in range(V):
                if v!=w:
                    commodities[i] = commodities[i].append({'origin': v, 'terminal': w, 'owner':i,
                                        'units':np.random.randint(commodities_units[0],commodities_units[1]),
                                        'revenue':np.random.randint(commodities_revenue[0],commodities_revenue[1])},
                                        ignore_index=True)

                    edges[i] = edges[i].append({'head': v, 'tail': w, 'owner':i,
                                'cost':np.random.randint(edges_cost[0],edges_cost[1]),
                                'capacity':np.random.randint(edges_capacity[0],edges_capacity[1])},
                                ignore_index=True)


    # ----------------------------------
    # ----- CREATION INSTANCE FILE -----
    # ----------------------------------

    file = open(os.path.join(os.path.join(os.path.dirname(__file__),instance_name)),"w")

    file.write('%d %d\n' %(N,V))
    for i in range(N):
        file.write('Agent \n')
        file.write('%d \n' %(i))
        file.write('Commodities \n')
        file.write(commodities[i].to_string(header=False, index=False))
        file.write('\n')
        file.write('Edges \n')
        file.write(edges[i].to_string(header=False, index=False))
        file.write('\n')

    file.close()
