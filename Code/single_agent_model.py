"""
Modeling the situation where multiple agents have to decide how to route their flow on a directed network,
 when a fixed cost of edges must be payed if the edges are used. Edges also have some capacity
 The agents have some demands between nodes
"""

from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX

# -------------------------------------------------------
# FUNCTIONS FOR CREATING THE NO INFORMATION MODEL
# -------------------------------------------------------

def build_no_info_problem(V, E, q, c, r, demands, **kwargs):
    # Takes as input the nodes, V, the edges, E, q the capacity of the edges, r the revenue per unit of demand, c the cost of each edge and the demands between pairs of nodes
    mdl = Model('Single agent no info', **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,demand) for edge in E for demand in demands],name = 'f') # Binary variable indicating if a demand is routed in some edge
    mdl.u = mdl.binary_var_dict(E,name = 'e') # Binary variable which would indicate if an edge is used or not.

    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[(v,z),d] for v in V if v!=z) == mdl.sum(mdl.f[(z,w),d] for w in V if w!=z) for d in demands for z in V if z!=d[0] and z!=d[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[(d[0],v),d] for v in V if v !=d[0]) <= 1 for d in demands) # Second constraint: Flow from source can only be one at max   (*)
    # mdl.add_constraints(mdl.sum(mdl.f[(z,v),d] for v in V if v !=z) <= 1 for z in V if z!=d[1] for d in demands) # Second'' constraint: A commodity can leave a node only once at max (similar to (*) but avoid subtours. No difference in objective value, but seems more reasonable)
    mdl.add_constraints(mdl.sum(mdl.f[(d[1],v),d] for v in V if v !=d[1]) == 0 for d in demands) # Third constraint: Commodities dont flow from terminal to other nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d]*demands[d] for d in demands) <= (q * mdl.u[e]) for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity

    # --- objective ---
    mdl.demands_revenues = mdl.sum(mdl.sum(mdl.f[((v,d[1]),d)]*demands[d]*r for v in V if v != d[1]) for d in demands)
    mdl.add_kpi(mdl.demands_revenues, "Demands revenue")
    mdl.edges_costs = mdl.sum(mdl.u[e]*c for e in E)
    mdl.add_kpi(mdl.edges_costs, "Edges costs")
    mdl.profit = mdl.demands_revenues - mdl.edges_costs
    mdl.add_kpi(mdl.profit, 'Profit agent')
    mdl.used_capacity = mdl.sum(mdl.sum(mdl.f[e,d]*demands[d] for d in demands) for e in E)
    mdl.add_kpi(mdl.used_capacity, 'Used capacity')
    mdl.maximize_static_lex([mdl.profit, - mdl.used_capacity])


    return mdl

def print_no_info_solution(mdl):
    obj = mdl.objective_value
    mdl.report_kpis()
    print("* Single agent model solved with objective: {:g}".format(obj))
    print("* Total demands revenue=%g" % mdl.demands_revenues.solution_value)
    print("* Total edges costs=%g" % mdl.edges_costs.solution_value, '\n')


def recover_data_no_info(mdl,E,demands,q):
    active_edges = {e:0 for e in E if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
    edges_free_capacity = {}  
    active_flow= [flow_var for flow_var in [(edge,demand) for edge in E for demand in demands] if mdl.f[flow_var].solution_value>0.9]
    served_demands = {d[1]:None for d in active_flow} # Dictionary with the satisfied demands as keys
    unserved_demands = {}
  
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
            active_edges[e] += demands[d]

    # We get dictionary of demands of the agent which are not served (and are different to 0)
    for d in demands:
        if d not in served_demands and demands[d] != 0:
            unserved_demands[d] = demands[d]

    for e in active_edges:
        if active_edges[e] < q:
            edges_free_capacity[e] = q - active_edges[e]

    return served_demands, active_edges, unserved_demands, edges_free_capacity