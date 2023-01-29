from math import log2
import pickle
from time import time

from auxiliary_functions import coeffs_from_roots, read_file_return_list
from constants import *
from oprf import server_prf_offline_parallel
from oprf_constants import GENERATOR_ORDER, G, OPRF_SERVER_KEY
from simple_hash import Simple_hash

# simple_hashed_data is padded with MSG_PADDING
MSG_PADDING = 2 ** (SIGMA_MAX - OUTPUT_BITS + int(log2(NUM_OF_HASHES)) + 1) + 1

if __name__ == "__main__":

    # store server's set in memory 
    server_set = read_file_return_list("server_set")

    # key * generator of elliptic curve (EC)
    key_gen_point = (OPRF_SERVER_KEY % GENERATOR_ORDER) * G

    t0 = time()

    # server's items multiplied by server's key * generator of the EC
    PRFed_server_set = set(server_prf_offline_parallel(server_set, key_gen_point))

    t1 = time()

    # The OPRF-processed database entries are simple hashed
    SH = Simple_hash(HASH_SEEDS)
    for item in PRFed_server_set:
        for i in range(NUM_OF_HASHES):
            SH.insert(item, i)

    # simple_hashed_data is padded with MSG_PADDING
    for i in range(NUM_OF_BINS):
        for j in range(BIN_CAP):
            if SH.simple_hashed_data[i][j] == None:
                SH.simple_hashed_data[i][j] = MSG_PADDING

    t2 = time()

    # Here we perform the partitioning:
    # Namely, we partition each bin into alpha minibins with B/alpha items each
    # We represent each minibin as the coefficients of a polynomial of degree B/alpha that vanishes in all the entries of the mininbin
    # Therefore, each minibin will be represented by B/alpha + 1 coefficients; notice that the leading coeff = 1

    poly_coeffs = []
    for i in range(NUM_OF_BINS):
        # we create a list of coefficients of all minibins from concatenating the list of coefficients of each minibin
        coeffs_from_bin = []
        for j in range(ALPHA):
            roots = [SH.simple_hashed_data[i][MINIBIN_CAP * j + r] for r in range(MINIBIN_CAP)]
            coeffs_from_bin = coeffs_from_bin + coeffs_from_roots(roots, PLAIN_MOD).tolist()
        poly_coeffs.append(coeffs_from_bin)

    f = open('server_preprocessed', 'wb')
    pickle.dump(poly_coeffs, f)
    f.close()
    t3 = time()
    #print('OPRF preprocessing time {:.2f}s'.format(t1 - t0))
    #print('Hashing time {:.2f}s'.format(t2 - t1))
    #print('Poly coefficients from roots time {:.2f}s'.format(t3 - t2))
    print('Server OFFLINE time {:.2f}s'.format(t3 - t0))