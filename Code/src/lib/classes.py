from collections import namedtuple
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

    @property
    def cost_per_unit(self):
        return self.cost/self.original_capacity


# --------------------------------------
# ------- AGENTS CLASS --------
# --------------------------------------

class Agent:

    def __init__(self,id,edges,commodities):
        self.id = id
        self.edges = edges
        self.commodities = commodities        
        self.served_commodities = {} # List of keys of the demands that are served
        self.unserved_commodities = {} # List of keys of the demands which are not served
        
        self.active_edges = {} # List of keys of the active edges
        self.edges_with_capacity = {} # List of keys of the edges with free capacity
        
        self.payoff_no_cooperation = 0
        self.payoff_cooperation = 0

        self.history_solutions = []
        self.incunbent_solution = None # Most prefered solution for the agent at the moment

    def share_edges(self):
        return {e:self.edges[e] for e in self.edges_with_capacity} # A dictionary, not only a list of keys, with the edges that have free capacity

    def restore_edges_info(self):
        for e in self.edges:
            self.edges[e].free_capacity =  self.edges[e].original_capacity
        self.active_edges = {}
        self.edges_with_capacity = {}

    def restore_commodities_info(self):
        for c in self.commodities:
            self.commodities[c].route = None
        self.served_commodities = {}
        self.unserved_commodities = {}

    def add_solution(self,solution):
        self.history_solutions.append(solution)

    @property
    def total_payoff_residual_cooperation(self):
        return self.payoff_no_cooperation + self.payoff_cooperation

    @property
    def total_payoff_partial_cooperation(self):
        return self.payoff_cooperation

    def total_payoff(self, type_cooperation):
        if type_cooperation == 'residual_cooperation':
            return self.payoff_no_cooperation + self.payoff_cooperation
        elif type_cooperation == 'partial_cooperation' or type_cooperation == 'full_cooperation':
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
        if type_cooperation == 'residual_cooperation':
            for i in agents:
                for d in i.unserved_commodities:
                    self.commodities[d] = copy.deepcopy(i.commodities[d])
        elif type_cooperation == 'partial_cooperation' or type_cooperation == 'full_cooperation':
            for i in agents:
                for d in i.commodities:
                    self.commodities[d] = copy.deepcopy(i.commodities[d])

    def create_edges_set(self,agents,type_cooperation):
        if type_cooperation == 'residual_cooperation':
            for i in agents:
                for e in i.edges_with_capacity:
                    self.edges[e] = copy.deepcopy(i.edges[e])
        elif type_cooperation == 'partial_cooperation':
            for i in agents:
                for e in i.active_edges:
                    self.edges[e] = copy.deepcopy(i.edges[e])
        elif type_cooperation == 'full_cooperation':
            for i in agents:
                for e in i.edges:
                    self.edges[e] = copy.deepcopy(i.edges[e])



# --------------------------------------
# ------- PLATFORM FOR SHARE INFORMATION --------
# --------------------------------------
        
class informationPlatform():
    def __init__(self,agents):
        self.shared_edges = {i.id:{} for i in agents}
        self.demanded_edges = {i.id:{} for i in agents for j in agents if j !=i}
        self.demanded_edges_conditions = {i.id:[] for i in agents}

    def restore_info(self,agent):
        self.shared_edges[agent.id] = {}
        self.demanded_edges[agent.id] = {}
        self.demanded_edges_conditions[agent.id] = []



# -------------------------------------
#  Class to store a "custom" solution
# -------------------------------------

class Solution():
    def __init__(self,agent,model):
        self.payoff = model.objective_value
        self.out_payments = model.out_payments.solution_value
        self.in_payments = model.in_payments.solution_value
        self.served_commodities = {c:agent.commodities[c].route for c in agent.served_commodities}
        self.active_edges = {e for e in agent.active_edges}        

    def print_data(self):
        print("Payoff: %s" %(self.payoff))
        print("Payments to do: %s" %(self.out_payments))
        print("Payments to receive: %s" %(self.in_payments))
        print("Served commodities: %s" %([c for c in self.served_commodities]))
        print("Active edges: %s" %([e for e in self.active_edges]))
        print()

    def equal_to(self,other):
        if self.payoff != other.payoff:
            return False
        elif self.out_payments != other.out_payments:
            return False
        elif self.in_payments != other.in_payments:
            return False
        elif self.served_commodities != other.served_commodities:
            return False
        elif self.active_edges != other.active_edges:
            return False
        else:
            return True

    
# ------------------
# ---- namedtuple to associate list of edges with values
# ------------------

EdgesConditions = namedtuple('EdgesConditions','edges price')

test = EdgesConditions([(0,1,2),(2,3,1)],4)