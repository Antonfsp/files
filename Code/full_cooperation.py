"""
Modeling the situation where multiple agents have to decide how to route their flow on a directed network,
 when a fixed cost of edges must be payed if the edges are used. Edges also have some capacity
 The agents have some demands between nodes
"""

import numpy as np # Basic functions, as random 
import matplotlib.pyplot as plt #For plotting
from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX
import itertools as it


#Setting a seed
np.random.seed(1)

# --------------------------------------
# ------- AGENTS CLASS --------
# --------------------------------------

class Agent:

    def __init__(self,id,E,q):
        self.id = id
        self.demands = {i:np.random.randint(0,q) for i in E}  # Random demands between pairs of nodes
        self.used_edges = None
        self.satisfied_demands= None
        self.unsatisfied_demands = None
        self.edges_free_capacity = None
        self.profit_first_stage = 0
        self.profit_second_stage = 0

    @property
    def total_profit(self):
        return self.profit_first_stage + self.profit_second_stage


# --------------------------------------
# ------- CENTRAL PLANNER CLASS --------
# --------------------------------------

class CentralizedSystem:

    def __init__(self,AGENTS):
        self.demands = {}
        self.edges = {}
        self.satisfied_demands= None
        self.unsatisfied_demands = None

        self.create_demands_set(AGENTS)
        self.create_edges_set(AGENTS)


    def create_demands_set(self,agents):
        for i in agents:
            for d in i.unsatisfied_demands:
                self.demands[(d[0],d[1],i.id)] = i.unsatisfied_demands[d]
    
    def create_edges_set(self,agents):
        for i in agents:
            for e in i.edges_free_capacity:
                self.edges[(e[0],e[1],i.id)] = i.edges_free_capacity[e]
        


# -----------------------------------
# ITERTOOLS RECIPES
# -----------------------------------

def powerset(iterable,min_subset):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(min_subset, len(s)+1))


# -------------------------------------------------------
# FUNCTIONS FOR CREATING THE NO INFORMATION MODEL
# -------------------------------------------------------

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
    mdl.profit = mdl.demands_revenues - mdl.edges_costs
    mdl.add_kpi(mdl.profit, 'Profit agent')
    mdl.used_capacity = mdl.sum(mdl.sum(mdl.f[e,d]*demands[d] for d in demands) for e in E)
    mdl.add_kpi(mdl.used_capacity, 'Used capacity')
    mdl.maximize_static_lex([mdl.profit, - mdl.used_capacity])


    return mdl

def print_no_info_solution(mdl):
    obj = mdl.objective_value
    model.report_kpis()
    print("* Single agent model solved with objective: {:g}".format(obj))
    print("* Total demands revenue=%g" % mdl.demands_revenues.solution_value)
    print("* Total edges costs=%g" % mdl.edges_costs.solution_value, '\n')


def recover_data_no_info(mdl,E,demands,q):
    active_edges = {e:0 for e in E if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
    edges_free_capacity = {}  
    active_flow= [flow_var for flow_var in [(edge,demand) for edge in E for demand in demands] if mdl.f[flow_var].solution_value>0.9]
    served_demands = {d[1]:None for d in active_flow} # Dictionary with the satisfied demands as keys
    unserved_demands = {}
  
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

    # We get dictionary of demands of the agent which are not served (and are different to 0)
    for d in demands:
        if d not in served_demands and demands[d] != 0:
            unserved_demands[d] = demands[d]

    for e in active_edges:
        if active_edges[e] < q:
            edges_free_capacity[e] = q - active_edges[e]

    return served_demands, active_edges, unserved_demands, edges_free_capacity





# -------------------------------------------------------
# FUNCTIONS FOR CREATING THE FULL COOPERATION MODEL
# -------------------------------------------------------

def build_full_cooperation_problem(N,V, E, q, c, r, demands, **kwargs):
    # Takes as input the number of agents, N, the nodes, V, the edges, E, that are tuples (v,w,i) and have some capacity, r the revenue per unit of demand, c the cost of each edge and the demands between pairs of nodes (which also are tuples (v,w,i) where i is is owner)
    mdl = Model('Full cooperation', **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,demand) for edge in E for demand in demands],name = 'f') # Binary variable indicating if a demand is routed in some edge

    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[1] == z) == mdl.sum(mdl.f[e,d] for e in E if e[0]==z) for d in demands for z in V if z!=d[0] and z!=d[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] == d[0]) <= 1 for d in demands) # Second constraint: Flow from source can only be one at max   (*)
    # mdl.add_constraints(mdl.sum(mdl.f[(z,v),d] for v in V if v !=z) <= 1 for z in V if z!=d[1] for d in demands) # Second'' constraint: A commodity can leave a node only once at max (similar to (*) but avoid subtours. No difference in objective value, but seems more reasonable)
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] ==d[1]) == 0 for d in demands) # Third constraint: Commodities dont flow from terminal to other nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d] * demands[d] for d in demands) <= E[e] for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] in S and e[1] in S) <= len(S) -1 for S in powerset(V,2) for d in demands) # Subtour elimination constraints

    # --- objective ---
    mdl.revenues = mdl.sum(mdl.sum(mdl.f[e,d] * r for e in E if e[1] == d[1]) - mdl.sum(mdl.f[e,d] * c/q for e in E if e[2]!=d[2]) for d in demands)
    mdl.add_kpi(mdl.revenues, "Demands revenue")
    mdl.maximize(mdl.revenues)

    return mdl

def print_full_cooperation_solution(mdl):
    obj = mdl.objective_value
    print("* Full cooperation solved with objective: {:g}".format(obj))


def recover_data_full_cooperation(mdl,E,demands,q):
    active_flow= [flow_var for flow_var in [(edge,demand) for edge in E for demand in demands] if mdl.f[flow_var].solution_value>0.9]
    served_demands = {d[1]:None for d in active_flow} # Dictionary with the satisfied demands as keys
    unserved_demands = {}
  
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
            E[e] -= demands[d]



    return served_demands, unserved_demands




# -------------------------------------------------------------------------
#  INSTANCE DATA
# -------------------------------------------------------------------------

N = 2 # Number of agents
V = {0:(0,0), 1:(1,0), 2:(1,1), 3:(0,1)} # Dictionary with the nodes and their location
E = {(i,j) for j in range(len(V)) for i in range(len(V)) if i!=j} # Dictionary with all possible edges between nodes
# We use dictionaries for V and E because it is handy when creting the model with Model()
q = 5 # Capacity of each edge is q
c = 3 # Cost of stablishing one edge is 3
#demands = {agent:{i:np.random.randint(0,q) for i in E} for agent in range(N)} # Random demands between pairs of nodes
r = 2 # Revenue of satisfying each unit of demand


# ------ Creating the agents objects ----------

agents = []
for i in range(N):
    agents.append(Agent(i,E,q))


# ----------------------------------------------------------------------------
# Solving the model and display the result for each agent
# ----------------------------------------------------------------------------

for agent in agents:

    # Build the model
    model = build_no_info_problem(V,E,q,c,r,agent.demands)
    # model.print_information()

    # Solve the model.
    if model.solve():
        print_no_info_solution(model)
        agent.satisfied_demands, agent.used_edges, agent.unsatisfied_demands, agent.edges_free_capacity = recover_data_no_info(model,E,agent.demands,q)
        agent.profit_first_stage = model.objective_value
    else:
        print("Problem has no solution")


    print('Satisfied demands:', agent.satisfied_demands)
    print('Used edges:', agent.used_edges)
    print('Unsatisfied demand:', agent.unsatisfied_demands)
    print('Edges with free capacity:', agent.edges_free_capacity, '\n')


    # Now we pass to the full cooperation model with leftovers (edges and demands) from each agent. 
    # The agents will pay the proportional cost of the fraction of edge capacity they use respect to the total capacity of the edge
    # For this, it will be necessary to keep track of who is the owner of each edge and commodity. 
    # Conflics can happen if a commodity can be routed for multiple paths (always choose shortest 
    # path as it will make the owner to pay less). Also if multiple commodities (but not all together) can
    # be route in the same edge. This could be solved including some kind of extra payment for routing the
    # commodity which doesn't fit. Also a commodity could be route at the same price for the customer, at different paths. How to choose?



# ------ Creating central planner object based in the agents situation

central_planner = CentralizedSystem(agents)




# ----------------------------------------
# SOLVING THE FULL COOPERATION MODEL
# ----------------------------------------


print(central_planner.demands)
print(central_planner.edges)

# Build the model
model = build_full_cooperation_problem(N,V,central_planner.edges,q,c,r,central_planner.demands)
model.print_information()

# Solve the model.
if model.solve():
    print_full_cooperation_solution(model)
    central_planner.satisfied_demands, central_planner.unsatisfied_demands = recover_data_full_cooperation(model, central_planner.edges, central_planner.demands, q)
else:
    print("Problem has no solution")

# ------ Recover how much each agent earn in the second stage
for d in central_planner.satisfied_demands:
    agents[d[2]].profit_second_stage += agents[d[2]].demands[(d[0],d[1])]*r 
    for e in central_planner.satisfied_demands[d]:
        if e[2] != d[2]:
            price =  agents[d[2]].demands[(d[0],d[1])] * c/q
            agents[e[2]].profit_second_stage += price
            agents[d[2]].profit_second_stage -= price

for agent in agents:
    print(agent.profit_second_stage)
    print(agent.total_profit)









# solution_pool = model.populate_solution_pool()


# print("Here!")
# #Look into all the solution and take the one with the lowest number of active variables?
# print(solution_pool.size)
# for i in range(solution_pool.size):
#     print(sum(solution_pool._solutions[i].get_value_dict(model.f).values())) 

# for i in range(solution_pool.size):
#     print(solution_pool._solutions[i])

