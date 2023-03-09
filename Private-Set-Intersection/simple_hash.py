import math
from typing import List

import mmh3

from auxiliary_functions import compute_coefficients_from_roots
from constants import BIN_CAP, NUM_OF_BINS, NUM_OF_HASHES, OUTPUT_BITS, SIGMA_MAX

log_no_hashes = int(math.log(NUM_OF_HASHES) / math.log(2)) + 1
POW_2_MASK = 2 ** OUTPUT_BITS - 1

def left_and_index(item: int, index: int) -> int:
    '''
    Returns an integer represented as item_left || index, where item_left is the leftmost
    OUTPUT_BITS bits of item and index is a log_no_hashes bits integer.

    :param item: an integer
    :param index: a log_no_hashes bits integer
    :return: an integer represented as item_left || index
    '''

    return ((item >> (OUTPUT_BITS)) << (log_no_hashes)) + index


def location(seed: int, item: int) -> int:
    '''
    Calculates the location of an item in a hash table using the Murmur hash function.

    The item is split into two parts: item_left and item_right. The Murmur hash of item_left
    is calculated using the mmh3.hash function with the given seed. The lower bits of the
    hashed item_left and item_right are XORed to obtain the location of the item in the
    hash table.

    :param seed: seed for the Murmur hash function.
    :param item: integer to be hashed.
    :param output_bits: number of bits to be used in the output (default: 16).
    :return: location of the item in the hash table.
    '''

    item_left = item >> OUTPUT_BITS
    item_right = item & POW_2_MASK
    hash_item_left = mmh3.hash(str(item_left), seed, signed=False) >> (32 - OUTPUT_BITS)
    return hash_item_left ^ item_right

class SimpleHash():
    """
    Class for performing simple hashing on a set of integers.

    Attributes:
        num_bins (int): the number of bins to hash the data into
        hashed_data (List[List[int]]): list of lists representing the hashed data,
                                       where each bin has a maximum capacity of bin_capacity
        occurences (List[int]): list representing the number of elements in each bin
        hash_seed (List[int]): list of seed values for the hash function
        bin_capacity (int): maximum capacity for bins
        msg_padding (int): padding value for bins to ensure a consistent size

    Methods:
        insert_entries(items: List[int]) -> None:
            Inserts a list of integers into the hash table
            using the insert method for each hash seed.

        insert(item: int, i: int) -> None:
            Inserts an integer item into the hash table for a given
            hash seed index i.

        pad_bins() -> None:
            Pads empty bins with a consistent value to ensure
            a consistent bin size.

        partition(num_minibins: int, minibin_cap: int, plain_mod: int) -> List[List[int]]:
            Performs partitioning on the hashed data.
            Bins are partitioned into num_minibins minibins,
            each with a capacity of minibin_cap.
            Returns a list of lists representing the coefficients of
            the polynomial representing each minibin.
    """


    def __init__(self, hash_seed):
        """
        SimpleHashing constructor.
        
        :param hash_seed: List of hash seeds
        """

        self.num_bins = NUM_OF_BINS
        self.hashed_data = [[None for j in range(BIN_CAP)] for i in range(self.num_bins)] # no_bins bins, len = BIN_CAP
        self.occurrences = [0 for i in range(self.num_bins)]
        self.hash_seed = hash_seed
        self.bin_capacity = BIN_CAP
        self.msg_padding = 2 ** (SIGMA_MAX - OUTPUT_BITS + int(math.log2(NUM_OF_HASHES)) + 1) + 1 # data padding


    def insert_entries(self, items: List[int]):
        """
        Inserts a set of items using the insert method.
        
        :param items: a list of integers representing the items to be inserted.
        """

        for item in items:
            for i in range(len(self.hash_seed)): # NUM_OF_HASHES
                self.insert(item, i)


    def insert(self, item: int, i: int) -> None:
        """
        Inserts an item using hash i at the position determined by the hash value.

        :param item: An integer representing the item to be inserted.
        :param i: An integer representing the index of the hash function to be used.
        """

        # Compute the hash value and check if the corresponding bin is full
        loc = location(self.hash_seed[i], item)
        if self.occurrences[loc] < self.bin_capacity:
            # If there is room in the bin, insert the item in the hashed data array
            self.hashed_data[loc][self.occurrences[loc]] = left_and_index(item, i)
            self.occurrences[loc] += 1
        else:
            raise Exception('Hashing failed: bin is full')


    def pad_bins(self):
        """
        Pads bins in the hash structure to have a consistent size.
        """

        for i in range(self.num_bins):
            for j in range(self.bin_capacity):
                if self.hashed_data[i][j] == None:
                    self.hashed_data[i][j] = self.msg_padding


    def partition(self, num_minibins: int, minibin_cap: int, plain_mod: int) -> List[List[int]]:
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
                bin_coefficients.extend(compute_coefficients_from_roots(roots, plain_mod))
            coefficients.append(bin_coefficients)

        return coefficients
