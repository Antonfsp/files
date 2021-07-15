import numpy as np # Basic functions, as random 
import copy



# --------------------------------------
# ---------  COMMODITY CLASS --------------
# --------------------------------------

class Commodity():

        def __init__(self,v,w,owner,units,revenue):
            self.origin = v
            self.terminal = w
            self.owner = owner
            self.units = units
            self.revenue = revenue
            self.route = None

class Edge():

    def __init__(self,head,tail,owner,cost,original_capacity):
        self.head = head
        self.tail = tail
        self.owner = owner
        self.cost = cost
        self.original_capacity = original_capacity
        self.free_capacity = original_capacity
        self.assigned_commodities = set()

    @property
    def cost_per_unit(self):
        return self.cost/self.original_capacity


# --------------------------------------
# ------- AGENTS CLASS --------
# --------------------------------------

class Agent:

    def __init__(self,id,E,q,c,r):
        self.id = id
        self.commodities = {(e[0],e[1],id):Commodity(e[0],e[1],id,np.random.randint(0,q),r) for e in E}  # Random commodities between pairs of nodes
        self.edges = {(e[0],e[1],id):Edge(e[0],e[1],id,c,q) for e in E} # Dictionary with each key is an edge, and each edge has a capacity and a cost
        self.served_commodities = {} # List of keys of the demands that are served
        self.unserved_commodities = {} # List of keys of the demands which are not served
        self.active_edges = {} # List of keys of the active edges
        self.edges_with_capacity = {} # List of keys of the edges with free capacity
        self.payoff_no_cooperation = 0
        self.payoff_cooperation = 0
        self.incunbent_solution = None # Most prefered solution for the agent at the moment

        # self.used_edges_from_others = None # Dict of the form {(v,w,i):5}, meaning that 5 units of capacity are used in the edge v,w,i, when i != self.id
        # self.commodities_through_others = None # Dict of the form {d:[(v,w,i)]}, meaning that the demand d is routed through the edge (v,w,i)

    @property
    def share_info(self):
        return {e:self.edges[e] for e in self.edges_with_capacity} # A dictionary, not only a list of keys, with the edges that have free capacity

    @property
    def total_payoff_partial1_cooperation(self):
        return self.payoff_no_cooperation + self.payoff_cooperation

    @property
    def total_payoff_partial2_cooperation(self):
        return self.payoff_cooperation

    def total_payoff(self, type_cooperation):
        if type_cooperation == 'partial1_cooperation':
            return self.payoff_no_cooperation + self.payoff_cooperation
        elif type_cooperation == 'partial2_cooperation' or type_cooperation == 'full_cooperation':
            return self.payoff_cooperation

# --------------------------------------
# ------- CENTRAL PLANNER CLASS --------
# --------------------------------------

class CentralizedSystem:

    def __init__(self,AGENTS,TYPE_COOPERATION):
        self.commodities = {}
        self.edges = {}
        self.sserved_commodities= {} # List of keys of the demands that are served
        self.unserved_commodities = {} # List of keys of the demands that are not served
        self.active_edges = {} # List of keys of the active edges

        self.create_commodities_set(AGENTS,TYPE_COOPERATION)
        self.create_edges_set(AGENTS, TYPE_COOPERATION)


    def create_commodities_set(self,agents, type_cooperation):
        if type_cooperation == 'partial1_cooperation':
            for i in agents:
                for d in i.unserved_commodities:
                    self.commodities[d] = copy.deepcopy(i.commodities[d])
        elif type_cooperation == 'partial2_cooperation' or type_cooperation == 'full_cooperation':
            for i in agents:
                for d in i.commodities:
                    self.commodities[d] = copy.deepcopy(i.commodities[d])

    def create_edges_set(self,agents,type_cooperation):
        if type_cooperation == 'partial1_cooperation':
            for i in agents:
                for e in i.edges_free_capacity:
                    self.edges[e] = copy.deepcopy(i.edges[e])
        elif type_cooperation == 'partial2_cooperation':
            for i in agents:
                for e in i.active_edges:
                    self.edges[e] = copy.deepcopy(i.edges[e])
        elif type_cooperation == 'full_cooperation':
            for i in agents:
                for e in i.edges:
                    self.edges[e] = copy.deepcopy(i.edges[e])

        
