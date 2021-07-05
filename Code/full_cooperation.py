"""
  Modeling the situation where multiple agents have to decide how to route their flow on a directed network,
 when a fixed cost of edges must be payed if the edges are used. Edges also have some capacity
 The agents have some demands between nodes
"""

import numpy as np # Basic functions, as random 
import matplotlib.pyplot as plt #For plotting
from docplex.mp.model import Model # For modeling the LP problem and solving it with CPLEX

#Setting a seed
np.random.seed(1)