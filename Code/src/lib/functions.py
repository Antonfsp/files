import lib.classes as cl
import os # Necessary to open the file from any working directory


# Function to read the data from an instance
def read_data(instance):
    file = open(os.path.join(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir,'instances',instance)),'r')
    lines_list = file.readlines()
    N, V = (int(x) for x in lines_list[0].split())
    V = {i for i in range(V)}
    commodities = {i:{} for i in range(N)}
    edges = {i:{} for i in range(N)}

    for line in lines_list[1:]:
        if line.rstrip() == 'Agent':
            prev = 'Agent'
        elif line.rstrip() == 'Commodities':
            prev = 'Commodities'
        elif line.rstrip() == 'Edges':
            prev = 'Edges'
        else:
            if prev == 'Agent':
                owner = int(line)
            if prev == 'Commodities':
                temp = [int(x) for x in line.split()]
                commodities[owner][(temp[0],temp[1],temp[2])] = cl.Commodity(temp[0],temp[1],temp[2],temp[3],temp[4])
            if prev == 'Edges':
                temp = [int(x) for x in line.split()]
                edges[owner][(temp[0],temp[1],temp[2])] = cl.Edge(temp[0],temp[1],temp[2],temp[3],temp[4])
    
    return N, V, commodities, edges



# -----------------------------
# Functions for print solutions from models
#------------------------------

# Single agent
def print_single_agent_solution(mdl):
    obj = mdl.objective_value
    mdl.report_kpis()
    print("* Single agent model solved with objective: {:g}".format(obj))
    print("* Total commodities revenue=%g" % mdl.commodities_revenues.solution_value)
    print("* Total edges costs=%g" % mdl.edges_costs.solution_value, '\n')


# Cooperation
def print_cooperation_solution(mdl):
    obj = mdl.objective_value
    print("* Cooperation solved with objective: {:g}".format(obj))


# Iterative
def print_iterative_solution(mdl):
    mdl.report_kpis()
    print()




# ----------------------------
# Function for recover data from solved model
# ----------------------------

# Single agent model
def recover_data_single_agent(mdl,agent):
    agent.active_edges = {e for e in agent.edges if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
    active_flow= [flow_var for flow_var in [(edge,commodity) for edge in agent.edges for commodity in agent.commodities] if mdl.f[flow_var].solution_value>0.9]
    
    agent.served_commodities = {a[1] for a in active_flow} # Dictionary with the served commodities as keys
  
    # We assign to each satisfied commodity its proper flow from origin to terminal
    for c in agent.served_commodities:
        agent.commodities[c].route = {flow_var[0] for flow_var in active_flow if flow_var[1] == c}
        
    # We update the free capacity of the edges
    for c in agent.served_commodities:
        for e in agent.commodities[c].route:
            agent.edges[e].free_capacity -= agent.commodities[c].units

    # We get dictionary of commodities of the agent which are not served (and are different to 0)
    agent.unserved_commodities = {c for c in agent.commodities if c not in agent.served_commodities and agent.commodities[c].units != 0}

    # Dictionary with active edges with free (not used) capacity
    agent.edges_with_capacity = {e for e in agent.active_edges if agent.edges[e].free_capacity > 0}


# Central planner model
def recover_data_cooperation(mdl,central_planner,type_cooperation):
    active_flow= [flow_var for flow_var in [(edge,commodity) for edge in central_planner.edges for commodity in central_planner.commodities] if mdl.f[flow_var].solution_value>0.9]
    central_planner.served_commodities = {a[1] for a in active_flow} # Dictionary with the satisfied commodities as keys
  
    # We assign to each satisfied commodity its proper flow from origin to terminal
    for c in central_planner.served_commodities:
        central_planner.commodities[c].route = {flow_var[0] for flow_var in active_flow if flow_var[1] == c}

    
    if type_cooperation == 'full_cooperation':
        central_planner.active_edges = {e for e in central_planner.edges if mdl.u[e].solution_value>0.9} # We use >0.9 because sometimes CPLEX can say the value is 0.99999, even if it is 1
        # We assign to each edge, its used capacity
        for c in central_planner.served_commodities:
            for e in central_planner.commodities[c].route:
                central_planner.edges[e].free_capacity -= central_planner.commodities[c].units


#Iterative model
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
            info_platform.demanded_edges_conditions[agent.id].append(cl.EdgesConditions(temp_list,temp_value))

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


