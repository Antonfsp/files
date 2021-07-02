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
print(demands)
r = 2 # Revenue of satisfying each unit of demand



# --------- PLOT OF NODES ------------------

# Plotting the nodes
# plt.scatter([V[j][0] for j in range(len(V))],[V[i][1] for i in range(len(V))])
# for i in range(len(V)):
#    plt.annotate(i,(V[i][0]+0.01,V[i][1])) #+0.01 just for moving the label lightly to the right
# plt.show()




# ---------- CREATING THE MODEL ------------

mdl = Model('Single agent no info')

# Adding the decision variables
#Create the idx for the next decision variable. It has 2 elements, each a double. First, the edge, secondly, the demand

f = mdl.binary_var_dict([(edge,demand) for edge in E for demand in demands],name = 'f') # Binary variable indicating if a demand is routed in some edge
u = mdl.binary_var_dict(E,name = 'u') # Binary variable which would indicate if an edge is used or not.

# Creating the objective function
#mdl.total_revenues(mdl.sum(mdl.sum(f[(d,(d[0],v))]*demands[d]*r for v in V if v != d[0]) for d in demands))
#mdl.total_costs(mdl.sum(u[e]*c for e in E))
mdl.maximize(mdl.sum(mdl.sum(f[((v,d[1]),d)]*demands[d]*r for v in V if v != d[1]) for d in demands) - mdl.sum(u[e]*c for e in E))

# Creating the constraints
mdl.add_constraints(mdl.sum(f[(v,z),d] for v in V if v!=z) == mdl.sum(f[(z,w),d] for w in V if w!=z) for d in demands for z in V if z!=d[0] and z!=d[1]) # First constraints: Flow over transit nodes
mdl.add_constraints(mdl.sum(f[(d[0],v),d] for v in V if v !=d[0]) <= 1 for d in demands) # Second constraint: Flow from source can only be one at max   (*)
# mdl.add_constraints(mdl.sum(f[(z,v),d] for v in V if v !=z) <= 1 for z in V if z!=d[1] for d in demands) # Second'' constraint: A commodity can leave a node only once at max (similar to (*) but avoid subtours. No difference in objective value, but seems more reasonable)
mdl.add_constraints(mdl.sum(f[(d[1],v),d] for v in V if v !=d[1]) == 0 for d in demands) # Third constraint: Commodities dont flow from terminal to other nodes
mdl.add_constraints(mdl.sum(f[e,d]*demands[d] for d in demands) <= (q * u[e]) for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity

# Solving the model
solution = mdl.solve(log_output=False)
print(solution)


# --------- RECOVERING DATA FROM THE SOLUTION ----------

active_edges = {e:0 for e in E if u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
print('Active edges:', active_edges)

active_flow= [flow_var for flow_var in [(edge,demand) for edge in E for demand in demands] if f[flow_var].solution_value>0.9]

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
print('Served:demands:', served_demands) # Dictionary of servec demands, with a list of its path from origin to terminal nodes as value

# We assign to each edge, its used capacity
for d in served_demands:
    for e in served_demands[d]:
        active_edges[e] += demands[d]

print('Active edges', active_edges) # Dictionary of used edges with its used capacities as values


#-------- PLOTTING SOLUTION ---------

# Plotting the nodes
plt.scatter([V[j][0] for j in range(len(V))],[V[i][1] for i in range(len(V))])
for i in range(len(V)):
    plt.annotate(i,(V[i][0]+0.01,V[i][1])) #+0.01 just for moving the label lightly to the right

# Drawing active (directed) edges
for e in active_edges:
    plt.annotate("",
                xy=(V[e[0]][0], V[e[1]][0]), xycoords='data',
                xytext=(V[e[0]][1], V[e[1]][1]), textcoords='data',
                arrowprops=dict(arrowstyle="->", color="0.5",
                                shrinkA=5, shrinkB=5,
                                patchA=None, patchB=None,
                                connectionstyle="arc3,rad=0.05",
                                ),
                )
plt.draw()
print('Code continues')
plt.show()