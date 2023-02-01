from Pyfhel import Pyfhel, PyCtxt
from time import time
import socket
import pickle
from math import log2
from constants import *
from cuckoo_hash import reconstruct_item, Cuckoo
from auxiliary_functions import windowing
from oprf import client_prf_online_parallel
from oprf_constants import GENERATOR_ORDER, OPRF_CLIENT_KEY

dummy_msg_client = 2 ** (SIGMA_MAX - OUTPUT_BITS + LOG_NO_HASHES)

def client_FHE_setup(polynomial_modulus, coefficient_modulus):
    """
    Setting the public and private contexts for the BFV Homorphic Encryption scheme via Pyfhel.

    :param polynomial_modulus: integer representing the polynomial modulus
    :param coefficient_modulus: integer representing the polynomial coefficient modulus
    :return: the Pyfhel object, context, public key, relinearization key, and rotation key in a 5-tuple
             (the last 4 as bytes for sending to server).
    """
    HEctx = Pyfhel()
    HEctx.contextGen(scheme="bfv", n=polynomial_modulus, t=coefficient_modulus)
    HEctx.keyGen()
    HEctx.relinKeyGen()
    HEctx.rotateKeyGen()

    s_context    = HEctx.to_bytes_context()
    s_public_key = HEctx.to_bytes_public_key()
    s_relin_key  = HEctx.to_bytes_relin_key()
    s_rotate_key = HEctx.to_bytes_rotate_key()

    return (HEctx, s_context, s_public_key, s_relin_key, s_rotate_key)

def send_embedded_client_items_to_server(clientsocket, preprocessed_file):
    """
    Opens the client's preprocessed set, serializes it and sends it to the server.

    :param clientsocket: client's socket object
    :preprocessed_file: filename of client's preprocessed dataset (output of client_offline.py)
    """
    # We prepare the partially OPRF processed database to be sent to the server
    pickle_off = open(preprocessed_file, "rb")
    encoded_client_set = pickle.load(pickle_off)
    encoded_client_set_serialized = pickle.dumps(encoded_client_set, protocol=None)


    L = len(encoded_client_set_serialized)
    sL = str(L) + ' ' * (10 - len(str(L)))
    client_to_server_communiation_oprf = L #in bytes
    # The length of the message is sent first
    clientsocket.sendall((sL).encode())
    clientsocket.sendall(encoded_client_set_serialized)

    return client_to_server_communiation_oprf

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 4470))

HEctx, s_context, s_public_key, s_relin_key, s_rotate_key = client_FHE_setup(POLY_MOD, PLAIN_MOD)



client_to_server_communiation_oprf = send_embedded_client_items_to_server(client, "client_preprocessed")


# # We prepare the partially OPRF processed database to be sent to the server
# pickle_off = open("client_preprocessed", "rb")
# encoded_client_set = pickle.load(pickle_off)
# encoded_client_set_serialized = pickle.dumps(encoded_client_set, protocol=None)

# L = len(encoded_client_set_serialized)
# sL = str(L) + ' ' * (10 - len(str(L)))
# client_to_server_communiation_oprf = L #in bytes
# # The length of the message is sent first
# client.sendall((sL).encode())
# client.sendall(encoded_client_set_serialized)











L = client.recv(10).decode().strip()
L = int(L, 10)



PRFed_encoded_client_set_serialized = b""
while len(PRFed_encoded_client_set_serialized) < L:
    data = client.recv(4096)
    if not data: break
    PRFed_encoded_client_set_serialized += data   
PRFed_encoded_client_set = pickle.loads(PRFed_encoded_client_set_serialized)
t0 = time()
server_to_client_communication_oprf = len(PRFed_encoded_client_set_serialized)

# We finalize the OPRF processing by applying the inverse of the secret key, oprf_client_key
key_inverse = pow(OPRF_CLIENT_KEY, -1, GENERATOR_ORDER)
PRFed_client_set = client_prf_online_parallel(PRFed_encoded_client_set, key_inverse)
print(' * OPRF protocol done!')

# Each PRFed item from the client set is mapped to a Cuckoo hash table
CH = Cuckoo(HASH_SEEDS)
for item in PRFed_client_set:
    CH.insert(item)

# We padd the Cuckoo vector with dummy messages
for i in range(CH.number_of_bins):
    if (CH.data_structure[i] == None):
        CH.data_structure[i] = dummy_msg_client

# We apply the windowing procedure for each item from the Cuckoo structure
windowed_items = []
for item in CH.data_structure:
    windowed_items.append(windowing(item, MINIBIN_CAP, PLAIN_MOD))

plain_query = [None for k in range(len(windowed_items))]
enc_query = [[None for j in range(LOG_B_ELL)] for i in range(1, BASE)]

# We create the <<batched>> query to be sent to the server
# By our choice of parameters, number of bins = poly modulus degree (m/N =1), so we get (base - 1) * logB_ell ciphertexts
for j in range(LOG_B_ELL):
    for i in range(BASE - 1):
        if ((i + 1) * BASE ** j - 1 < MINIBIN_CAP):
            for k in range(len(windowed_items)):
                plain_query[k] = windowed_items[k][i][j]
            enc_query[i][j] = HEctx.encrypt(plain_query)

enc_query_serialized = [[None for j in range(LOG_B_ELL)] for i in range(1, BASE)]
for j in range(LOG_B_ELL):
    for i in range(BASE - 1):
        if ((i + 1) * BASE ** j - 1 < MINIBIN_CAP):
            enc_query_serialized[i][j] = enc_query[i][j].to_bytes()





# context_serialized = public_context.serialize()
# message_to_be_sent = [context_serialized, enc_query_serialized]

message_to_be_sent = [s_context, s_public_key, s_relin_key, s_rotate_key, enc_query_serialized]


message_to_be_sent_serialized = pickle.dumps(message_to_be_sent, protocol=None)
t1 = time()
L = len(message_to_be_sent_serialized)
sL = str(L) + ' ' * (10 - len(str(L)))
client_to_server_communiation_query = L 
#the lenght of the message is sent first
client.sendall((sL).encode())
print(" * Sending the context and ciphertext to the server....")
# Now we send the message to the server
client.sendall(message_to_be_sent_serialized)

print(" * Waiting for the servers's answer...")

# The answer obtained from the server:
L = client.recv(10).decode().strip()
L = int(L, 10)
answer = b""
while len(answer) < L:
    data = client.recv(4096)
    if not data: break
    answer += data
t2 = time()
server_to_client_query_response = len(answer) #bytes
# Here is the vector of decryptions of the answer
ciphertexts = pickle.loads(answer)
decryptions = []
for ct in ciphertexts:
    decryptions.append(PyCtxt(bytestring=ct, pyfhel=HEctx, scheme="bfv").decrypt())

recover_CH_structure = []
for matrix in windowed_items:
    recover_CH_structure.append(matrix[0][0])

count = [0] * ALPHA

g = open('client_set', 'r')
client_set_entries = g.readlines()
g.close()
client_intersection = []
for j in range(ALPHA):
    for i in range(POLY_MOD):
        if decryptions[j][i] == 0:
            count[j] = count[j] + 1

            # The index i is the location of the element in the intersection
            # Here we recover this element from the Cuckoo hash structure
            PRFed_common_element = reconstruct_item(recover_CH_structure[i], i, HASH_SEEDS[recover_CH_structure[i] % (2 ** LOG_NO_HASHES)])
            index = PRFed_client_set.index(PRFed_common_element)
            client_intersection.append(int(client_set_entries[index][:-1]))

h = open('intersection', 'r')
real_intersection = [int(line[:-1]) for line in h]
h.close()
t3 = time()
print('\n Intersection recovered correctly: {}'.format(set(client_intersection) == set(real_intersection)))
print("Disconnecting...\n")
print('  Client ONLINE computation time {:.2f}s'.format(t1 - t0 + t3 - t2))
print('  Communication size:')
print('    ~ Client --> Server:  {:.2f} MB'.format((client_to_server_communiation_oprf + client_to_server_communiation_query )/ 2 ** 20))
print('    ~ Server --> Client:  {:.2f} MB'.format((server_to_client_communication_oprf + server_to_client_query_response )/ 2 ** 20))
client.close()


