from math import log2

# Database sizes
SERVER_SIZE = 2 ** 20
"""
Server's database size.
"""
CLIENT_SIZE = 4000
"""
Client's database size.
"""
INTERSECTION_SIZE = 3500
"""
How many items the server and client should have in common.
Make sure it is smaller than both the client and server size.
"""

# Hash constants
NUM_OF_HASHES = 3
"""
The number of hash functions used for simple/Cuckoo hashing.
"""
LOG_NO_HASHES = int(log2(NUM_OF_HASHES)) + 1
"""
The number of bits required to represent the range of hash values produced by the hash functions.
"""
HASH_SEEDS = [123456789, 10111213141516, 17181920212223]
"""
A list representing the seeds used by both the server and client for the Murmur hash functions.
"""
OUTPUT_BITS = 13
"""
The number of bits of output of the hash functions.
"""

# BFV scheme parameters
PLAIN_MOD = 536903681
"""
The plain modulus of the BFV scheme.
"""
POLY_MOD = 2 ** 13
"""
The polynomial modulus degree of the BFV scheme.
"""

# Bin parameters
NUM_OF_BINS = 2 ** OUTPUT_BITS
"""
The number of bins for both simple and Cuckoo hashing.
"""
BIN_CAP = 536
"""
The capacity of each bin in simple/Cuckoo hashing.
"""
ALPHA = 16
"""
The partitioning parameter
"""
MINIBIN_CAP = int(BIN_CAP/ALPHA)
"""
The number of items in a minibin.
"""

# Windowing
ELL = 2
"""
The windowing parameter.
"""
BASE = 2 ** ELL
"""
The base used for exponentiation in the windowing technique.
"""
LOG_B_ELL = int(log2(MINIBIN_CAP/ELL)) + 1
"""
Number of elements in each row of the windowing matrix. Needs to be <= 2 ** HE.depth
"""

SIGMA_MAX = int(log2(PLAIN_MOD)) + OUTPUT_BITS - (int(log2(NUM_OF_HASHES)) + 1)
"""
The length of the database items.
"""