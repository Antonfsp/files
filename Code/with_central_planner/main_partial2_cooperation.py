
# Python packages
import numpy as np # Basic functions, as random 
import matplotlib.pyplot as plt #For plotting

# Own scripts
from classes import Agent, CentralizedSystem, Commodity, Edge
import single_agent_model as samdl
import central_planner_model as cpmdl

# -------------------------------------------------------------------------
#  INSTANCE DATA
# -------------------------------------------------------------------------

#Setting a seed
np.random.seed(1)

# N = 2 # Number of agents
# V = {0:(0,0), 1:(1,0), 2:(1,1), 3:(0,1)} # Dictionary with the nodes and their location
# E = {(i,j) for j in range(len(V)) for i in range(len(V)) if i!=j} # Dictionary with all possible edges between nodes
# # We use dictionaries for V and E because it is handy when creting the model with Model()
# q = 5 # Capacity of each edge is q
# c = 3 # Cost of stablishing one edge is 3
# #commodities = {agent:{i:np.random.randint(0,q) for i in E} for agent in range(N)} # Random commodities between pairs of nodes
# r = 2 # Revenue of satisfying each unit of commodity




file = open('instance.txt','r')
lines_list = file.readlines()
N, V = (int(x) for x in lines_list[0].split())
V = {i for i in range(V)}
commodities = {i:{} for i in range(N)}
edges = {i:{} for i in range(N)}

for line in lines_list[1:]:
    if line.rstrip() == 'Agent':
        prev = 'Agent'
    elif line.rstrip() == 'Commodities':
        prev = 'Commodities'
    elif line.rstrip() == 'Edges':
        prev = 'Edges'
    else:
        if prev == 'Agent':
            owner = int(line)
        if prev == 'Commodities':
            temp = [int(x) for x in line.split()]
            commodities[owner][(temp[0],temp[1],temp[2])] = Commodity(temp[0],temp[1],temp[2],temp[3],temp[4])
        if prev == 'Edges':
            temp = [int(x) for x in line.split()]
            edges[owner][(temp[0],temp[1],temp[2])] = Edge(temp[0],temp[1],temp[2],temp[3],temp[4])

# ------ Creating the agents objects ----------

agents_list = []
for i in range(N):
    agents_list.append(Agent(i,edges[i],commodities[i]))


# ----------------------------------------------------------------------------
# Solving the model and display the result for each agent
# ----------------------------------------------------------------------------

for agent in agents_list:

    # Build the model
    model = samdl.build_single_agent_model(V,agent.edges,agent.commodities)
    # model.print_information()

    # Solve the model.
    if model.solve():
        # samdl.print_no_info_solution(model)
        samdl.recover_data_single_agent(model,agent)
        agent.payoff_no_cooperation = model.objective_value
        agent.payoff_cooperation = - model.edges_costs.solution_value
    else:
        print("Problem has no solution")


    # print('Served commodities:', agent.served_commodities)
    # print('Used edges:', agent.active_edges)
    # print('Unserved commodities:', agent.unserved_commodities)
    # print('Edges with free capacity:', agent.edges_free_capacity, '\n')


# Now we pass to the partial2 cooperation model with leftovers (edges and commodities) from each agent. 
# The agents will pay the proportional cost of the fraction of edge capacity they use respect to the total capacity of the edge
# For this, it will be necessary to keep track of who is the owner of each edge and commodity. 
# Conflics can happen if a commodity can be routed for multiple paths (always choose shortest 
# path as it will make the owner to pay less). Also if multiple commodities (but not all together) can
# be route in the same edge. This could be solved including some kind of extra payment for routing the
# commodity which doesn't fit. Also a commodity could be route at the same price for the customer, at different paths. How to choose?


# -------------------------------------------------------------
# --- MODEL WITH PARTIAL2 COOPERATION
# -------------------------------------------------------------

central_planner = CentralizedSystem(agents_list,'partial2_cooperation')

agents_minimal_profit = []
for agent in agents_list:
    agents_minimal_profit.append(agent.payoff_no_cooperation - agent.payoff_cooperation)

print(agents_minimal_profit)
# ----------------------------------------
# SOLVING THE PARTIAL2 COOPERATION MODEL
# ----------------------------------------

# print(central_planner.commodities)
# print(central_planner.edges)

# Build the model
model = cpmdl.build_cooperation_model(V,central_planner.edges,central_planner.commodities,'partial2_cooperation',agents_minimal_profit)
# model.print_information()

# Solve the model.
if model.solve():
    cpmdl.print_cooperation_solution(model)
    cpmdl.recover_data_cooperation(model, central_planner,'partial2_cooperation')

    # ------ Recover how much each agent earn in the second stage
    for c in central_planner.served_commodities:
        agents_list[c[2]].payoff_cooperation += agents_list[c[2]].commodities[c].units*agents_list[c[2]].commodities[c].revenue
        for e in central_planner.commodities[c].route:
            if e[2] != c[2]:
                side_payment =  agents_list[c[2]].commodities[c].units * agents_list[e[2]].edges[e].cost/agents_list[e[2]].edges[e].original_capacity
                agents_list[e[2]].payoff_cooperation += side_payment
                agents_list[c[2]].payoff_cooperation -= side_payment

    # ---------------------------------
    # ---- PRINTING RESULTS FROM PARTIAL2 COOPERATION
    # ---------------------------------

    for agent in agents_list:
        print('Agent %s would have earned %s without cooperation and earns %s cooperating' % (agent.id,agent.payoff_no_cooperation,agent.total_payoff('partial2_cooperation')))
else:
    print("Problem has no solution")

