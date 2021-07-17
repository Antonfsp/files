from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX
import itertools as it


# -----------------------------------------------------------------------------------
# ------------------ MODELS FOR MECHANISM WITH CENTRAL PLANNER ----------------------
# -----------------------------------------------------------------------------------

# ---------------------------
# MODEL SINGLE AGENT
# ---------------------------

def build_single_agent_model(V, E, commodities, **kwargs):
    # Takes as input the nodes, V, the edges, E, q the capacity of the edges, r the revenue per unit of commoditie, c the cost of each edge and the commodities between pairs of nodes
    mdl = Model('Single agent', **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,commodity) for edge in E for commodity in commodities],name = 'f') # Binary variable indicating if a commodity is routed in some edge
    mdl.u = mdl.binary_var_dict(E,name = 'u') # Binary variable which would indicate if an edge is used or not.

    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[1] == z) == mdl.sum(mdl.f[e,c] for e in E if e[0] == z) for c in commodities for z in V if z!=c[0] and z!=c[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[0] == c[0]) <= 1 for c in commodities) # Second constraint: Flow from source can only be one at max   (*)
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[0] == c[1]) == 0 for c in commodities) # Third constraint: Commodities dont flow from terminal to other nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,c]*commodities[c].units for c in commodities) <= (E[e].original_capacity * mdl.u[e]) for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in E if e[0] in S and e[1] in S) <= len(S) -1 for S in powerset(V,2) for c in commodities) # Subtour elimination constraints

    # --- objective ---
    mdl.commodities_revenues = mdl.sum(mdl.sum(mdl.f[e,c]*commodities[c].units*commodities[c].revenue for e in E if e[1] == c[1]) for c in commodities)
    mdl.add_kpi(mdl.commodities_revenues, "Demands revenue")
    mdl.edges_costs = mdl.sum(mdl.u[e]*E[e].cost for e in E)
    mdl.add_kpi(mdl.edges_costs, "Edges costs")
    mdl.profit = mdl.commodities_revenues - mdl.edges_costs
    mdl.add_kpi(mdl.profit, 'Profit agent')
    mdl.free_capacity = mdl.sum(E[e].original_capacity - mdl.sum(mdl.f[e,c]*commodities[c].units for c in commodities) for e in E)
    mdl.add_kpi(mdl.free_capacity, 'Free capacity')
    mdl.maximize_static_lex([mdl.profit, mdl.free_capacity])
    # mdl.maximize(mdl.profit)

    return mdl


# ---------------------------
#  MODEL COOPERATION
# ---------------------------

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


# -----------------------------------------------------------------------------------
# ------------------------- MODEL FOR ITERATIVE MECHANISM ---------------------------
# -----------------------------------------------------------------------------------

def build_iterative_model(V, agent, info_platform,  **kwargs):
    
    # ORGANIZING INPUT DATA
    if agent.id == 0:
        other_agent_id = 1
    else:
        other_agent_id = 0
    E = agent.edges
    commodities = agent.commodities
    L = info_platform.shared_edges[other_agent_id]
    conditioned_edges = info_platform.demanded_edges[other_agent_id]
    edges_condition_relations = info_platform.demanded_edges_conditions[other_agent_id]
    
    # Takes as input the nodes, V, the edges, E, q the capacity of the edges, r the revenue per unit of commoditie, c the cost of each edge and the commodities between pairs of nodes
    mdl = Model('Iterative model', **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,commodity) for edge in {**E,**L} for commodity in commodities],name = 'f') # Binary variable indicating if a commodity is routed in some edge
    mdl.u = mdl.binary_var_dict(E, name = 'u') # Binary variable which would indicate if an edge is used or not.
    if conditioned_edges:
        mdl.b = mdl.binary_var_dict(conditioned_edges, name = 'b')

    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in {**E,**L} if e[1] == z) == mdl.sum(mdl.f[e,c] for e in {**E,**L} if e[0] == z) for c in commodities for z in V if z!=c[0] and z!=c[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in {**E,**L} if e[0] == c[0]) <= 1 for c in commodities) # Second constraint: Flow from source can only be one at max   (*)
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in {**E,**L} if e[0] == c[1]) == 0 for c in commodities) # Third constraint: Commodities dont flow from terminal to other nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,c]*commodities[c].units for c in commodities) <= (E[e].original_capacity * mdl.u[e]) for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    
    if conditioned_edges: # If b_e is equal to 1, the, the current agent cannt route more flow through the edge e than its original capacity - the capacity demanded by the other agent, for e an edge used for the other agent
            mdl.add_indicator_constraints(mdl.indicator_constraint(mdl.b[e],mdl.sum(mdl.f[e,c]*commodities[c].units for c in commodities) <= E[e].original_capacity - conditioned_edges[e]) for e in conditioned_edges) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity)  # Fourth constraint: The sum of commodities on an edge can't exceed its capacity

    if L:
        mdl.add_constraints(mdl.sum(mdl.f[e,c]*commodities[c].units for c in commodities) <= L[e].free_capacity for e in L) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    
    mdl.add_constraints(mdl.sum(mdl.f[e,c] for e in {**E,**L} if e[0] in S and e[1] in S) <= len(S) -1 for S in powerset(V,2) for c in commodities) # Subtour elimination constraints

    # --- objective ---
    mdl.commodities_revenues = mdl.sum(mdl.sum(mdl.f[e,c]*commodities[c].units*commodities[c].revenue for e in {**E,**L} if e[1] == c[1]) for c in commodities)
    mdl.add_kpi(mdl.commodities_revenues, "Demands revenue")
    mdl.edges_costs = mdl.sum(mdl.u[e]*E[e].cost for e in E)
    mdl.add_kpi(mdl.edges_costs, "Edges costs")
    
    mdl.out_payments = mdl.sum(mdl.sum(mdl.f[e,c]*commodities[c].units*L[e].cost_per_unit for e in L)for c in commodities)
    mdl.add_kpi(mdl.out_payments, "Payments to do to other agents")
    mdl.in_payments = mdl.sum((mdl.sum(mdl.b[e]for e in condition.edges) == len(condition.edges))*condition.price for condition in edges_condition_relations)
    mdl.add_kpi(mdl.in_payments, "Payments to receive from other agents")

    mdl.profit = mdl.commodities_revenues - mdl.edges_costs - mdl.out_payments + mdl.in_payments
    mdl.add_kpi(mdl.profit, 'Profit agent')
    # mdl.free_capacity = mdl.sum(E[e].original_capacity - mdl.sum(mdl.f[e,c]*commodities[c].units for c in commodities) for e in E)
    # mdl.add_kpi(mdl.free_capacity, 'Free capacity')
    # mdl.maximize_static_lex([mdl.profit, mdl.free_capacity])
    mdl.maximize(mdl.profit)

    return mdl




# -----------------------------------
# Recipe to get subsets of a set
# -----------------------------------

def powerset(iterable,min_subset):
    "powerset([1,2,3],2) --> (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(min_subset, len(s)+1))