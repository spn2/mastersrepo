import pickle
import socket
from time import time

import numpy as np
from Pyfhel import Pyfhel, PyCtxt

from auxiliary_functions import get_and_deserialize_data, power_reconstruct, serialize_and_send_data
from constants import *
from oprf import server_prf_online_parallel
from oprf_constants import OPRF_SERVER_KEY


def main():
    # ready socket object and listen for incoming connection
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.bind(('localhost', 4470))
    serv.listen(1)

    # accept connection from client
    conn, _ = serv.accept()


    # OPRF layer: the server receives the encoded set elements as curve points
    encoded_client_set, length_of_data_received_1 = get_and_deserialize_data(conn)

    # The server computes (parallel computation) the online part of the OPRF protocol, using its own secret key
    PRFed_encoded_client_set = server_prf_online_parallel(encoded_client_set, OPRF_SERVER_KEY)

    # send the resulting PRF-ed client set
    length_of_data_sent_1 = serialize_and_send_data(conn, PRFed_encoded_client_set)
 
    # Here we recover the context and ciphertext received from the received bytes
    # message_to_be_sent = [s_context, s_public_key, s_relin_key, s_rotate_key, enc_query_serialized]
    received_data, length_of_data_received_2 = get_and_deserialize_data(conn)

    HE_server, received_enc_query_serialized = server_FHE_setup(received_data)

    encrypted_query = reconstruct_encrypted_query(HE_server, received_enc_query_serialized)

    # Here we recover all the encrypted powers Enc(y), Enc(y^2), Enc(y^3) ..., Enc(y^{minibin_capacity}), from the encrypted windowing of y.
    # These are needed to compute the polynomial of degree minibin_capacity
    all_powers = recover_encrypted_powers(encrypted_query)

    srv_answer = prepare_server_response(all_powers, "server_preprocessed")

    # The answer to be sent to the client is prepared
    length_of_data_sent_2 = serialize_and_send_data(conn, data=srv_answer)

    # Close the connection
    print("Client disconnected \n")
    # print('Server ONLINE computation time {:.2f}s'.format(t1 - t0 + t3 - t2))

    conn.close()

def server_FHE_setup(received_data):
    """
    get client blabla
    """
    HE_server = Pyfhel()
    HE_server.from_bytes_context(received_data[0])
    HE_server.from_bytes_public_key(received_data[1])
    HE_server.from_bytes_relin_key(received_data[2])
    HE_server.from_bytes_rotate_key(received_data[3])

    received_enc_query_serialized = received_data[4]

    return HE_server, received_enc_query_serialized

def reconstruct_encrypted_query(pyfhelobj, serialized_query):
    """
    Given the client serialized (not via pickle) encrypted query, deserialize it.

    :param pyfhelobj: the Pyfhel object
    :param serialized_query: client serialized encrypted query
    :return: deserialized query
    """

    deserialized_query = [[None for j in range(LOG_B_ELL)] for i in range(BASE - 1)]

    for i in range(BASE - 1):
        for j in range(LOG_B_ELL):
            if ((i + 1) * BASE ** j - 1 < MINIBIN_CAP):
                deserialized_query[i][j] = PyCtxt(pyfhel=pyfhelobj, bytestring=serialized_query[i][j])

    return deserialized_query

def recover_encrypted_powers(encrypted_query):
    """
    Recovers all the encrypted powers Encrypted(y), Encrypted(y^2), ..., Encrypted(y^{minibin_capacity}),
    using the encrypted windowing of y.
    "needed to compute the polynomial of degree minibin_capacity"

    :param encrypted_query: deserialized query from client
    :return: all the encrypted powers Enc(y), Enc(y^2), Enc(y^3) ..., Enc(y^{minibin_capacity})
    """

    all_powers = [None for i in range(MINIBIN_CAP)]

    for i in range(BASE - 1):
        for j in range(LOG_B_ELL):
            if ((i + 1) * BASE ** j - 1 < MINIBIN_CAP):
                all_powers[(i + 1) * BASE ** j - 1] = encrypted_query[i][j]

    for k in range(MINIBIN_CAP):
        if all_powers[k] == None:
            all_powers[k] = power_reconstruct(encrypted_query, k + 1)
    all_powers = all_powers[::-1]

    return all_powers

def prepare_server_response(all_powers, server_preprocessed_filename):
    """
    
    """
    g = open(server_preprocessed_filename, 'rb')
    poly_coeffs = pickle.load(g)

    # For the online phase of the server, we need to use the columns of the preprocessed database
    transposed_poly_coeffs = np.transpose(poly_coeffs).tolist()

    # Server sends alpha ciphertexts, obtained from performing dot_product between the polynomial coefficients from the preprocessed server database and all the powers Enc(y), ..., Enc(y^{minibin_capacity})
    srv_answer = []
    for i in range(ALPHA):
        # the rows with index multiple of (B/alpha+1) have only 1's
        dot_product = all_powers[0]
        for j in range(1, MINIBIN_CAP):
            dot_product = dot_product + transposed_poly_coeffs[(MINIBIN_CAP + 1) * i + j] * all_powers[j]
        dot_product = dot_product + transposed_poly_coeffs[(MINIBIN_CAP + 1) * i + MINIBIN_CAP]
        srv_answer.append(dot_product.to_bytes())

    return srv_answer

if __name__ == "__main__":
    main()
