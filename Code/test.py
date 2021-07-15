import copy

class Car():
    def __init__(self,q):
        self.capacity = q



d={'a':Car(5)}

print(d['a'].capacity)

d['a'].capacity = 3

print(d['a'].capacity)

t={}
t['a'] = copy.deepcopy(d['a'])

print(t['a'].capacity)

t['a'].capacity = 1

print(t['a'].capacity)

print(d['a'].capacity)

