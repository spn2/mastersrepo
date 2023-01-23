import pickle
from oprf import client_prf_offline, order_of_generator, G
from time import time
from constants import OPRF_CLIENT_KEY

t0 = time()

# key * generator of elliptic curve
client_point_precomputed = (OPRF_CLIENT_KEY % order_of_generator) * G

client_set = []


# OPRF layer: encode the client's set as elliptic curve points.
encoded_client_set = [client_prf_offline(item, client_point_precomputed) for item in client_set]

g = open('client_preprocessed', 'wb')
pickle.dump(encoded_client_set, g)	 
g.close()   
t1 = time()
print('Client OFFLINE time: {:.2f}s'.format(t1-t0))
