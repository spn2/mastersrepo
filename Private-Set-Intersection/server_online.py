from Pyfhel import Pyfhel, PyCtxt
import socket
import pickle
import numpy as np
from math import log2

from constants import *
from auxiliary_functions import power_reconstruct
from oprf import server_prf_online_parallel

from time import time

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv.bind(('localhost', 4470))
serv.listen(1)

g = open('server_preprocessed', 'rb')
poly_coeffs = pickle.load(g)

# For the online phase of the server, we need to use the columns of the preprocessed database
transposed_poly_coeffs = np.transpose(poly_coeffs).tolist()

for i in range(1):
    conn, addr = serv.accept()
    L = conn.recv(10).decode().strip()
    L = int(L, 10)
    # OPRF layer: the server receives the encoded set elements as curve points
    encoded_client_set_serialized = b""
    while len(encoded_client_set_serialized) < L:
        data = conn.recv(4096)
        if not data: break
        encoded_client_set_serialized += data   
    encoded_client_set = pickle.loads(encoded_client_set_serialized)
    t0 = time()
    # The server computes (parallel computation) the online part of the OPRF protocol, using its own secret key
    PRFed_encoded_client_set = server_prf_online_parallel(OPRF_SERVER_KEY, encoded_client_set)
    PRFed_encoded_client_set_serialized = pickle.dumps(PRFed_encoded_client_set, protocol=None)
    L = len(PRFed_encoded_client_set_serialized)
    sL = str(L) + ' ' * (10 - len(str(L))) #pad len to 10 bytes

    conn.sendall((sL).encode())
    conn.sendall(PRFed_encoded_client_set_serialized)    
    print(' * OPRF layer done!')
    t1 = time()
    L = conn.recv(10).decode().strip()
    L = int(L, 10)

    # The server receives bytes that represent the public HE context and the query ciphertext
    final_data = b""
    while len(final_data) < L:
        data = conn.recv(4096)
        if not data: break
        final_data += data

    t2 = time()    
    # Here we recover the context and ciphertext received from the received bytes
    # message_to_be_sent = [s_context, s_public_key, s_relin_key, s_rotate_key, enc_query_serialized]
    received_data = pickle.loads(final_data)

    # HEctx = received_data[0]
    # clientPubKey = received_data[1]
    # clientRelKey = received_data[2]
    # clientRotKey = received_data[3]
    # received_enc_query_serialized = received_data[4]




    print(type(received_data))
    
    HE_server = Pyfhel()
    HE_server.from_bytes_context(received_data[0])
    HE_server.from_bytes_public_key(received_data[1])
    HE_server.from_bytes_relin_key(received_data[2])
    HE_server.from_bytes_rotate_key(received_data[3])
    # print("###################")
    # print(len(received_data[4]))
    # print(type(received_data[4]))
    # print("@@@@@@@@@@@@@@@")
    # print(len(received_data[4][0]))
    # print(len(received_data[4][1]))
    # print(len(received_data[4][2]))
    # print("###################")
    # cx = PyCtxt(pyfhel=HE_server, bytestring=received_data[4])
    received_enc_query_serialized = received_data[4]
    
    # OLD:
    # srv_context = ts.context_from(received_data[0])




    received_enc_query = [[None for j in range(LOG_B_ELL)] for i in range(BASE - 1)]
    for i in range(BASE - 1):
        for j in range(LOG_B_ELL):
            if ((i + 1) * BASE ** j - 1 < MINIBIN_CAP):
                received_enc_query[i][j] = PyCtxt(pyfhel=HE_server, bytestring=received_enc_query_serialized[i][j])
                # OLD:
                # received_enc_query[i][j] = ts.bfv_vector_from(srv_context, received_enc_query_serialized[i][j])
    
    # Here we recover all the encrypted powers Enc(y), Enc(y^2), Enc(y^3) ..., Enc(y^{minibin_capacity}), from the encrypted windowing of y.
    # These are needed to compute the polynomial of degree minibin_capacity
    all_powers = [None for i in range(MINIBIN_CAP)]
    for i in range(BASE - 1):
        for j in range(LOG_B_ELL):
            if ((i + 1) * BASE ** j - 1 < MINIBIN_CAP):
                all_powers[(i + 1) * BASE ** j - 1] = received_enc_query[i][j]

    for k in range(MINIBIN_CAP):
        if all_powers[k] == None:
            all_powers[k] = power_reconstruct(received_enc_query, k + 1)
    all_powers = all_powers[::-1]

    # Server sends alpha ciphertexts, obtained from performing dot_product between the polynomial coefficients from the preprocessed server database and all the powers Enc(y), ..., Enc(y^{minibin_capacity})
    srv_answer = []
    for i in range(ALPHA):
        # the rows with index multiple of (B/alpha+1) have only 1's
        dot_product = all_powers[0]
        for j in range(1, MINIBIN_CAP):
            dot_product = dot_product + transposed_poly_coeffs[(MINIBIN_CAP + 1) * i + j] * all_powers[j]
        dot_product = dot_product + transposed_poly_coeffs[(MINIBIN_CAP + 1) * i + MINIBIN_CAP]
        srv_answer.append(dot_product.to_bytes())

    # The answer to be sent to the client is prepared
    response_to_be_sent = pickle.dumps(srv_answer, protocol=None)
    t3 = time()
    L = len(response_to_be_sent)
    sL = str(L) + ' ' * (10 - len(str(L))) #pad len to 10 bytes

    conn.sendall((sL).encode())
    conn.sendall(response_to_be_sent)

    # Close the connection
    print("Client disconnected \n")
    print('Server ONLINE computation time {:.2f}s'.format(t1 - t0 + t3 - t2))

    conn.close()
