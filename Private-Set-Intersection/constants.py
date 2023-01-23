from math import log2

# Database sizes for client and server
# Important: INTERSECTION_SIZE < SERVER_SIZE and INTERSECTION_SIZE < CLIENT_SIZE
SERVER_SIZE = 2 ** 20
CLIENT_SIZE = 4000
INTERSECTION_SIZE = 3500

# seeds used by both the Server and the Client for the Murmur hash functions
HASH_SEEDS = [123456789, 10111213141516, 17181920212223]

# output_bits = number of bits of output of the hash functions
# number of bins for simple/Cuckoo Hashing = 2 ** output_bits
OUTPUT_BITS = 13

# encryption parameters of the BFV scheme: the plain modulus and the polynomial modulus degree
PLAIN_MOD = 536903681
POLY_MOD = 2 ** 13

# the number of hashes we use for simple/Cuckoo hashing
NUM_OF_HASHES = 3

# length of the database items
SIGMA_MAX = int(log2(PLAIN_MOD)) + OUTPUT_BITS - (int(log2(NUM_OF_HASHES)) + 1) 

# B = [68, 176, 536, 1832, 6727] for log(server_size) = [16, 18, 20, 22, 24]
BIN_CAP = 536

# partitioning parameter
ALPHA = 16

# windowing parameter
ELL = 2

# write about these
##############################################################################################################
LOG_NO_HASHES = int(log2(NUM_OF_HASHES)) + 1
BASE = 2 ** ELL
MINIBIN_CAP = int(BIN_CAP/ALPHA)
LOG_B_ELL = int(log2(MINIBIN_CAP/ELL)) + 1 # <= 2 ** HE.depth

# OPRF keys
OPRF_CLIENT_KEY = 12345678910111213141516171819222222222222
OPRF_SERVER_KEY = 1234567891011121314151617181920
