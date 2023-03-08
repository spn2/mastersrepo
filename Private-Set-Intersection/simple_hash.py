import math
import mmh3

from auxiliary_functions import compute_coefficients_from_roots
from constants import BIN_CAP, NUM_OF_BINS, NUM_OF_HASHES, OUTPUT_BITS, SIGMA_MAX

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

    def partition(self, num_minibins, minibin_cap, plain_mod):
        """
        Performs partitioning on the bins (self.hashed_data). Bins are partitioned into
        num_minibins minibins, with minibin_cap items in each minibin. Minibins are represented
        as coefficients from polynomials with degree num_minibins/num_bins . This polynomial equals to zero
        whenever it is evaluated at any of the items in the minibin.

        :param num_minibins: the number of minibins
        :param minibin_cap: the number of items in each minibin
        :param plain_mod: plain modulus (coefficient are modulo plain_mod)
        :return: list of integers representing coefficients from the minibin polynomials
        """

        coefficients = []
        for i in range(self.num_bins):
            bin_coefficients = []
            for j in range(num_minibins):
                roots = [self.hashed_data[i][minibin_cap * j + k] for k in range(minibin_cap)]
                bin_coefficients = bin_coefficients + compute_coefficients_from_roots(roots, plain_mod)
            coefficients.append(bin_coefficients)
        return coefficients
