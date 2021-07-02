# Modeling the situation where an agent has to decide how to route his flow on a directed network,
# when a fixed cost of edges must be payed if the edges are used. Edges also have some capacity
# The agent has some demands between nodes

import numpy as np # Basic functions, as random 
import matplotlib.pyplot as plt #For plotting
from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX

#Setting a seed
np.random.seed(1)

# ------- DATA --------
V = {0:(0,0), 1:(1,0), 2:(1,1), 3:(0,1)} # Dictionary with the nodes and their location
E = {(i,j) for j in range(len(V)) for i in range(len(V)) if i!=j} # Dictionary with all possible edges between nodes
# We use dictionaries for V and E because it is handy when creting the model with Model()
q = 5 # Capacity of each edge is q
c = 3 # Cost of stablishing one edge is 3
demands ={i:np.random.randint(0,q) for i in E} # Random demands between pairs of nodes
print(demands, '\n')
r = 2 # Revenue of satisfying each unit of demand



def build_no_info_problem(V, E, q, c, r, demands, **kwargs):
    # Takes as input the nodes, V, the edges, E, q the capacity of the edges, r the revenue per unit of demand, c the cost of each edge and the demands between pairs of nodes
    mdl = Model('Single agent no info', **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,demand) for edge in E for demand in demands],name = 'f') # Binary variable indicating if a demand is routed in some edge
    mdl.u = mdl.binary_var_dict(E,name = 'e') # Binary variable which would indicate if an edge is used or not.

    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[(v,z),d] for v in V if v!=z) == mdl.sum(mdl.f[(z,w),d] for w in V if w!=z) for d in demands for z in V if z!=d[0] and z!=d[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[(d[0],v),d] for v in V if v !=d[0]) <= 1 for d in demands) # Second constraint: Flow from source can only be one at max   (*)
    # mdl.add_constraints(mdl.sum(mdl.f[(z,v),d] for v in V if v !=z) <= 1 for z in V if z!=d[1] for d in demands) # Second'' constraint: A commodity can leave a node only once at max (similar to (*) but avoid subtours. No difference in objective value, but seems more reasonable)
    mdl.add_constraints(mdl.sum(mdl.f[(d[1],v),d] for v in V if v !=d[1]) == 0 for d in demands) # Third constraint: Commodities dont flow from terminal to other nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d]*demands[d] for d in demands) <= (q * mdl.u[e]) for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity

    # --- objective ---
    mdl.demands_revenues = mdl.sum(mdl.sum(mdl.f[((v,d[1]),d)]*demands[d]*r for v in V if v != d[1]) for d in demands)
    mdl.add_kpi(mdl.demands_revenues, "Demands revenue")
    mdl.edges_costs = mdl.sum(mdl.u[e]*c for e in E)
    mdl.add_kpi(mdl.edges_costs, "Edges costs")
    mdl.maximize(mdl.demands_revenues - mdl.edges_costs )

    return mdl

def print_no_info_solution(mdl):
    obj = mdl.objective_value
    print("* Single agent model solved with objective: {:g}".format(obj))
    print("* Total demands revenue=%g" % mdl.demands_revenues.solution_value)
    print("* Total edges costs=%g" % mdl.edges_costs.solution_value, '\n')


def recover_data(mdl,E,demands):
    active_edges = {e:0 for e in E if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
    active_flow= [flow_var for flow_var in [(edge,demand) for edge in E for demand in demands] if mdl.f[flow_var].solution_value>0.9]

    served_demands = {d[1]:None for d in active_flow} # Dictionary with the satisfied demands as keys
    
    # We assign to each satisfied demand its proper flow from origin to terminal
    for d in served_demands:
        used_edges = [flow_var[0] for flow_var in active_flow if flow_var[1] == d]
        prev = d[0]
        path = []
        while(prev != d[1]):
            for e in used_edges:
                if e[0] == prev:
                    path.append(e)
                    used_edges.remove(e)
                    prev = e[1]
        served_demands[d] = path

    # We assign to each edge, its used capacity
    for d in served_demands:
        for e in served_demands[d]:
            active_edges[e] += demands[d]

    return served_demands, active_edges



# ----------------------------------------------------------------------------
# Solve the model and display the result
# ----------------------------------------------------------------------------

# Build the model
model = build_no_info_problem(V,E,q,c,r,demands)
# model.print_information()

# Solve the model.
if model.solve():
    print_no_info_solution(model)
    satisfied_demand, used_edges = recover_data(model,E,demands)
else:
    print("Problem has no solution")


print('Satisfied demands:', satisfied_demand)
print('Used edges:', used_edges)
