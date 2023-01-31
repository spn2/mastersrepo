import math
import mmh3
from random import randint

from auxiliary_functions import coeffs_from_roots
from constants import ALPHA, BIN_CAP, MINIBIN_CAP, NUM_OF_BINS, NUM_OF_HASHES, OUTPUT_BITS, PLAIN_MOD, SIGMA_MAX

log_no_hashes = int(math.log(NUM_OF_HASHES) / math.log(2)) + 1
POW_2_MASK = 2 ** OUTPUT_BITS - 1

def left_and_index(item, index):
    '''
    :param item: an integer
    :param index: a log_no_hashes bits integer
    :return: an integer represented as item_left || index
    '''

    return ((item >> (OUTPUT_BITS)) << (log_no_hashes)) + index

#The hash family used for simple hashing relies on the Murmur hash family (mmh3)

def location(seed, item):
    '''
    :param seed: a seed of a Murmur hash function
    :param item: an integer
    :return: Murmur_hash(item_left) xor item_right, where item = item_left || item_right
    '''

    item_left = item >> OUTPUT_BITS
    item_right = item & POW_2_MASK
    hash_item_left = mmh3.hash(str(item_left), seed, signed=False) >> (32 - OUTPUT_BITS)
    return hash_item_left ^ item_right

class Simple_hash():

    def __init__(self, hash_seed):
        self.num_bins = NUM_OF_BINS
        self.hashed_data = [[None for j in range(BIN_CAP)] for i in range(self.num_bins)] # no_bins bins, len = BIN_CAP
        self.occurences = [0 for i in range(self.num_bins)]
        self.FAIL = 0
        self.hash_seed = hash_seed
        self.bin_capacity = BIN_CAP
        self.msg_padding = 2 ** (SIGMA_MAX - OUTPUT_BITS + int(math.log2(NUM_OF_HASHES)) + 1) + 1 # data padding
        self.num_minibins = ALPHA
        self.minibin_cap = MINIBIN_CAP
        self.plain_mod = PLAIN_MOD

    # inserts a set of items, using self.insert
    # for our purpose the set of items should be the PRFed server's set
    def insert_entries(self, items):
        for item in items:
            for i in range(len(self.hash_seed)): # NUM_OF_HASHES
                self.insert(item, i)

    #  insert item using hash i on position given by location
    def insert(self, item, i):
        loc = location(self.hash_seed[i], item)
        if (self.occurences[loc] < self.bin_capacity):
            self.hashed_data[loc][self.occurences[loc]] = left_and_index(item, i)
            self.occurences[loc] += 1
        else:
            self.FAIL = 1
            print('Simple hashing aborted')

    # bins are padded to have a consistent size
    def pad_bins(self):
        for i in range(self.num_bins):
            for j in range(self.bin_capacity):
                if self.hashed_data[i][j] == None:
                    self.hashed_data[i][j] = self.msg_padding

    # bins are partitioned into alpha minibins (i.e. each new minibin has B/alpha items)
    def partition(self):
        poly_coeffs = []
        for i in range(self.num_bins):
            coeffs_from_bin = []
            for j in range(self.num_minibins):
                roots = [self.hashed_data[i][self.minibin_cap * j + r] for r in range(self.minibin_cap)]
                coeffs_from_bin = coeffs_from_bin + coeffs_from_roots(roots, self.plain_mod).tolist()
            poly_coeffs.append(coeffs_from_bin)
        return poly_coeffs
