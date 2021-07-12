"""
Modeling the situation where multiple agents have to decide how to route their flow on a directed network,
 when a fixed cost of edges must be payed if the edges are used. Edges also have some capacity
 The agents have some demands between nodes
"""

from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX
import itertools as it
import classes # Neccesary to use edge namedtuple

# -------------------------------------------------------
# FUNCTIONS FOR CREATING THE SINGLE AGENT MODEL
# -------------------------------------------------------

def build_single_agent_model(V, E, demands, **kwargs):
    # Takes as input the nodes, V, the edges, E, q the capacity of the edges, r the revenue per unit of demand, c the cost of each edge and the demands between pairs of nodes
    mdl = Model('Single agent', **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,demand) for edge in E for demand in demands],name = 'f') # Binary variable indicating if a demand is routed in some edge
    mdl.u = mdl.binary_var_dict(E,name = 'e') # Binary variable which would indicate if an edge is used or not.

    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[1] == z) == mdl.sum(mdl.f[e,d] for e in E if e[0] == z) for d in demands for z in V if z!=d[0] and z!=d[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] == d[0]) <= 1 for d in demands) # Second constraint: Flow from source can only be one at max   (*)
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] == d[1]) == 0 for d in demands) # Third constraint: Commodities dont flow from terminal to other nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d]*demands[d].units for d in demands) <= (E[e].capacity * mdl.u[e]) for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] in S and e[1] in S) <= len(S) -1 for S in powerset(V,2) for d in demands) # Subtour elimination constraints

    # --- objective ---
    mdl.demands_revenues = mdl.sum(mdl.sum(mdl.f[e,d]*demands[d].units*demands[d].revenue for e in E if e[1] == d[1]) for d in demands)
    mdl.add_kpi(mdl.demands_revenues, "Demands revenue")
    mdl.edges_costs = mdl.sum(mdl.u[e]*E[e].cost for e in E)
    mdl.add_kpi(mdl.edges_costs, "Edges costs")
    mdl.profit = mdl.demands_revenues - mdl.edges_costs
    mdl.add_kpi(mdl.profit, 'Profit agent')
    mdl.free_capacity = mdl.sum(E[e].capacity - mdl.sum(mdl.f[e,d]*demands[d].units for d in demands) for e in E)
    mdl.add_kpi(mdl.free_capacity, 'Free capacity')
    mdl.maximize_static_lex([mdl.profit, mdl.free_capacity])
    # mdl.maximize(mdl.profit)

    return mdl

def print_no_info_solution(mdl):
    obj = mdl.objective_value
    mdl.report_kpis()
    print("* Single agent model solved with objective: {:g}".format(obj))
    print("* Total demands revenue=%g" % mdl.demands_revenues.solution_value)
    print("* Total edges costs=%g" % mdl.edges_costs.solution_value, '\n')


def recover_data_no_info(mdl,E,demands):
    active_edges = {e:0 for e in E if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
    edges_free_capacity = {}  
    active_flow= [flow_var for flow_var in [(edge,demand) for edge in E for demand in demands] if mdl.f[flow_var].solution_value>0.9]
    served_demands = {d[1]:None for d in active_flow} # Dictionary with the served demands as keys
    unserved_demands = {} # Dictionary to store unserved demands
  
    # We assign to each satisfied demand its proper flow from origin to terminal
    for d in served_demands:
        used_edges = [flow_var[0] for flow_var in active_flow if flow_var[1] == d]
        prev = d[0]
        path = []
        while(prev != d[1]):
            for e in used_edges:
                if e[0] == prev:
                    path.append(e)
                    used_edges.remove(e)
                    prev = e[1]
        served_demands[d] = path

    # We assign to each edge, its used capacity
    for d in served_demands:
        for e in served_demands[d]:
            active_edges[e] += demands[d].units

    # We get dictionary of demands of the agent which are not served (and are different to 0)
    for d in demands:
        if d not in served_demands and demands[d].units != 0:
            unserved_demands[d] = demands[d]

    # Dictionary with active edges with free (not used) capacity
    for e in active_edges:
        if active_edges[e] < E[e].capacity:
            edges_free_capacity[e] = classes.Edge(E[e].capacity - active_edges[e], E[e].cost,E[e].original_capacity)

    return served_demands, active_edges, unserved_demands, edges_free_capacity



# -----------------------------------
# Recipe to get subsets of a set
# -----------------------------------

def powerset(iterable,min_subset):
    "powerset([1,2,3],2) --> (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(min_subset, len(s)+1))
