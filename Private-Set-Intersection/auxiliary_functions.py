import pickle
from random import randint
import socket
from typing import Any, List, Optional, Tuple, TypeVar

from constants import *

Multiplicable = TypeVar("Multiplicable", bound="MultiplicableBase")

class MultiplicableBase:
    def __mul__(self, other: "Multiplicable") -> "Multiplicable":
        pass

def get_random_distinct_integer(bound: int, i: int) -> int:
    '''
    Generates a uniform random integer in the range [0, bound-1] that is distinct from i.

    :param bound: an integer representing the upper bound of the range
    :param i: an integer less than bound
    :return: a uniformly random integer in the range [0, bound-1] that is distinct from i.
    '''

    value = randint(0, bound - 1)
    while (value == i):
        value = randint(0, bound - 1)
        
    return value

def split_int_into_base_digits(n: int, b: int) -> List[int]:
    '''
    Converts an integer n to a list representing its digits in another base b.
    For example, convert_integer_to_digits(10, 2) returns [0,1,0,1]

    :param n: an integer
    :param b: a base
    :return: a list representing n's digits in base b, with the highest power
             at the end of the list
    '''

    digits = []
    while n > 0:
        digits.append(n % b)
        n //= b

    return digits

def fast_multiply_items(arr: List[Multiplicable]) -> Multiplicable:
    '''
    Divide and conquer for faster multiplication. Assumes the items in
    arr are multiplicable. (len(powers_vec) <= 2 ** HE.depth)

    :param: arr: a list of multiplicable objects 
    :return: the result of multiplying all the objects in arr
    '''

    if len(arr) == 1:
        return arr[0]

    if len(arr) == 2:
        return(arr[0] * arr[1])

    halfarr = [arr[i] * arr[i+1] for i in range(0, len(arr)-1, 2)]

    if len(arr) % 2 == 1: # in case of odd # of items
        halfarr.append(arr[-1])

    return fast_multiply_items(halfarr)


def reconstruct_power(matrix: List[List[int]], exponent: int) -> int:
    '''
    Reconstruct an exponent of y (exponent) given a matrix of precomputed powers of y (matrix).

    :param: matrix:  powers of y with the form matrix[i][j] = [y ** i * base ** j]
    :param: exponent: an integer <= LOG_B_ELL
    :return: y ** exponent
    '''

    # compute the exponent's digits in BASE
    exponent_digits = split_int_into_base_digits(exponent, BASE)

    # select needed powers from window to compute y ** exponent.
    needed_powers = [matrix[x-1][j] for j, x in enumerate(exponent_digits) if x >= 1]

    return fast_multiply_items(needed_powers)


def windowing(y: int, bound: int, mod: int) -> List[List[Optional[int]]]:
    """
    Windowing technique to efficiently compute modular exponentiation of an integer y.
    Returns a matrix of y raised to powers of BASE with exponents up to a specified bound (modulo mod).

    :param y: an integer we want powers of
    :param bound: an integer that bounds the exponents of y
    :param mod: an integer; the modulus
    :return: a matrix of y raised to powers of BASE with exponents
             up to a specified bound (modulo mod)
    """
    windowed_y = []
    for i in range(1, BASE):
        row = []
        for j in range(LOG_B_ELL):
            exp = i * (BASE ** j)
            if exp <= bound:
                row.append(pow(y, exp, mod))
            else:
                row.append(None)
        windowed_y.append(row)

    return windowed_y


def compute_coefficients_from_roots(roots: List[int], mod: int) -> List[int]:
    '''
    Takes a set of roots and computes the coefficients (modulo mod) of the
    polynomial that vanishes at each root in roots.

    :param roots: an array of integers
    :param mod: an integer
    :return: integer coefficients of a polynomial whose roots are roots modulo mod
    '''

    coefficients = [1]

    for r in roots:
        # pre-allocate a new coefficients list
        new_coeffs = [0] * (len(coefficients) + 1)
        for i, c in enumerate(coefficients):
            # compute convolution
            new_coeffs[i] += c
            new_coeffs[i+1] -= r * c
        # take coefficients modulo mod
        for i in range(len(new_coeffs)):
            new_coeffs[i] %= mod
        coefficients = new_coeffs

    return coefficients


def read_file_return_list_of_int(filename: str) -> List[int]:
    """
    :param filename: filename to process
    :return: list of lines from file with newlines stripped off and everything converted to int
    """

    with open(filename) as f:
        return [int(line.rstrip()) for line in f]

def split_list_into_parts(items: List[Any], n: int) -> List[List[Any]]:
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

def unpack_list_of_lists(lists: List[List]) -> List:
    """
    :param lists: list of lists to unpack
    :return: single list containing all the elements from the lists in lists
    """

    unpacked = []

    for l in lists:
        unpacked += l

    return unpacked


# functions for sending/receiving data for the online phase

def serialize_and_send_data(socketobj: socket.socket, data: object = None, filename: str = "") -> int:
    """
    Sends data to the other part of the socketobj.

    :param clientsocket: socket object with a connection to the other party
    :param data: data to send
    :param filename: name of file where data is found (used if data is None)
    :return: length of data sent
    """

    # if no data was provided, try to open the filename where data should be
    if data is None:
        try:
            unloaded_set = open(filename, "rb")
            data = pickle.load(unloaded_set)
        except Exception as e:
            print(e)
    
    serialized_data = pickle.dumps(data, protocol=None)

    # send length of data to the other party first
    length_of_sent_data = send_outgoing_data_length(socketobj, serialized_data)
    # send the actual data
    socketobj.sendall(serialized_data)

    return length_of_sent_data


def get_and_deserialize_data(socketobj: socket.socket) -> Tuple[Any, int]:
    """
    Receives data from the other side of the socket connection.
    Deserializes the data before returning it.
    
    :param clientsocket: client's socket object
    :returns:
        deserialized_data: deserialized data
        serialized_data_length: length of the serialized data that was received
    """

    expected_data_length = get_incoming_data_length(socketobj)

    serialized_data = b""

    while len(serialized_data) < expected_data_length:
        data = socketobj.recv(65536)
        if not data: break
        serialized_data += data

    serialized_data_length = len(serialized_data)
    deserialized_data = pickle.loads(serialized_data)

    return deserialized_data, serialized_data_length

def send_outgoing_data_length(socketobj: socket.socket, data: bytes) -> int:
    """
    Sends the length of the outgoing data to the other side of the socketobj. 
    Used before the one party sends a larger amount of data. The data will be
    padded till it reaches 10 bytes before it is sent. I.e. if client sends
    6 items, it will send '6         ' to the server via this function first.

    :param clientsocket: socket object with a connection to the other party
    :param data: data that party wants to send (client only sends size here)
    :return: the length of the data the party will send
    """

    # prepare size, pad with spaces to reach 10 bytes, send data, return the length
    msg_length = len(data)
    padded_msg_length = str(msg_length) + ' ' * (10 - len(str(msg_length)))
    socketobj.sendall((padded_msg_length).encode())

    return msg_length

def get_incoming_data_length(clientsocket: socket.socket) -> int:
    """
    Receives the length of data to receive from the other side of socketobj.
    Used before the other party sends a larger amount of data.

    :param clientsocket: socket object with a connection to the other party
    :return: the length of the data that the other party will send
    """

    return int(clientsocket.recv(10).decode().strip())