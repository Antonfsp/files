from classes import Commodity, Edge

file = open('instance.txt','r')
lines_list = file.readlines()
N, V = (int(x) for x in lines_list[0].split())
commodities = {i:{} for i in range(N)}
edges = {i:{} for i in range(N)}
# print(lines_list)
# print(lines_list[1].rstrip() == 'Agent')
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
            commodities[owner][(temp[0],temp[1],temp[2])] = Commodity(temp[0],temp[1],temp[2],temp[3],temp[4])
        if prev == 'Edge':
            temp = [int(x) for x in line.split()]
            edges[owner][(temp[0],temp[1],temp[2])] = Edge(temp[0],temp[1],temp[2],temp[3],temp[4])
