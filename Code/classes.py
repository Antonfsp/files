import numpy as np # Basic functions, as random 


# --------------------------------------
# ------- AGENTS CLASS --------
# --------------------------------------

class Agent:

    def __init__(self,id,E,q):
        self.id = id
        self.demands = {i:np.random.randint(0,q) for i in E}  # Random demands between pairs of nodes
        self.used_edges = None
        self.satisfied_demands= None
        self.unsatisfied_demands = None
        self.edges_free_capacity = None
        self.profit_first_stage = 0
        self.profit_second_stage = 0

    @property
    def total_profit(self):
        return self.profit_first_stage + self.profit_second_stage


# --------------------------------------
# ------- CENTRAL PLANNER CLASS --------
# --------------------------------------

class CentralizedSystem:

    def __init__(self,AGENTS):
        self.demands = {}
        self.edges = {}
        self.satisfied_demands= None
        self.unsatisfied_demands = None

        self.create_demands_set(AGENTS)
        self.create_edges_set(AGENTS)


    def create_demands_set(self,agents):
        for i in agents:
            for d in i.unsatisfied_demands:
                self.demands[(d[0],d[1],i.id)] = i.unsatisfied_demands[d]
    
    def create_edges_set(self,agents):
        for i in agents:
            for e in i.edges_free_capacity:
                self.edges[(e[0],e[1],i.id)] = i.edges_free_capacity[e]
        
