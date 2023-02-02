from math import log2
import pickle
import socket
from time import time

from Pyfhel import Pyfhel, PyCtxt
from rich.console import Console

from auxiliary_functions import serialize_and_send_data, get_and_deserialize_data
from constants import *
from cuckoo_hash import reconstruct_item, Cuckoo
from oprf import client_prf_online_parallel
from oprf_constants import GENERATOR_ORDER, OPRF_CLIENT_KEY

dummy_msg_client = 2 ** (SIGMA_MAX - OUTPUT_BITS + LOG_NO_HASHES)

def main():

    # for prettier printing
    console = Console()

    with console.status("[bold green]Client online in progress...") as status:

        # connect to server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('localhost', 4470))

        # FHE setup
        HEctx, s_context, s_public_key, s_relin_key, s_rotate_key = client_FHE_setup(POLY_MOD, PLAIN_MOD)
        console.log("[yellow]FHE setup finished.[/yellow]")

        # send our EC embedded items to server
        client_to_server_communiation_oprf = serialize_and_send_data(client, filename="client_preprocessed")
        console.log("[yellow]Elliptic curve embedded items sent to server.[/yellow]")

        # get the PRFed version of our set back from server
        PRFed_encoded_client_set, server_to_client_communication_oprf = get_and_deserialize_data(client)
        console.log("[yellow]PRFed items received from server.[/yellow]")

        t0 = time()

        # We finalize the OPRF processing by applying the inverse of the secret key, oprf_client_key
        key_inverse = pow(OPRF_CLIENT_KEY, -1, GENERATOR_ORDER)
        PRFed_client_set = client_prf_online_parallel(PRFed_encoded_client_set, key_inverse)
        console.log("[yellow]OPRF processing finished.[/yellow]")

        # Each PRFed item from the client set is mapped to a Cuckoo hash table
        # We pad the Cuckoo vector with dummy messages
        CH = Cuckoo(HASH_SEEDS)
        CH.insert_items(PRFed_client_set)
        CH.pad(dummy_msg_client)

        console.log("[yellow]PRF-encoded items inserted into Cuckoo hash table.[/yellow]")

        # Window procedure for all the items in the CH table
        windowed_items =  CH.windowing(MINIBIN_CAP, PLAIN_MOD)
        console.log("[yellow]Windowing procedure applied to items in the Cuckoo hash table.[/yellow]")

        # batching
        enc_query_serialized = create_and_seralize_batched_query(HEctx, windowed_items, LOG_B_ELL, BASE, MINIBIN_CAP)
        console.log("[yellow]Batched query finalized.[/yellow]")

        t1 = time()
        
        # set up and serialize the query to be sent to the server
        message_to_be_sent = [s_context, s_public_key, s_relin_key, s_rotate_key, enc_query_serialized]
        # send query to server
        client_to_server_communiation_query = serialize_and_send_data(client, data=message_to_be_sent)
        console.log("[yellow]Query sent to server, waiting for answer.[/yellow]")

        # get the ciphertexts from server
        ciphertexts, server_to_client_query_response = get_and_deserialize_data(client)
        console.log("[yellow]Answer containing ciphertexts received from server.[/yellow]")

        t2 = time()

        # decrypt ciphertexts
        decryptions = decrypt_ciphertexts(HEctx, ciphertexts)
        console.log("[yellow]Ciphertexts decrypted.[/yellow]")

        # find the client's intersection with the server set (as found by the PSI protocol)
        PSI_intersection = find_client_intersection(decryptions, windowed_items, PRFed_client_set)
        console.log("[yellow]Client and server intersection found.[/yellow]")

        t3 = time()
        console.log("\n[blue]Intersection recovered correctly: {}[/blue]".format(check_if_recovered_real_intersection(PSI_intersection, "intersection")))
        console.log("[blue]Client ONLINE computation time {:.2f}s[/blue]".format(t1 - t0 + t3 - t2))
        console.log("[blue]Communication size:[/blue]")
        console.log("[blue]~ Client --> Server:  {:.2f} MB[/blue]".format((client_to_server_communiation_oprf + client_to_server_communiation_query )/ 2 ** 20))
        console.log("[blue]~ Server --> Client:  {:.2f} MB[/blue]".format((server_to_client_communication_oprf + server_to_client_query_response )/ 2 ** 20))

        # disconnect from server
        client.close()

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

def send_bytes_to_send_to_server(clientsocket, data):
    """
    Sends the length of data to send to the server. 
    Used before the client sends a larger amount of data. The data will be
    padded till it reaches 10 bytes before it is sent. I.e. if client sends
    6 items, it will send '6         ' to the server via this function first.

    :param clientsocket: client's socket object with a connection to server
    :param data: data that client wants to send (client only sends size here)
    :return: the number of bytes the client will send
    """
    
    # prepare size, pad with spaces to reach 10 bytes, send data, return the length
    msg_length = len(data)
    padded_msg_length = str(msg_length) + ' ' * (10 - len(str(msg_length)))
    clientsocket.sendall((padded_msg_length).encode())

    return msg_length


def send_embedded_items_to_server(clientsocket, preprocessed_file):
    """
    Opens the client's preprocessed set, serializes it and sends it to the server.

    :param clientsocket: client's socket object
    :preprocessed_file: filename of client's preprocessed dataset (output of client_offline.py)
    :return: length of data sent from client to server
    """

    # Open and serialize client's preprocessed set
    unloaded_set = open(preprocessed_file, "rb")
    encoded_client_set = pickle.load(unloaded_set)
    encoded_client_set_serialized = pickle.dumps(encoded_client_set, protocol=None)

    # send length of data to server first
    client_to_server_communiation_oprf = send_bytes_to_send_to_server(clientsocket, encoded_client_set_serialized)
    # then send the data
    clientsocket.sendall(encoded_client_set_serialized)

    return client_to_server_communiation_oprf

def get_bytes_to_receive_from_server(clientsocket):
    """
    Receives the amount of bytes to receive from the server, from the server.
    Used before the server sends a larger amount of data.

    :param clientsocket: client's socket object with a connection to server
    :return: the number of bytes the server will send
    """
    return int(clientsocket.recv(10).decode().strip())

def receive_PRFed_set(clientsocket):
    """
    Receives the (serialized) PRF-processed set from the server. Unserializes the
    set and returns it along with the length of the serialized data.
    
    :param clientsocket: client's socket object
    :returns:
        PRFed_encoded_client_set: PRF-encoded client set
        server_to_client_communication_oprf: size of data sent by server
    """

    bytes_to_receive = get_bytes_to_receive_from_server(clientsocket)

    PRFed_client_set_serialized = b""
    while len(PRFed_client_set_serialized) < bytes_to_receive:
        data = clientsocket.recv(4096)
        if not data: break
        PRFed_client_set_serialized += data

    PRFed_client_set = pickle.loads(PRFed_client_set_serialized)

    return PRFed_client_set, len(PRFed_client_set_serialized)

def create_and_seralize_batched_query(pyfhelctx, windowed_items, log_b_ell, base, minibin_cap):
    """
    Given a list of windowed items, returns a serialized and batched query to be sent to the server.
    Using the provided Pyfhel object, pyfhelctx, the query is of course encrypted.
    
    :param pyfhelctx: the Pyfhel object
    :param windowed_items: client's windowed items
    :return: batched query
    """
    plain_query = [None for k in range(len(windowed_items))]
    enc_query = [[None for j in range(log_b_ell)] for i in range(1, base)]

    # We create the <<batched>> query to be sent to the server
    # By our choice of parameters, number of bins = poly modulus degree (m/N =1), so we get (base - 1) * logB_ell ciphertexts
    for i in range(log_b_ell):
        for j in range(base - 1):
            if ((j + 1) * base ** i - 1 < minibin_cap):
                for k in range(len(windowed_items)):
                    plain_query[k] = windowed_items[k][j][i]
                enc_query[j][i] = pyfhelctx.encrypt(plain_query)
    
    enc_query_serialized = [[None for j in range(log_b_ell)] for i in range(1, base)]

    for i in range(log_b_ell):
        for j in range(base - 1):
            if ((j + 1) * base ** i - 1 < minibin_cap):
                enc_query_serialized[j][i] = enc_query[j][i].to_bytes()

    return enc_query_serialized

def send_query_to_server(clientsocket, message_to_be_sent):
    """
    Serializes message_to_be_sent, then sends the size of message_to_be_sent
    to the server, then sends message_to_be_sent itself to the server. Returns
    the size of the message_to_be_sent in bytes.

    :param clientsocket: client's socket
    :param message_to_be_sent: non-serialized message client wants to send
    :return: size of message_to_be_sent in bytes
    """

    message_to_be_sent_serialized = pickle.dumps(message_to_be_sent, protocol=None)

    # send length of data first
    client_to_server_communiation_query = send_bytes_to_send_to_server(clientsocket, message_to_be_sent_serialized)
    # print("context + ciphertext -> server")
    # then send the actual data
    clientsocket.sendall(message_to_be_sent_serialized)

    return client_to_server_communiation_query

def receive_answer_from_server(clientsocket):
    """
    Receive the answer to the query (see send_query_to_server) from server.

    :param clientsocket: client's socket that is connected to server
    :return:
        ciphertexts - the unserialized ciphertexts (answers)
        server_to_client_query_response - size of the response (size of serialized ciphertexts)
    """

    bytes_to_receive = get_bytes_to_receive_from_server(clientsocket)

    answer = b""
    while len(answer) < bytes_to_receive:
        data = clientsocket.recv(4096)
        if not data: break
        answer += data

    ciphertexts = pickle.loads(answer)

    return ciphertexts, len(answer)

def decrypt_ciphertexts(pyfhelctx, ciphertexts, scheme="bfv"):
    """
    Decrypts a lits of ciphertexts, returns a list of plaintexts.

    :param pyfhelctx: the Pyfhel object
    :param ciphertexts: list of ciphertexts
    :param scheme: the FHE scheme, default to BFV (Brakerski-Fan-Vercauteren)
    :return: list of plaintexts
    """

    decryptions = []
    for ct in ciphertexts:
        decryptions.append(PyCtxt(bytestring=ct, pyfhel=pyfhelctx, scheme=scheme).decrypt())
    return decryptions

def find_client_intersection(decryptions, windowed_items, PRFed_client_set,):
    """
    Finds the client's intersection given the list of decrypted answers from the server,
    the client's windowed items, and the PRF-processed client set.

    :param decryptions: list of decrypted ciphertexts
    :param windowed_items: client's windowed items
    :param PRFed_client_set: client's PRFed client set
    :return: the client's intersection with the server set
    """

    recover_CH_structure = []
    for matrix in windowed_items:
        recover_CH_structure.append(matrix[0][0])

    count = [0] * ALPHA

    # get client's set
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

    return client_intersection

def check_if_recovered_real_intersection(PSI_intersection, real_intersection_file):
    """
    Checks if the client recovered the real intersection. Should evaluate to true
    if protocol is right.

    :param PSI_intersection: list representing the intersection as calculated by the PSI protocol
    :param real_intersection_file: filename of file containing the real client/server set intersection
    :return: boolean indicating whether the correct intersection was recovered or not
    """
    h = open(real_intersection_file, 'r')
    real_intersection = [int(line[:-1]) for line in h]
    h.close()
    
    return set(PSI_intersection) == set(real_intersection)

if __name__ == "__main__":
    main()
