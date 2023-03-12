from multiprocessing import Pool

from fastecdsa.point import Point

from auxiliary_functions import split_list_into_parts, unpack_list_of_lists
from oprf_constants import *

def server_prf_offline(list_of_items_and_point):
    """
    Takes a list of items and processes them by multiplying each item with a point
    from an elliptic curve (EC). This point will be equal to the server's key * the EC's generator.
    SIGMA_MAX bits are taken from the first coordinate of the resulting
    operation on each item, appended to a list, then returned.

    The first coordinate of list_of_items_and_point should be the list of items, whereas
    the second should be the point on the EC.

    :param list_of_items_and_point: list of server items and a point (key * generator)
                                      on the EC
    :return: server items multiplied by the point (key * generator), with SIGMA_MAX
             bits taken from the first coordinate
    """

    items_time_point = multiply_items_by_point(list_of_items_and_point)

    return [(Q.x >> LOG_P - SIGMA_MAX - 10) & MASK for Q in items_time_point]


def server_prf_offline_parallel(item_list, point):
    '''
    Takes a list of items as input, then splits them into NUM_OF_PROCESSES lists.
    Runs server_prf_offline in parallel on each list, then merges and returns the
    result. The point is appended along with each list as a way to send it to the
    subrotuine server_prf_offline.

    :param item_list: a list of integers
    :param point: a point on the EC (server's key (mod generator order) * generator)
    :return: a sigma_max bits integer from the first coordinate of item * point
             (this will be the same as item * key * G)
    '''

    # split up list, add point along with each of the new lists as a way to pass the point to each process
    process_items = split_list_into_parts(item_list, NUM_OF_PROCESSES)
    inputs_and_point = [(input_vec, point) for input_vec in process_items]

    return parallelize_function_on_lists(server_prf_offline, inputs_and_point)



def server_prf_online(points_with_key):
    """
    :param points_with_key: sever's PRF-encoded items (first index) and key (second index)
    :return: X and Y coordinates (as integers) of the server's PRF-encoded items multiplied
             by the key (second index of points_with_key)
    """
    multiplied_points = multiply_items_by_point(points_with_key)
    return [[P.x, P.y] for P in multiplied_points]


def server_prf_online_parallel(prf_list, key):
    '''
    :param prf_list: list consisting of the server's PRF encoded items, represented
                     as integer X and Y coordinates
    :param key: server's key on the EC CURVE (see oprf_constants.py)
    :return: list of coordinates of points key * P on the EC CURVE
    '''

    # X and Y coordinates into actual points on the EC
    list_of_points = [Point(P[0], P[1], curve=CURVE) for P in prf_list]

    # prepare lists for each process (for multiprocessing)
    inputs = split_list_into_parts(list_of_points, NUM_OF_PROCESSES)

    # add key to each list so each process has access to it
    inputs_with_key = [(_, key) for _ in inputs]

    return parallelize_function_on_lists(server_prf_online, inputs_with_key)

def client_prf_offline(set_with_point):
    """
    :param set_with_points: client's unprocessed set (first index) and client's precomputed point
                            (second index) corresponding to client's OPRF key times the EC generator
    :return: PRF-encoded list of client's items
    """
    c_set = set_with_point[0]
    p = set_with_point[1]
    return [(point.x, point.y) for point in multiply_items_by_point((c_set, p))]

def client_prf_online(key_coord_list):
    """
    :param coord_key_list: list consisting of the inverse of theclient's key plus a list of X and Y coordinates
                           (as integers) of points belonging to the EC CURVE (see oprf_constants.py) representing
                           the client's encoded items
    :return: client items multiplied by the point (key * generator), with SIGMA_MAX bits taken from the first coordinate
    """

    # reconstruct the the points on the curve based on the given X and Y coords (coord_key_list[1])
    list_of_points = [Point(pair[0],pair[1], curve=CURVE) for pair in key_coord_list[1]]

    # multiply the inverse of the key (key_coord_list[0]) with all the points
    points_time_inversekey = [key_coord_list[0] * PP for PP in list_of_points]

    # return SIGMA_MAX bits from first coordinate
    return [(Q.x >> LOG_P - SIGMA_MAX - 10) & MASK for Q in points_time_inversekey]


def client_prf_online_parallel(prf_list, inv_key):
    """
    :param inv_key: inverse of secret key
    :param prf_list: the PRF-encoded client set
    :return: inverse of the the secret key (inv_key) applied to the PRF-encoded client set
    """

    inputs = split_list_into_parts(prf_list, NUM_OF_PROCESSES)
        
    keyed_inputs = [(inv_key, _) for _ in inputs]

    return parallelize_function_on_lists(client_prf_online, keyed_inputs)

def multiply_items_by_point(items_with_point):
    """
    :param items_with_point: list with items (first index) and point (on an elliptic curve)
                             (second index)
    :return: list of items multiplied by point
    """

    item_list = items_with_point[0]
    p = items_with_point[1]

    return [item * p for item in item_list]

def parallelize_function_on_lists(func, lists):
    """"
    Uses the multiprocessing library's Pool object to run
    func on each list in lists. 

    :param func: function that takes a list as input and returns a list as output.
    :param lists: list of lists.
    :return: the aggregated lists from func as a single list. 
    """

    outputs = []
    with Pool(NUM_OF_PROCESSES) as p:
        outputs = p.map(func, lists)
    # outputs consists of a list of lists
    return unpack_list_of_lists(outputs)

