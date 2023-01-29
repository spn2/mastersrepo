from multiprocessing import Pool

from fastecdsa.point import Point

from auxiliary_functions import split_list_into_parts, unpack_list_of_lists, multiply_items_by_point, parallelize_function_on_lists
from oprf_constants import *

def server_prf_offline(vector_of_items_and_point):
    """
    Takes a list of items and processes them by multiplying each item with a point
    from an elliptic curve. This point will be equal to the server's key * the elliptic
    curve's generator. SIGMA_MAX bits are taken from the first coordinate of the resulting
    operation on each item, appended to a list, then returned.

    The first coordinate of vector_of_items_and_point should be the list of items, whereas
    the second should be the point on the elliptic curve.

    :param vector_of_items_and_point: list of server items and a point (key * generator)
                                      on the elliptic curve
    :return: server items multiplied by the point (key * generator), with SIGMA_MAX
             bits taken from the first coordinate
    """

    items_time_point = multiply_items_by_point(vector_of_items_and_point)

    return [(Q.x >> LOG_P - SIGMA_MAX - 10) & MASK for Q in items_time_point]

def server_prf_offline_parallel(vector_of_items, point):
    '''
    
    Takes a list of items as input, then splits them into NUM_OF_PROCESSES lists.
    Runs server_prf_offline in parallel on each list, then merges and returns the
    result. The point is appended along with each list as a way to send it to the
    subrotuine server_prf_offline.

    :param vector_of_items: a vector of integers
    :param point: a point on elliptic curve (it will be key * generator)
    :return: a sigma_max bits integer from the first coordinate of item * point
             (this will be the same as item * key * G)
    '''

    # split up list, add point along with each of the new lists as a way to pass the point to each process
    process_items = split_list_into_parts(vector_of_items, NUM_OF_PROCESSES)
    inputs_and_point = [(input_vec, point) for input_vec in process_items]
    
    return parallelize_function_on_lists(inputs_and_point)

def server_prf_online(keyed_vector_of_points):
    """
    #used as a subroutine in server_prf_online_paralel
    """
    multiplied_points = multiply_items_by_point(keyed_vector_of_points)
    return [[P.x, P.y] for P in multiplied_points]


def server_prf_online_parallel(key, vector_of_pairs):
    '''
    :param key: an integer
    :param vector_of_pairs: vector of coordinates of some points P on the elliptic curve
    :return: vector of coordinates of points key * P on the elliptic curve
    '''
    vector_of_points = [Point(P[0], P[1], curve=CURVE) for P in vector_of_pairs]

    inputs = split_list_into_parts(vector_of_points, NUM_OF_PROCESSES)

    keyed_inputs = [(key, _) for _ in inputs]

    return parallelize_function_on_lists(keyed_inputs)

def client_prf_online(keyed_vector_of_pairs):
    key_inverse = keyed_vector_of_pairs[0]
    vector_of_pairs = keyed_vector_of_pairs[1]
    vector_of_points = [Point(pair[0],pair[1], curve=CURVE) for pair in keyed_vector_of_pairs[1]]
    vector_key_inverse_points = [key_inverse * PP for PP in vector_of_points]
    return [(Q.x >> LOG_P - SIGMA_MAX - 10) & MASK for Q in vector_key_inverse_points]

def client_prf_online_parallel(key_inverse, vector_of_pairs):

    inputs = split_list_into_parts(vector_of_pairs, NUM_OF_PROCESSES)
        
    keyed_inputs = [(key_inverse, _) for _ in inputs]		

    return parallelize_function_on_lists(client_prf_online, keyed_inputs)

