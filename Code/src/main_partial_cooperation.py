# Own scripts
import lib.classes as cl
import lib.models as mdls
import lib.functions as fn

# -------------------------------------------------------------------------
#  INSTANCE DATA
# -------------------------------------------------------------------------

def partial_cooperation(instance):
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
            # fn.print_no_info_solution(model)
            fn.recover_data_single_agent(model,agent)
            agent.payoff_no_cooperation = model.objective_value
            agent.payoff_cooperation = - model.edges_costs.solution_value
        else:
            print("Problem has no solution")


    # -------------------------------------------------------------
    # --- MODEL WITH PARTIAL2 COOPERATION
    # -------------------------------------------------------------

    central_planner = cl.CentralizedSystem(agents_list,'partial_cooperation')

    agents_minimal_profit = []
    for agent in agents_list:
        agents_minimal_profit.append(agent.payoff_no_cooperation - agent.payoff_cooperation)

    # ----------------------------------------
    # SOLVING THE PARTIAL2 COOPERATION MODEL
    # ----------------------------------------

    # Build the model
    model = mdls.build_cooperation_model(V,central_planner.edges,central_planner.commodities,'partial_cooperation',agents_minimal_profit)
    # model.print_information()

    # Solve the model.
    if model.solve():
        # fn.print_cooperation_solution(model)
        fn.recover_data_cooperation(model, central_planner,'partial_cooperation')

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

        coalition_payoff = 0
        for agent in agents_list:
        #    print('Agent %s would have earned %s without cooperation and earns %s cooperating' % (agent.id,agent.payoff_no_cooperation,agent.total_payoff('partial_cooperation')))
            coalition_payoff += agent.total_payoff('partial_cooperation')
        return coalition_payoff
    else:
        print("Problem has no solution")


if __name__ == '__main__':
    instance = '2_low_0'
    partial_cooperation(instance)
