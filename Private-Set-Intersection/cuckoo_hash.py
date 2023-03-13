import math
from random import randint
from typing import List, Tuple, Union

# The hash family used for Cuckoo hashing relies on the Murmur hash family (mmh3)
import mmh3

from auxiliary_functions import get_random_distinct_integer, windowing
from constants import LOG_NO_HASHES, OUTPUT_BITS, NUM_OF_HASHES, NUM_OF_BINS, POW_2_MASK


def location(seed, item):
    '''
    Computes the location of an item in a Cuckoo hash table.

    :param seed: a seed value for the Murmur hash function.
    :param item: an integer to be hashed.
    :return: Murmur(item_left) xor item_right, where item = item_left || item_right
    '''

    item_left = item >> OUTPUT_BITS
    item_right = item & POW_2_MASK
    hash_item_left = mmh3.hash(str(item_left), seed, signed=False) >> (32 - OUTPUT_BITS)
    return hash_item_left ^ item_right


def left_and_index(item, index): 
    '''
    Combines an item and an index into a single integer.

    :param item: an integer
    :param index: a LOG_NO_HASHES bits integer
    :return: an integer represented as item_left || index 
    '''
    return ((item >> (OUTPUT_BITS)) << (LOG_NO_HASHES)) + index 	


def extract_index(item_left_and_index): 
    '''
    Extracts the index from an integer that combines an item and an index.

    :param item_left_and_index: an integer represented as item_left || index
    :return: index extracted
    '''
    return item_left_and_index & (2 ** LOG_NO_HASHES - 1) 


def reconstruct_item(item_left_and_index, current_location, seed):
    '''
    Reconstructs the original item from an integer that combines an item
    and an index, the corresponding location obtained from the location()
    function, and the seed value used by the Murmur hash function.

    :param item_left_and_index: an integer represented as item_left || index
    :param current_location: the corresponding location, i.e. Murmur_hash(item_left) xor item_right
    :param seed: the seed of the Murmur hash function
    :return: the integer item
    '''
    item_left = item_left_and_index >> LOG_NO_HASHES
    hashed_item_left = mmh3.hash(str(item_left), seed, signed=False) >> (32 - OUTPUT_BITS)
    item_right = hashed_item_left ^ current_location
    return (item_left << OUTPUT_BITS) + item_right


class CuckooHash():
    """
    The CuckooHash class implements a data structure for cuckoo hashing.

    Attributes:
        hash_seed (list): A list of integers that will be used as seeds for hashing.
        number_of_bins (int): The number of bins in the hash table.
        recursion_depth (int): The maximum recursion depth when inserting an item into the hash table.
        data_structure (list): The actual hash table represented as a list.
        insert_index (int): The current index used for inserting an item into the hash table.
        depth (int): The current recursion depth when inserting an item into the hash table.

    Methods:
        insert_items(items: List[int]) -> None:
            Inserts multiple items into the hash table.

        insert(item: int) -> None:
            Inserts an item into the hash table.

        pad(dummy_msg: Any) -> None:
            Fills the remaining empty slots in the hash table with a dummy message.

        windowing(minibin_cap: int, plain_mod: int) -> List:
            Applies windowing to all items in the hash table and returns a list of the windowed items.
    """

    def __init__(self, hash_seed: List[int]):
        """
        CuckooHash Constructor.

        :param hash_seed: A list of NUM_OF_HASHES integers that are used as the seeds for the hash functions.
        """
        self.number_of_bins = NUM_OF_BINS
        self.recursion_depth = int(8 * math.log(self.number_of_bins) / math.log(2))
        self.data_structure = [None for j in range(self.number_of_bins)]
        self.insert_index = randint(0, NUM_OF_HASHES - 1)
        self.depth = 0

        self.hash_seed = hash_seed

    def insert_items(self, items: List[int]) -> None:
        """
        Inserts a list of items into the CuckooHash data structure.

        :param items: A list of integers to insert.
        """
        for item in items:
            self.insert(item)

    def insert(self, item: int) -> None:
        """
        Inserts an item into the CuckooHash data structure.

        :param item: an integer to insert.
        """
        current_location = location( self.hash_seed[self.insert_index], item)
        current_item = self.data_structure[ current_location]
        self.data_structure[ current_location ] = left_and_index(item, self.insert_index)

        if (current_item == None):
            self.insert_index = randint(0, NUM_OF_HASHES - 1)	
            self.depth = 0	
        else:
            unwanted_index = extract_index(current_item)
            self.insert_index = get_random_distinct_integer(NUM_OF_HASHES, unwanted_index)	
            if (self.depth < self.recursion_depth):
                self.depth +=1
                jumping_item = reconstruct_item(current_item, current_location, self.hash_seed[unwanted_index])
                self.insert(jumping_item)		
            else:
                raise Exception('Hashing failed: bin is full')
    
    def pad(self, dummy_msg: int) -> None:
        """
        Pads the CuckooHash data structure with a dummy message.

        :param dummy_msg: an integer that will be used as the dummy message.
        """
        for i in range(self.number_of_bins):
            if (self.data_structure[i] == None):
                self.data_structure[i] = dummy_msg

    def windowing(self, minibin_cap: int, plain_mod: int) -> List[Union[None, Tuple[int, int]]]:
        """
        Applies windowing for all items in the CuckooHash data structure.

        :param minibin_cap: an integer representing the size of each minibin.
        :param plain_mod: an integer representing the size of the plain modulus.
        :return: a list of tuples representing the windowed items.
        """
        windowed_items = []
        for item in self.data_structure:
            windowed_items.append(windowing(item, minibin_cap, plain_mod))
        return windowed_items
