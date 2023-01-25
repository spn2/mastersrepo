from multiprocessing import Pool

from fastecdsa.point import Point

from auxiliary_functions import split_list_into_parts
from oprf_constants import *

def server_prf_offline(vector_of_items_and_point):
	vector_of_items = vector_of_items_and_point[0]
	point = vector_of_items_and_point[1]
	vector_of_multiples = [item * point for item in vector_of_items]
	return [(Q.x >> LOG_P - SIGMA_MAX - 10) & MASK for Q in vector_of_multiples]

def server_prf_offline_parallel(vector_of_items, point):
	'''
	:param vector_of_items: a vector of integers
	:param point: a point on elliptic curve (it will be key * G)
	:return: a sigma_max bits integer from the first coordinate of item * point (this will be the same as item * key * G)
	'''

	items_per_process = int(len(vector_of_items) / NUM_OF_PROCESSES)
	# list of lists where each list is a set of items to be handled by a process
	process_items = [vector_of_items[i * items_per_process: (i+1) * items_per_process] for i in range(NUM_OF_PROCESSES)]
	
	if len(vector_of_items) % NUM_OF_PROCESSES != 0:
		process_items.append(vector_of_items[NUM_OF_PROCESSES * items_per_process: NUM_OF_PROCESSES * items_per_process + (len(vector_of_items) % NUM_OF_PROCESSES)])
	
	inputs_and_point = [(input_vec, point) for input_vec in process_items]
	outputs = []
	with Pool(NUM_OF_PROCESSES) as p:
		outputs = p.map(server_prf_offline, inputs_and_point)	
	final_output = []
	for output_vector in outputs:
		final_output = final_output + output_vector
	return final_output		

def server_prf_online(keyed_vector_of_points): #used as a subroutine in server_prf_online_paralel
	key = keyed_vector_of_points[0]
	vector_of_points = keyed_vector_of_points[1]
	vector_of_multiples = [key * PP for PP in vector_of_points]
	return [[Q.x, Q.y] for Q in vector_of_multiples]


def server_prf_online_parallel(key, vector_of_pairs):
	'''
	:param key: an integer
	:param vector_of_pairs: vector of coordinates of some points P on the elliptic curve
	:return: vector of coordinates of points key * P on the elliptic curve
	'''
	vector_of_points = [Point(P[0], P[1], curve=CURVE) for P in vector_of_pairs]
	division = int(len(vector_of_points) / NUM_OF_PROCESSES)
	inputs = [vector_of_points[i * division: (i+1) * division] for i in range(NUM_OF_PROCESSES)]
	if len(vector_of_points) % NUM_OF_PROCESSES != 0:
		inputs.append(vector_of_points[NUM_OF_PROCESSES * division: NUM_OF_PROCESSES * division + (len(vector_of_points) % NUM_OF_PROCESSES)])
	keyed_inputs = [(key, _) for _ in inputs]
	outputs = []
	with Pool(NUM_OF_PROCESSES) as p:
		outputs = p.map(server_prf_online, keyed_inputs)
	final_output = []
	for output_vector in outputs:
		final_output = final_output + output_vector
	return final_output

def client_prf_offline(item, point):
	'''
	:param item: an integer
	:param point: a point on elliptic curve (ex. in the protocol point = key * G)
	:return: coordinates of item * point (ex. in the protocol it computes key * item * G)
	'''
	P = item * point
	x_item = P.x
	y_item = P.y
	return (x_item, y_item)

def client_prf_online(keyed_vector_of_pairs):
	key_inverse = keyed_vector_of_pairs[0]
	vector_of_pairs = keyed_vector_of_pairs[1]
	vector_of_points = [Point(pair[0],pair[1], curve=CURVE) for pair in vector_of_pairs]
	vector_key_inverse_points = [key_inverse * PP for PP in vector_of_points]
	return [(Q.x >> LOG_P - SIGMA_MAX - 10) & MASK for Q in vector_key_inverse_points]

def client_prf_online_parallel(key_inverse, vector_of_pairs):
	vector_of_pairs = vector_of_pairs
	division = int(len(vector_of_pairs) / NUM_OF_PROCESSES)
	inputs = [vector_of_pairs[i * division: (i+1) * division] for i in range(NUM_OF_PROCESSES)]
	if len(vector_of_pairs) % NUM_OF_PROCESSES != 0:
		inputs.append(vector_of_pairs[NUM_OF_PROCESSES * division: NUM_OF_PROCESSES * division + (len(vector_of_pairs) % NUM_OF_PROCESSES)])
	keyed_inputs = [(key_inverse, _) for _ in inputs]		
	outputs = []
	with Pool(NUM_OF_PROCESSES) as p:
		outputs = p.map(client_prf_online, keyed_inputs)
	final_output = []
	for output_vector in outputs:
		final_output = final_output + output_vector
	return final_output

