from math import log2

# sizes of databases of server and client
# size of intersection should be less than size of client's database
server_size = 2 ** 20
client_size = 4000
intersection_size = 3500

# seeds used by both the Server and the Client for the Murmur hash functions
hash_seeds = [123456789, 10111213141516, 17181920212223]

# output_bits = number of bits of output of the hash functions
# number of bins for simple/Cuckoo Hashing = 2 ** output_bits
output_bits = 13

# encryption parameters of the BFV scheme: the plain modulus and the polynomial modulus degree
plain_modulus = 536903681
poly_modulus_degree = 2 ** 13

# the number of hashes we use for simple/Cuckoo hashing
number_of_hashes = 3

# length of the database items
sigma_max = int(log2(plain_modulus)) + output_bits - (int(log2(number_of_hashes)) + 1) 

# B = [68, 176, 536, 1832, 6727] for log(server_size) = [16, 18, 20, 22, 24]
bin_capacity = 536

# partitioning parameter
alpha = 16

# windowing parameter
ell = 2

# write about these
##############################################################################################################
log_no_hashes = int(log2(number_of_hashes)) + 1
base = 2 ** ell
minibin_capacity = int(bin_capacity / alpha)
logB_ell = int(log2(minibin_capacity) / ell) + 1 # <= 2 ** HE.depth