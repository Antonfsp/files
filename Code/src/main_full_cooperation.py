
# Own scripts
import lib.classes as cl
import lib.models as mdls
import lib.functions as fn

# -------------------------------------------------------------------------
#  INSTANCE DATA
# -------------------------------------------------------------------------

def full_cooperation(instance):

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


    # -------------------------------------------------------------
    # --- MODEL WITH full COOPERATION
    # -------------------------------------------------------------

    central_planner = cl.CentralizedSystem(agents_list,'full_cooperation')

    agents_minimal_profit = []
    for agent in agents_list:
        agents_minimal_profit.append(agent.payoff_no_cooperation)


    # ----------------------------------------
    # SOLVING THE PARTIAL COOPERATION MODEL
    # ----------------------------------------

    # Build the model
    model = mdls.build_cooperation_model(V,central_planner.edges,central_planner.commodities,'full_cooperation',agents_minimal_profit)
    # model.print_information()
    model.set_time_limit(5400)
    # # Solve the model.
    if model.solve():
        # model.print_solution()
        # fn.print_cooperation_solution(model)
        fn.recover_data_cooperation(model, central_planner,'full_cooperation')

        # ------ Recover how much each agent earn in the second stage
        for c in central_planner.served_commodities:
            agents_list[c[2]].payoff_cooperation += agents_list[c[2]].commodities[c].units*agents_list[c[2]].commodities[c].revenue
            for e in central_planner.commodities[c].route:
                if e[2] != c[2]:
                    price =  agents_list[c[2]].commodities[c].units * agents_list[e[2]].edges[e].cost/agents_list[e[2]].edges[e].original_capacity
                    agents_list[e[2]].payoff_cooperation += price
                    agents_list[c[2]].payoff_cooperation -= price

        for e in central_planner.active_edges:
            agents_list[e[2]].payoff_cooperation -= central_planner.edges[e].cost

        # ---------------------------------
        # ---- PRINTING RESULTS FROM PARTIAL COOPERATION
        # ---------------------------------

        # Need to revise how the profit of each stage is served. Attributes of AGENT class doesnt make sense
        coalition_payoff = 0
        for agent in agents_list:
            # print('Agent %s would have earned %s without cooperation, and would earn %s with cooperation' % (agent.id,agent.payoff_no_cooperation,agent.total_payoff('full_cooperation')))
            coalition_payoff += agent.total_payoff('full_cooperation')
        
        return coalition_payoff
    else:
        print("Problem has no solution")
        return -1

if __name__ == '__main__':
    instance = '5_high_0'
    full_cooperation(instance)