from constants import *
from simple_hash import Simple_hash
from auxiliary_functions import coeffs_from_roots
from math import log2
import pickle
from oprf import server_prf_offline_parallel, order_of_generator, G
from time import time

from auxiliary_functions import *

# key * generator of elliptic curve
server_point_precomputed = (OPRF_SERVER_KEY % order_of_generator) * G

server_set = read_file_return_list("server_set")

t0 = time()
#The PRF function is applied on the set of the server, using parallel computation
PRFed_server_set = server_prf_offline_parallel(server_set, server_point_precomputed)
PRFed_server_set = set(PRFed_server_set)
t1 = time()

log_no_hashes = int(log2(NUMBER_OF_HASHES)) + 1
dummy_msg_server = 2 ** (SIGMA_MAX - OUTPUT_BITS + log_no_hashes) + 1 
server_size = len(server_set)
minibin_capacity = int(BIN_CAP / ALPHA)
number_of_bins = 2 ** OUTPUT_BITS

# The OPRF-processed database entries are simple hashed
SH = Simple_hash(HASH_SEEDS)
for item in PRFed_server_set:
    for i in range(NUMBER_OF_HASHES):
        SH.insert(item, i)

# simple_hashed_data is padded with dummy_msg_server
for i in range(number_of_bins):
    for j in range(BIN_CAP):
        if SH.simple_hashed_data[i][j] == None:
            SH.simple_hashed_data[i][j] = dummy_msg_server

# Here we perform the partitioning:
# Namely, we partition each bin into alpha minibins with B/alpha items each
# We represent each minibin as the coefficients of a polynomial of degree B/alpha that vanishes in all the entries of the mininbin
# Therefore, each minibin will be represented by B/alpha + 1 coefficients; notice that the leading coeff = 1
t2 = time()

poly_coeffs = []
for i in range(number_of_bins):
    # we create a list of coefficients of all minibins from concatenating the list of coefficients of each minibin
    coeffs_from_bin = []
    for j in range(ALPHA):
        roots = [SH.simple_hashed_data[i][minibin_capacity * j + r] for r in range(minibin_capacity)]
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
