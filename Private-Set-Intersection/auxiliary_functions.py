from math import log2
import numpy as np
from constants import *

def int2base(n, b):
    '''
    :param n: an integer
    :param b: a base
    :return: an array of coefficients from the base decomposition of an integer n with coeff[i] being the coeff of b ** i
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
    :param: window: a matrix of integers as powers of y; in the protocol is the matrix with entries window[i][j] = [y ** i * base ** j]
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


def windowing(y, bound, modulus):
    '''
    :param: y: an integer
    :param bound: an integer
    :param modulus: a modulus integer
    :return: a matrix associated to y, where we put y ** (i+1)*base ** j mod modulus in the (i,j) entry, as long as the exponent of y is smaller than some bound
    '''
    windowed_y = [[None for j in range(LOG_B_ELL)] for i in range(BASE-1)]
    for j in range(LOG_B_ELL):
        for i in range(BASE-1):
            if ((i+1) * BASE ** j - 1 < bound):
                windowed_y[i][j] = pow(y, (i+1) * BASE ** j, modulus)
    return windowed_y


def coeffs_from_roots(roots, modulus):
    '''
    :param roots: an array of integers
    :param modulus: an integer
    :return: coefficients of a polynomial whose roots are roots modulo modulus
    '''
    coefficients = np.array(1, dtype=np.int64)
    for r in roots:
        coefficients = np.convolve(coefficients, [1, -r]) % modulus
    return coefficients

def read_file_return_list(filename):
    with open(filename) as f:
        return [int(line.rstrip()) for line in f]
    
def read_file_return_list1(filename):
    lines = []
    with open(filename) as f:
        for line in f:
            lines.append(int(line.rstrip()))
    return lines

def read_file_return_list2(filename):
    lines = []
    with open(filename) as f:
        while (line := f.readline().rstrip()):
            lines.append(int(line.rstrip()))
    return lines