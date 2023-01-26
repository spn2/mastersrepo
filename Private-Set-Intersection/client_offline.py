import pickle
from time import time

from auxiliary_functions import *
from oprf import client_prf_offline
from oprf_constants import GENERATOR_ORDER, G, OPRF_CLIENT_KEY



if __name__ == "__main__":
    t0 = time()

    # key * generator of elliptic curve
    client_point_precomputed = (OPRF_CLIENT_KEY % GENERATOR_ORDER) * G

    # store client's set in memory 
    client_set = read_file_return_list("client_set")

    # OPRF layer: encode the client's set as elliptic curve points.
    encoded_client_set = [client_prf_offline(item, client_point_precomputed) for item in client_set]
    print(type(encoded_client_set[0][0]))

    # write the preprocessed client's set to disk
    g = open('client_preprocessed', 'wb')
    pickle.dump(encoded_client_set, g)	 
    g.close()

    t1 = time()

    print('Client OFFLINE time: {:.2f}s'.format(t1-t0))
