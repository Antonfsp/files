from collections import namedtuple
import numpy as np # Basic functions, as random 



# --------------------------------------
# ------- NAMED TUPLE FOR DEMANDS AND EDGES --------
# --------------------------------------

Demands = namedtuple('Demand',['units','revenue'])

Edge = namedtuple('Edge',['capacity','cost','original_capacity'])



# --------------------------------------
# ------- AGENTS CLASS --------
# --------------------------------------

class Agent:

    def __init__(self,id,E,q,c,r):
        self.id = id
        self.demands = {e:Demands(np.random.randint(0,q),r) for e in E}  # Random demands between pairs of nodes
        self.edges = {e:Edge(q,c,q) for e in E} # Dictionary with each key is an edge, and each edge has a capacity and a cost
        self.used_edges = None
        self.satisfied_demands= None
        self.unsatisfied_demands = None
        self.edges_free_capacity = None
        self.payoff_no_cooperation = 0
        self.payoff_cooperation = 0


    def total_payoff(self, type_cooperation):
        if type_cooperation == 'partial1_cooperation':
            return self.payoff_no_cooperation + self.payoff_cooperation
        elif type_cooperation == 'partial2_cooperation' or type_cooperation == 'full_cooperation':
            return self.payoff_cooperation

    @property
    def total_payoff_partial1_cooperation(self):
        return self.payoff_no_cooperation + self.payoff_cooperation

    @property
    def total_payoff_partial2_cooperation(self):
        return self.payoff_cooperation


# --------------------------------------
# ------- CENTRAL PLANNER CLASS --------
# --------------------------------------

class CentralizedSystem:

    def __init__(self,AGENTS,TYPE_COOPERATION):
        self.demands = {}
        self.edges = {}
        self.satisfied_demands= None
        self.unsatisfied_demands = None
        self.used_edges = None

        self.create_demands_set(AGENTS,TYPE_COOPERATION)
        self.create_edges_set(AGENTS, TYPE_COOPERATION)


    def create_demands_set(self,agents, type_cooperation):
        if type_cooperation == 'partial1_cooperation':
            for i in agents:
                for d in i.unsatisfied_demands:
                    self.demands[(d[0],d[1],i.id)] = i.unsatisfied_demands[d]
        elif type_cooperation == 'partial2_cooperation' or type_cooperation == 'full_cooperation':
            for i in agents:
                for d in i.demands:
                    self.demands[(d[0],d[1],i.id)] = i.demands[d]

    def create_edges_set(self,agents,type_cooperation):
        if type_cooperation == 'partial1_cooperation':
            for i in agents:
                for e in i.edges_free_capacity:
                    self.edges[(e[0],e[1],i.id)] = i.edges_free_capacity[e]
        elif type_cooperation == 'partial2_cooperation':
            for i in agents:
                for e in i.used_edges:
                    self.edges[(e[0],e[1],i.id)] = i.edges[e]
        elif type_cooperation == 'full_cooperation':
            for i in agents:
                for e in i.edges:
                    self.edges[(e[0],e[1],i.id)] = i.edges[e]

        
