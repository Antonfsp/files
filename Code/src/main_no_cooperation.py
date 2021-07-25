# Own scripts
import lib.classes as cl
import lib.models as mdls
import lib.functions as fn

# -------------------------------------------------------------------------
#  INSTANCE DATA
# -------------------------------------------------------------------------

def no_cooperation(instance):

    N, V, commodities, edges = fn.read_data(instance)

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
            # fn.print_single_agent_solution(model)
            fn.recover_data_single_agent(model,agent)
            agent.payoff_no_cooperation = model.objective_value
        else:
            print("Problem has no solution")

if __name__ == '__main__':
    instance = '2_low_0'
    no_cooperation(instance)
