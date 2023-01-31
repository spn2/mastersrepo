from math import log2
from multiprocessing import Pool
import numpy as np

from constants import *
from oprf_constants import NUM_OF_PROCESSES

def int2base(n, b):
    '''
    :param n: an integer
    :param b: a base
    :return: an array of coefficients from the base decomposition of an
             integer n with coeff[i] being the coeff of b ** i
    '''
    if n < b:
        return [n]
    else:
        return [n % b] + int2base(n // b, b)  

# We need len(powers_vec) <= 2 ** HE.depth
def low_depth_multiplication(vector):
    '''
    :param: vector: a vector of integers 
    :return: an integer representing the multiplication of all the integers from vector
    '''
    L = len(vector)
    if L == 1:
        return vector[0]
    if L == 2:
        return(vector[0] * vector[1])
    else:    
        if (L % 2 == 1):
            vec = []
            for i in range(int(L / 2)):
                vec.append(vector[2 * i] * vector[2 * i + 1])
            vec.append(vector[L-1])
            return low_depth_multiplication(vec)
        else:
            vec = []
            for i in range(int(L / 2)):
                vec.append(vector[2 * i] * vector[2 * i + 1])
            return low_depth_multiplication(vec)

def power_reconstruct(window, exponent):
    '''
    :param: window: a matrix of integers as powers of y; in the protocol is the matrix
                    with entries window[i][j] = [y ** i * base ** j]
    :param: exponent: an integer, will be an exponent <= logB_ell
    :return: y ** exponent
    '''
    e_base_coef = int2base(exponent, BASE)
    necessary_powers = [] #len(necessary_powers) <= 2 ** HE.depth 
    j = 0
    for x in e_base_coef:
        if x >= 1:
            necessary_powers.append(window[x - 1][j])
        j = j + 1
    return low_depth_multiplication(necessary_powers)


def windowing(y, bound, mod):
    '''
    :param: y: an integer
    :param bound: an integer
    :param mod: a modulus integer
    :return: a matrix associated to y, where we put y ** (i+1)*base ** j modulus mod
             in the (i,j) entry, as long as the exponent of y is smaller than some bound
    '''
    windowed_y = [[None for j in range(LOG_B_ELL)] for i in range(BASE-1)]
    for j in range(LOG_B_ELL):
        for i in range(BASE-1):
            if ((i+1) * BASE ** j - 1 < bound):
                windowed_y[i][j] = pow(y, (i+1) * BASE ** j, mod)
    return windowed_y


def compute_coefficients_from_roots(roots, mod):
    '''
    Takes a set of roots and computes the coefficients (modulo mod) of the
    polynomial that vanishes at each root in roots.

    :param roots: an array of integers
    :param mod: an integer
    :return: integer coefficients of a polynomial whose roots are roots modulo mod
    '''
    # return [np.convolve(np.array(1, dtype=np.int64), [1, -r]) % mod for r in roots]
    for r in roots:
        coefficients = np.convolve(np.array(1, dtype=np.int64), [1, -r]) % mod
    return coefficients.tolist()
# 


def read_file_return_list(filename):
    """
    :param filename: filename to process
    :return: list of lines from file with newlines stripped off and everything converted to int
    """
    with open(filename) as f:
        return [int(line.rstrip()) for line in f]

def split_list_into_parts(items, n):
    """
    Example: split_list_into_parts([0,1,2,3,4,5,6,7,8,9], 3) is split into [0,1,2], [3,4,5], [6,7,8], [9]

    :param items: object of items to split
    :param n: the number of lists for the items to be sent into
    :return: list of n lists containing the objects from items 
    """

    split_lists = []

    q = int(len(items)/n)

    for i in range(0, int(len(items)/q)):
        split_lists.append(items[i*q:(i+1)*q])

    # put remainder in own list
    if len(items[q*(1+i):]) > 0:
        split_lists.append(items[q*(1+i):])

    return split_lists

def unpack_list_of_lists(lists):
    """
    :param lists: list of lists to unpack
    :return: single list containing all the elements from the lists in lists
    """
    unpacked = []
    for l in lists:
        unpacked += l
    return unpacked