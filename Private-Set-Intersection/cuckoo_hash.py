import math
from random import randint 

# The hash family used for Cuckoo hashing relies on the Murmur hash family (mmh3)
import mmh3

from constants import OUTPUT_BITS, NUM_OF_HASHES

POW_2_MASK = 2 ** OUTPUT_BITS - 1
LOG_NO_HASHES = int(math.log(NUM_OF_HASHES) / math.log(2)) + 1


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

def left_and_index(item, index): 
	'''
	:param item: an integer
	:param index: a LOG_NO_HASHES bits integer
	:return: an integer represented as item_left || index 
	'''
	return ((item >> (OUTPUT_BITS)) << (LOG_NO_HASHES)) + index 	

def extract_index(item_left_and_index): 
	'''
	:param item_left_and_index: an integer represented as item_left || index
	:return: index extracted
	'''
	return item_left_and_index & (2 ** LOG_NO_HASHES - 1) 

def reconstruct_item(item_left_and_index, current_location, seed):
	'''
	:param item_left_and_index: an integer represented as item_left || index
	:param current_location: the corresponding location, i.e. Murmur_hash(item_left) xor item_right
	:param seed: the seed of the Murmur hash function
	:return: the integer item
	'''
	item_left = item_left_and_index >> LOG_NO_HASHES
	hashed_item_left = mmh3.hash(str(item_left), seed, signed=False) >> (32 - OUTPUT_BITS)
	item_right = hashed_item_left ^ current_location
	return (item_left << OUTPUT_BITS) + item_right

def rand_point(bound, i): 
	'''
	:param bound: an integer
	:param i: an integer less than bound
	:return: a uniform integer from [0, bound - 1], distinct from i
	'''
	value = randint(0, bound - 1)
	while (value == i):
		value = randint(0, bound - 1)
	return value	

class Cuckoo():

	def __init__(self, hash_seed):
		self.number_of_bins = 2 ** OUTPUT_BITS
		self.recursion_depth = int(8 * math.log(self.number_of_bins) / math.log(2))
		self.data_structure = [None for j in range(self.number_of_bins)]
		self.insert_index = randint(0, NUM_OF_HASHES - 1)
		self.depth = 0
		self.FAIL = 0

		self.hash_seed = hash_seed	

	def insert(self, item): #item is an integer
		current_location = location( self.hash_seed[self.insert_index], item)
		current_item = self.data_structure[ current_location]
		self.data_structure[ current_location ] = left_and_index(item, self.insert_index)

		if (current_item == None):
			self.insert_index = randint(0, NUM_OF_HASHES - 1)	
			self.depth = 0	
		else:
			unwanted_index = extract_index(current_item)
			self.insert_index = rand_point(NUM_OF_HASHES, unwanted_index)	
			if (self.depth < self.recursion_depth):
				self.depth +=1
				jumping_item = reconstruct_item(current_item, current_location, self.hash_seed[unwanted_index])
				self.insert(jumping_item)		
			else:
				self.FAIL = 1	
