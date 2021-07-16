"""
Model for the iterative optimization mechasnim
"""

from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX
import itertools as it
import classes
import copy

# -------------------------------------------------------
# FUNCTIONS FOR CREATING THE SINGLE AGENT MODEL
# -------------------------------------------------------

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



# -------------------
# ----- FUNCTION FOR PRINTING SOLUTION
# -------------------

def print_iterative_solution(mdl):
    mdl.report_kpis()
    print()


# -------------------
# ----- FUNCTION FOR RECOVERING THE DATA FROM THE SOLUTION, BOTH FOR THE AGENT AND THE INFO PLATFORM


def recover_data_iterative(mdl,agent,info_platform):
    
    if agent.id == 0:
        other_agent_id = 1
    else:
        other_agent_id = 0

    agent.active_edges = {e for e in agent.edges if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
    
    active_flow = [flow_var for flow_var in [(edge,commodity) for edge in {**agent.edges,**info_platform.shared_edges[other_agent_id]} for commodity in agent.commodities] if mdl.f[flow_var].solution_value>0.9]
    
    agent.served_commodities = {a[1] for a in active_flow} # Dictionary with the served commodities as keys
  
    # We assign to each satisfied commodity its proper flow from origin to terminal
    for c in agent.served_commodities:
        agent.commodities[c].route = {flow_var[0] for flow_var in active_flow if flow_var[1] == c}
        
        # Also take which edges shared for the other agent that demands requires, and how much it would generate
        temp_list = [e for e in agent.commodities[c].route if e[2]!=agent.id]
        temp_value = sum(info_platform.shared_edges[other_agent_id][e].cost_per_unit*agent.commodities[c].units for e in temp_list)
        if temp_list:
            info_platform.demanded_edges_conditions[agent.id].append(classes.EdgesConditions(temp_list,temp_value))

        # This is if we need the path in order. (I think is not the case)
        # prev = c[0]
        # path = []
        # while(prev != c[1]):
        #     for e in used_edges:
        #         if e[0] == prev:
        #             path.append(e)
        #             used_edges.remove(e)
        #             prev = e[1]
        # agent.commodities[c].route = path


    # We get which edges from the other agent the current agent uses
    info_platform.demanded_edges[agent.id] = {flow_var[0]:0 for flow_var in active_flow if flow_var[0][2] != agent.id}


    # We update the free capacity of the edges
    for c in agent.served_commodities:
        for e in agent.commodities[c].route:
            if e[2] == agent.id: # We have to update the capacity of the edge in differenc dictionaries depending who is the owner
                agent.edges[e].free_capacity -= agent.commodities[c].units
            else:
                info_platform.demanded_edges[agent.id][e] += agent.commodities[c].units

    # We get dictionary of commodities of the agent which are not served (and are different to 0)
    agent.unserved_commodities = {c for c in agent.commodities if c not in agent.served_commodities and agent.commodities[c].units != 0}

    # Dictionary with active edges with free (not used) capacity
    agent.edges_with_capacity = {e for e in agent.active_edges if agent.edges[e].free_capacity > 0}

    # Finally, the agent share in the platform which edges with free capacity he share
    info_platform.shared_edges[agent.id] = agent.share_edges()


# -----------------------------------
# Recipe to get subsets of a set
# -----------------------------------

def powerset(iterable,min_subset):
    "powerset([1,2,3],2) --> (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(min_subset, len(s)+1))
