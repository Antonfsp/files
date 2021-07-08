from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX
import itertools as it


# -------------------------------------------------------
# FUNCTIONS FOR CREATING THE FULL COOPERATION MODEL
# -------------------------------------------------------

def build_full_cooperation_problem(N,V, E, q, c, r, demands, **kwargs):
    # Takes as input the number of agents, N, the nodes, V, the edges, E, that are tuples (v,w,i) and have some capacity, r the revenue per unit of demand, c the cost of each edge and the demands between pairs of nodes (which also are tuples (v,w,i) where i is is owner)
    mdl = Model('Full cooperation', **kwargs)

    # --- decision variables ---
    mdl.f = mdl.binary_var_dict([(edge,demand) for edge in E for demand in demands],name = 'f') # Binary variable indicating if a demand is routed in some edge

    # --- constraints ---
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[1] == z) == mdl.sum(mdl.f[e,d] for e in E if e[0]==z) for d in demands for z in V if z!=d[0] and z!=d[1]) # First constraints: Flow over transit nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] == d[0]) <= 1 for d in demands) # Second constraint: Flow from source can only be one at max   (*)
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] == d[1]) == 0 for d in demands) # Third constraint: Commodities dont flow from terminal to other nodes
    mdl.add_constraints(mdl.sum(mdl.f[e,d] * demands[d] for d in demands) <= E[e] for e in E) # Fourth constraint: The sum of commodities on an edge can't exceed its capacity
    mdl.add_constraints(mdl.sum(mdl.f[e,d] for e in E if e[0] in S and e[1] in S) <= len(S) -1 for S in powerset(V,2) for d in demands) # Subtour elimination constraints

    # --- objective ---
    mdl.revenues = mdl.sum(mdl.sum(mdl.f[e,d] * r for e in E if e[1] == d[1]) - mdl.sum(mdl.f[e,d] * c/q for e in E if e[2]!=d[2]) for d in demands)
    mdl.add_kpi(mdl.revenues, "Demands revenue")
    mdl.maximize(mdl.revenues)

    return mdl

def print_full_cooperation_solution(mdl):
    obj = mdl.objective_value
    print("* Full cooperation solved with objective: {:g}".format(obj))


def recover_data_full_cooperation(mdl,E,demands,q):
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
            E[e] -= demands[d]



    return served_demands, unserved_demands


# -----------------------------------
# Recipe to get subsets of a set
# -----------------------------------

def powerset(iterable,min_subset):
    "powerset([1,2,3],2) --> (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return it.chain.from_iterable(it.combinations(s, r) for r in range(min_subset, len(s)+1))

