''' 
The idea is to find a way in which agent can interact with each other, still having full control about their
decision variables, and sharing as little information as possible with the other agents, but still interact
with them and find an agreement about how to cooperatively solve the multicommodity flow problem they are facing

In this script we will only consider the case with 2 agents, and later we will try to extend the model to more players
'''

# Own scripts
from numpy import NaN
import lib.classes as cl
import lib.models as mdls
import lib.functions as fn
import time

# -------------------------------------------------------------------------
#  INSTANCE DATA
# -------------------------------------------------------------------------


def iterative_cooperation(instance,order=[0,1]):
    init_time = time.time()
    max_time = 5400
    N, V, commodities, edges = fn.read_data(instance)

    max_iter = 100

    # ------ Creating the agents objects ----------

    agents_list = []
    for i in range(N-1,-1,-1):
        agents_list.append(cl.Agent(i,edges[i],commodities[i]))


    # ----- Creating the information platform ------

    info_platform = cl.informationPlatform(agents_list)


    # ----------------------------------------------------------------------------
    # First, Agent 1 will solve his own optimization problem
    # ----------------------------------------------------------------------------

    first_agent = order[0]
    second_agent = order[1]

    iteration = 0
    while(iteration<max_iter):

        iteration += 1
        # print(iteration)
        # print("************")
        # print('Iteration %s' %(iteration))
        # print("************")
        # print()


        # print('Agent %d' %(first_agent))
        # print("----------------------")

        # We have to re-start the info each time an agent reoptimizes
        agents_list[first_agent].restore_commodities_info()
        agents_list[first_agent].restore_edges_info()

        info_platform.restore_info(agents_list[first_agent])

        # Build the model
        model = mdls.build_iterative_model(V,agents_list[first_agent],info_platform)
        model.set_time_limit(max_time-(time.time()-init_time))
        # Solve the model.
        if model.solve():
            #fn.print_iterative_solution(model)
            fn.recover_data_iterative(model,agents_list[first_agent],info_platform)
            agents_list[first_agent].history_solutions.append(cl.Solution(agents_list[first_agent],model))
            #agents_list[first_agent].history_solutions[-1].print_data()
        else:
            print("Problem has no solution")
            return -1

        
        # print("----------------------")
        # print('Agent %d' %(second_agent))
        # print("----------------------")

        # We have to re-start the info each time an agent reoptimizes
        agents_list[second_agent].restore_commodities_info()
        agents_list[second_agent].restore_edges_info()

        info_platform.restore_info(agents_list[second_agent])

        # Build the model
        model = mdls.build_iterative_model(V,agents_list[second_agent],info_platform)
        model.set_time_limit(max_time-(time.time()-init_time))
        # Solve the model.
        if model.solve():
            #fn.print_iterative_solution(model)
            fn.recover_data_iterative(model,agents_list[second_agent],info_platform)
            agents_list[second_agent].history_solutions.append(cl.Solution(agents_list[second_agent],model))
            #agents_list[second_agent].history_solutions[-1].print_data()
        else:
            print("Problem has no solution")
            return -1

        if(iteration >= 2 and agents_list[first_agent].history_solutions[-1].equal_to(agents_list[first_agent].history_solutions[-2]) and agents_list[second_agent].history_solutions[-1].equal_to(agents_list[second_agent].history_solutions[-2])):
            # print('Equilibrium was found in %d iterations!' %(iteration))
            coalition_payoff = agents_list[first_agent].history_solutions[-1].payoff + agents_list[second_agent].history_solutions[-1].payoff
            break
    else:
        print('No equilibrium found in %d iterations' %(iteration))
        coalition_payoff = -1
    
    
    return coalition_payoff,iteration
    #print(coalition_payoff,iteration)


if __name__ == '__main__':
    instance = '2_high_1'
    iterative_cooperation(instance,[1,0])
    iterative_cooperation(instance)
