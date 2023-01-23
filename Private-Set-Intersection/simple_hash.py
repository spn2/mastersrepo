from random import randint
import math
import mmh3

#parameters
from constants import *
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
        self.no_bins = 2 ** OUTPUT_BITS
        self.simple_hashed_data = [[None for j in range(BIN_CAP)] for i in range(self.no_bins)]
        self.occurences = [0 for i in range(self.no_bins)]
        self.FAIL = 0
        self.hash_seed = hash_seed
        self.bin_capacity = BIN_CAP

    #  insert item using hash i on position given by location
    def insert(self, item, i):
        loc = location(self.hash_seed[i], item)
        if (self.occurences[loc] < self.bin_capacity):
            self.simple_hashed_data[loc][self.occurences[loc]] = left_and_index(item, i)
            self.occurences[loc] += 1
        else:
            self.FAIL = 1
            print('Simple hashing aborted')
