from random import sample
from constants import SERVER_SIZE, CLIENT_SIZE, INTERSECTION_SIZE

#set elements can be integers < order of the generator of the elliptic curve (192 bits integers if P192 is used); 'sample' works only for a maximum of 63 bits integers.
disjoint_union = sample(range(2 ** 63 - 1), SERVER_SIZE + CLIENT_SIZE)
intersection = disjoint_union[:INTERSECTION_SIZE]
server_set = intersection + disjoint_union[INTERSECTION_SIZE: SERVER_SIZE]
client_set = intersection + disjoint_union[SERVER_SIZE: SERVER_SIZE - INTERSECTION_SIZE + CLIENT_SIZE]

f = open('server_set', 'w')
for item in server_set:
	f.write(str(item) + '\n')
f.close()

g = open('client_set', 'w')
for item in client_set:
	g.write(str(item) + '\n')
g.close()		

h = open('intersection', 'w')
for item in intersection:
	h.write(str(item) + '\n')
h.close()
