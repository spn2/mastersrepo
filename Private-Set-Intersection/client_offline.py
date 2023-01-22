import pickle
from oprf import client_prf_offline, order_of_generator, G
from time import time
from constants import OPRF_CLIENT_KEY

# client's PRF secret key (a value from range(order_of_generator))
t0 = time()

# key * generator of elliptic curve
client_point_precomputed = (OPRF_CLIENT_KEY % order_of_generator) * G

client_set = []
f = open('client_set', 'r')
lines = f.readlines()
for item in lines:
	client_set.append(int(item[:-1]))
f.close()

# OPRF layer: encode the client's set as elliptic curve points.
encoded_client_set = [client_prf_offline(item, client_point_precomputed) for item in client_set]

g = open('client_preprocessed', 'wb')
pickle.dump(encoded_client_set, g)	 
g.close()   
t1 = time()
print('Client OFFLINE time: {:.2f}s'.format(t1-t0))
