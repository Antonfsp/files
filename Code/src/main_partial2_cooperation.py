
# Python packages
import numpy as np # Basic functions, as random 
import matplotlib.pyplot as plt #For plotting

# Own scripts
import lib.classes as cl
import lib.models as mdls
import lib.functions as fn

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



N, V, commodities, edges = fn.read_data('instance_05')

# ------ Creating the agents objects ----------

agents_list = []
for i in range(N):
    agents_list.append(cl.Agent(i,edges[i],commodities[i]))


# ----------------------------------------------------------------------------
# Solving the model and display the result for each agent
# ----------------------------------------------------------------------------

for agent in agents_list:

    # Build the model
    model = mdls.build_single_agent_model(V,agent.edges,agent.commodities)
    # model.print_information()

    # Solve the model.
    if model.solve():
        # fn.print_no_info_solution(model)
        fn.recover_data_single_agent(model,agent)
        agent.payoff_no_cooperation = model.objective_value
        agent.payoff_cooperation = - model.edges_costs.solution_value
    else:
        print("Problem has no solution")


# -------------------------------------------------------------
# --- MODEL WITH PARTIAL2 COOPERATION
# -------------------------------------------------------------

central_planner = cl.CentralizedSystem(agents_list,'partial2_cooperation')

agents_minimal_profit = []
for agent in agents_list:
    agents_minimal_profit.append(agent.payoff_no_cooperation - agent.payoff_cooperation)

print(agents_minimal_profit)

# ----------------------------------------
# SOLVING THE PARTIAL2 COOPERATION MODEL
# ----------------------------------------

# Build the model
model = mdls.build_cooperation_model(V,central_planner.edges,central_planner.commodities,'partial2_cooperation',agents_minimal_profit)
# model.print_information()

# Solve the model.
if model.solve():
    fn.print_cooperation_solution(model)
    fn.recover_data_cooperation(model, central_planner,'partial2_cooperation')

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
