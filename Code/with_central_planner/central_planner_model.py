from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX
import itertools as it


def build_cooperation_model(V, E, commodities, type_cooperation, agents_minimal_profit = None,**kwargs):
    # Takes as input the the nodes, V, the edges, E, that are tuples (v,w,i) and have some capacity and a cost, the commodities between pairs of nodes (which also are tuples (v,w,i) where i is is owner)
    # the type of cooperation want to be used, and which is the minimal payoff each agent should obtain.
    # In the case type_cooperation if partial1_cooperation, the agents_minimal_rofit doesnt need to be specified

    mdl = Model(type_cooperation, **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,commodity) for edge in E for commodity in commodities],name = 'f') # Binary variable indicating if a commodity is routed in some edge
    if type_cooperation == 'full_cooperation':
        mdl.u = mdl.binary_var_dict(E,name = 'u') # Binary variable which would indicate if an edge is used or not.


    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[1] == z) == mdl.sum(mdl.f[e,c] for e in E if e[0]==z) for c in commodities for z in V if z!=c[0] and z!=c[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[0] == c[0]) <= 1 for c in commodities) # Second constraint: Flow from source can only be one at max   (*)
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[0] == c[1]) == 0 for c in commodities) # Third constraint: Commodities dont flow from terminal to other nodes
    
    if type_cooperation == 'partial1_cooperation':
        mdl.add_constraints(mdl.sum(mdl.f[e,c] * commodities[c].units for c in commodities) <= E[e].free_capacity for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    elif type_cooperation == 'partial2_cooperation':
        mdl.add_constraints(mdl.sum(mdl.f[e,c] * commodities[c].units for c in commodities) <= E[e].original_capacity for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    elif type_cooperation == 'full_cooperation':
        mdl.add_constraints(mdl.sum(mdl.f[e,c]*commodities[c].units for c in commodities) <= (E[e].original_capacity * mdl.u[e]) for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[0] in S and e[1] in S) <= len(S) -1 for S in powerset(V,2) for c in commodities) # Subtour elimination constraints

    if type_cooperation == 'partial2_cooperation':
        mdl.add_constraints(mdl.sum(mdl.sum(mdl.f[e,c] * commodities[c].units * commodities[c].revenue for e in E if e[0] == c[0]) - mdl.sum(mdl.f[e,c] * commodities[c].units * (E[e].cost/E[e].original_capacity) for e in E if e[2] != i) for c in commodities if c[2] == i) + mdl.sum(mdl.sum(mdl.f[e,c]*commodities[c].units*(E[e].cost/E[e].original_capacity) for e in E if e[2] == i) for c in commodities if c[2]!= i) >= agents_minimal_profit[i] for i in range(len(agents_minimal_profit))) # Every agent has to earn at least as much as he will win without cooperation
    elif type_cooperation == 'full_cooperation':
        mdl.add_constraints(mdl.sum(mdl.sum(mdl.f[e,c] * commodities[c].units * commodities[c].revenue for e in E if e[0] == c[0]) - mdl.sum(mdl.f[e,c] * commodities[c].units * (E[e].cost/E[e].original_capacity) for e in E if e[2] != i) for c in commodities if c[2] == i) + mdl.sum(mdl.sum(mdl.f[e,c]*commodities[c].units*(E[e].cost/E[e].original_capacity) for e in E if e[2] == i) for c in commodities if c[2]!= i) - mdl.sum(mdl.u[e]*E[e].cost for e in E if e[2] == i) >= agents_minimal_profit[i] for i in range(len(agents_minimal_profit))) # Every agent has to earn at least as much as he will win without cooperation

    # --- objective ---
    if type_cooperation == 'partial1_cooperation' or type_cooperation == 'partial2_cooperation':
        mdl.revenues = mdl.sum(mdl.sum(mdl.f[e,c] * commodities[c].units * commodities[c].revenue for e in E if e[1] == c[1]) - mdl.sum(mdl.f[e,c] * commodities[c].units * E[e].cost/E[e].original_capacity for e in E if e[2]!=c[2]) for c in commodities)
        mdl.add_kpi(mdl.revenues, "commodities revenue")
        mdl.maximize(mdl.revenues)
    elif type_cooperation == 'full_cooperation':
        mdl.commodities_revenues = mdl.sum(mdl.sum(mdl.f[e,c]*commodities[c].units*commodities[c].revenue for e in E if e[1] == c[1]) for c in commodities)
        mdl.add_kpi(mdl.commodities_revenues, "commodities revenue")
        mdl.edges_costs = mdl.sum(mdl.u[e]*E[e].cost for e in E)
        mdl.add_kpi(mdl.edges_costs, "Edges costs")
        mdl.profit = mdl.commodities_revenues - mdl.edges_costs
        mdl.add_kpi(mdl.profit, 'Profit agent')
        mdl.maximize(mdl.profit)

    return mdl


def print_cooperation_solution(mdl):
    obj = mdl.objective_value
    print("* Cooperation solved with objective: {:g}".format(obj))

def recover_data_cooperation(mdl,central_planner,type_cooperation):
    
    active_flow= [flow_var for flow_var in [(edge,commodity) for edge in central_planner.edges for commodity in central_planner.commodities] if mdl.f[flow_var].solution_value>0.9]
    central_planner.served_commodities = {a[1] for a in active_flow} # Dictionary with the satisfied commodities as keys
  
    # We assign to each satisfied commodity its proper flow from origin to terminal
    for c in central_planner.served_commodities:
        central_planner.commodities[c].route = {flow_var[0] for flow_var in active_flow if flow_var[1] == c}
        # If the order is necessary. I dont think so
        # used_edges = [flow_var[0] for flow_var in active_flow if flow_var[1] == c]
        # prev = c[0]
        # path = []
        # while(prev != c[1]):
        #     for e in used_edges:
        #         if e[0] == prev:
        #             path.append(e)
        #             used_edges.remove(e)
        #             prev = e[1]
        # served_commodities[c] = path

    
    if type_cooperation == 'full_cooperation':
        central_planner.active_edges = {e for e in central_planner.edges if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
        # We assign to each edge, its used capacity
        for c in central_planner.served_commodities:
            for e in central_planner.commodities[c].route:
                central_planner.edges[e].free_capacity -= central_planner.commodities[c].units


# -----------------------------------
# Recipe to get subsets of a set
# -----------------------------------

def powerset(iterable,min_subset):
    "powerset([1,2,3],2) --> (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(min_subset, len(s)+1))

