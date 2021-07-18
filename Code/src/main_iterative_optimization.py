''' 
The idea is to find a way in which agent can interact with each other, still having full control about their
decision variables, and sharing as little information as possible with the other agents, but still interact
with them and find an agreement about how to cooperatively solve the multicommodity flow problem they are facing

In this script we will only consider the case with 2 agents, and later we will try to extend the model to more players
'''
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
# r = 2 # Revenue of satisfying each unit of demand


N, V, commodities, edges = fn.read_data('instance_05')


# ------ Creating the agents objects ----------

agents_list = []
for i in range(N-1,-1,-1):
    agents_list.append(cl.Agent(i,edges[i],commodities[i]))


# ----- Creating the information platform ------

info_platform = cl.informationPlatform(agents_list)


# ----------------------------------------------------------------------------
# First, Agent 1 will solve his own optimization problem
# ----------------------------------------------------------------------------

iteration = 0
while(iteration<6):

    iteration += 1

    print("************")
    print('Iteration %s' %(iteration))
    print("************")
    print()


    print('Agent %d' %(0))
    print("----------------------")

    # We have to re-start the info each time an agent reoptimizes
    agents_list[0].restore_commodities_info()
    agents_list[0].restore_edges_info()

    info_platform.restore_info(agents_list[0])

    # Build the model
    model = mdls.build_iterative_model(V,agents_list[0],info_platform)

    # Solve the model.
    if model.solve():
        #fn.print_iterative_solution(model)
        fn.recover_data_iterative(model,agents_list[0],info_platform)
        agents_list[0].history_solutions.append(cl.Solution(agents_list[0],model))
        agents_list[0].history_solutions[-1].print_data()
    else:
        print("Problem has no solution")

    
    print("----------------------")
    print('Agent %d' %(1))
    print("----------------------")

    # We have to re-start the info each time an agent reoptimizes
    agents_list[1].restore_commodities_info()
    agents_list[1].restore_edges_info()

    info_platform.restore_info(agents_list[1])

    # Build the model
    model = mdls.build_iterative_model(V,agents_list[1],info_platform)

    # Solve the model.
    if model.solve():
        #fn.print_iterative_solution(model)
        fn.recover_data_iterative(model,agents_list[1],info_platform)
        agents_list[1].history_solutions.append(cl.Solution(agents_list[1],model))
        agents_list[1].history_solutions[-1].print_data()
    else:
        print("Problem has no solution")


if(agents_list[0].history_solutions[-1].equal_to(agents_list[0].history_solutions[-2]) and agents_list[1].history_solutions[-1].equal_to(agents_list[1].history_solutions[-2])):
    print('There is an equilibrium!')
else:
    print('No equilibrium found in %d iterations' %(iteration))
