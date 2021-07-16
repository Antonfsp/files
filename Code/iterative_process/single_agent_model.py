"""
Modeling the situation where multiple agents have to decide how to route their flow on a directed network,
 when a fixed cost of edges must be payed if the edges are used. Edges also have some capacity
 The agents have some commodities between nodes
"""

from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX
import itertools as it

# -------------------------------------------------------
# FUNCTIONS FOR CREATING THE SINGLE AGENT MODEL
# -------------------------------------------------------

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

def print_single_agent_solution(mdl):
    obj = mdl.objective_value
    mdl.report_kpis()
    print("* Single agent model solved with objective: {:g}".format(obj))
    print("* Total commodities revenue=%g" % mdl.commodities_revenues.solution_value)
    print("* Total edges costs=%g" % mdl.edges_costs.solution_value, '\n')


def recover_data_single_agent(mdl,agent):
    agent.active_edges = {e for e in agent.edges if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
    active_flow= [flow_var for flow_var in [(edge,commodity) for edge in agent.edges for commodity in agent.commodities] if mdl.f[flow_var].solution_value>0.9]
    
    agent.served_commodities = {a[1] for a in active_flow} # Dictionary with the served commodities as keys
  
    # We assign to each satisfied commodity its proper flow from origin to terminal
    for c in agent.served_commodities:
        agent.commodities[c].route = {flow_var[0] for flow_var in active_flow if flow_var[1] == c}
        
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

    # We update the free capacity of the edges
    for c in agent.served_commodities:
        for e in agent.commodities[c].route:
            agent.edges[e].free_capacity -= agent.commodities[c].units

    # We get dictionary of commodities of the agent which are not served (and are different to 0)
    agent.unserved_commodities = {c for c in agent.commodities if c not in agent.served_commodities and agent.commodities[c].units != 0}

    # Dictionary with active edges with free (not used) capacity
    agent.edges_with_capacity = {e for e in agent.active_edges if agent.edges[e].free_capacity > 0}


# -----------------------------------
# Recipe to get subsets of a set
# -----------------------------------

def powerset(iterable,min_subset):
    "powerset([1,2,3],2) --> (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(min_subset, len(s)+1))
