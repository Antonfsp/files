
# Python packages
import numpy as np # Basic functions, as random 
import matplotlib.pyplot as plt #For plotting

# Own scripts
from classes import Agent, CentralizedSystem
import single_agent_model as samdl
import central_planner_model as cpmdl

# -------------------------------------------------------------------------
#  INSTANCE DATA
# -------------------------------------------------------------------------

#Setting a seed
np.random.seed(1)

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
    agents.append(Agent(i,E,q,c,r))


# ----------------------------------------------------------------------------
# Solving the model and display the result for each agent
# ----------------------------------------------------------------------------

for agent in agents:

    # Build the model
    model = samdl.build_single_agent_model(V,agent.edges,agent.demands)
    # model.print_information()

    # Solve the model.
    if model.solve():
        # samdl.print_no_info_solution(model)
        agent.satisfied_demands, agent.used_edges, agent.unsatisfied_demands, agent.edges_free_capacity = samdl.recover_data_no_info(model,agent.edges,agent.demands)
        agent.profit_first_stage_partial_cooperation = model.objective_value
        agent.profit_first_stage_partial2_cooperation = - model.edges_costs.solution_value
    else:
        print("Problem has no solution")


    # print('Satisfied demands:', agent.satisfied_demands)
    # print('Used edges:', agent.used_edges)
    # print('Unsatisfied demand:', agent.unsatisfied_demands)
    # print('Edges with free capacity:', agent.edges_free_capacity, '\n')


# Now we pass to the partial cooperation model with leftovers (edges and demands) from each agent. 
# The agents will pay the proportional cost of the fraction of edge capacity they use respect to the total capacity of the edge
# For this, it will be necessary to keep track of who is the owner of each edge and commodity. 
# Conflics can happen if a commodity can be routed for multiple paths (always choose shortest 
# path as it will make the owner to pay less). Also if multiple commodities (but not all together) can
# be route in the same edge. This could be solved including some kind of extra payment for routing the
# commodity which doesn't fit. Also a commodity could be route at the same price for the customer, at different paths. How to choose?


# -------------------------------------------------------------
# --- MODEL WITH partial2 COOPERATION
# -------------------------------------------------------------

partial2_cooperation_planner = CentralizedSystem(agents,'partial2_cooperation')

agents_minimal_profit = []
for agent in agents:
    agents_minimal_profit.append(agent.profit_first_stage_partial_cooperation - agent.profit_first_stage_partial2_cooperation)

print(agents_minimal_profit)
# ----------------------------------------
# SOLVING THE PARTIAL COOPERATION MODEL
# ----------------------------------------

# print(partial2_cooperation_planner.demands)
# print(partial2_cooperation_planner.edges)



# Build the model
model = cpmdl.build_partial2_cooperation_model(N,V,partial2_cooperation_planner.edges,partial2_cooperation_planner.demands,agents_minimal_profit)
# model.print_information()

# Solve the model.
if model.solve():
     cpmdl.print_partial2_cooperation_solution(model)
     partial2_cooperation_planner.satisfied_demands = cpmdl.recover_data_partial2_cooperation(model, partial2_cooperation_planner.edges, partial2_cooperation_planner.demands)
else:
    print("Problem has no solution")

# ------ Recover how much each agent earn in the second stage
for d in partial2_cooperation_planner.satisfied_demands:
    agents[d[2]].profit_second_stage_partial2_cooperation += agents[d[2]].demands[(d[0],d[1])].units*agents[d[2]].demands[(d[0],d[1])].revenue
    for e in partial2_cooperation_planner.satisfied_demands[d]:
        if e[2] != d[2]:
            price =  agents[d[2]].demands[(d[0],d[1])].units * agents[e[2]].edges[(e[0],e[1])].cost/agents[e[2]].edges[(e[0],e[1])].capacity
            agents[e[2]].profit_second_stage_partial2_cooperation += price
            agents[d[2]].profit_second_stage_partial2_cooperation -= price


# ---------------------------------
# ---- PRINTING RESULTS FROM PARTIAL COOPERATION
# ---------------------------------


for agent in agents:
    print('Agent %s has earned %s in the first stage and %s in the second stage' % (agent.id,agent.profit_first_stage_partial2_cooperation,agent.profit_second_stage_partial2_cooperation))
    print('what makes a total of %s' % agent.total_profit_partial2_cooperation)