import pickle
import socket
from time import time, sleep
from typing import List, Tuple

import numpy as np
from Pyfhel import Pyfhel, PyCtxt
from rich.console import Console

from auxiliary_functions import get_and_deserialize_data, reconstruct_power, serialize_and_send_data
from constants import *
from oprf import server_prf_online_parallel
from oprf_constants import SERVER_OPRF_KEY


def main():

    # for prettier printing
    console = Console()

    with console.status("[bold green]Server online in progress...") as status:

        t0 = time()
        console.log("[yellow]Waiting for client.[/yellow]")

        # socket setup; wait for client connection here
        conn_socket = server_network_setup()
        console.log("[yellow]Client connection accepted.[/yellow]")

        # server receives elliptic curve embedded curve points from the client
        encoded_client_set, client_embedded_set_size = get_and_deserialize_data(conn_socket)
        console.log("[yellow]Received client's elliptic curve embedded items.[/yellow]")

        t1 = time()
        # server multiplies the client's curve points with server's OPRF key
        PRFed_client_set = server_prf_online_parallel(encoded_client_set, SERVER_OPRF_KEY)
        console.log("[yellow]Finished multiplying client's items with server's OPRF key.[/yellow]")

        t2 = time()
        # send the result (PRFed_client_set) to the client
        PRFed_client_set_size = serialize_and_send_data(conn_socket, PRFed_client_set)
        console.log("[yellow]Client's EC-embedded items * server's OPRF key sent to client.[/yellow]")
    
        # We wait for client to send us their FHE context and ciphertext, and also their query
        received_data, fhe_context_and_query_size = get_and_deserialize_data(conn_socket)

        # reconstruct the pyfhel object (pyfhelobj) and the (serialized) client query
        pyfhelobj, serialized_query = server_FHE_setup(received_data)
        console.log("[yellow]Received client's query and Fully Homomorphic Encryption context.[/yellow]")

        # deserialize the client's query
        encrypted_query = reconstruct_encrypted_query(pyfhelobj, serialized_query)
        console.log("[yellow]Finished deserializing client's query.[/yellow]")

        # recover all the encrypted powers Enc(y), Enc(y^2), Enc(y^3) ..., Enc(y^{minibin_capacity})
        all_powers = recover_encrypted_powers(encrypted_query)
        console.log("[yellow]Finished recovering client's encrypted powers.[/yellow]")

        t3 = time()
        # prepare server's answer to client query; the evaluated polynomials in encrypted form
        srv_answer = prepare_server_response(pyfhelobj, all_powers, "server_preprocessed")

        t4 = time()
        # send the answer
        server_answer_size = serialize_and_send_data(conn_socket, data=srv_answer)
        console.log("[yellow]Server's answer prepared and sent to client.[/yellow]")

        t5 = time()

        # close the connection socket
        conn_socket.close()

        console.log("\n[blue]Server time spent on computations: {:.2f}s[/blue]".format(t2-t1+t4-t3))
        console.log("[blue]Server program total time:  {:.2f}s[/blue]".format(t5 - t0))
        console.log("[blue]Communication sizes:[/blue]")
        console.log("[blue]\tServer --> Client:\t{:.2f} MB[/blue]".format((PRFed_client_set_size + server_answer_size )/ 2 ** 20))
        console.log("[blue]\tClient --> Server:\t{:.2f} MB[/blue]".format((client_embedded_set_size + fhe_context_and_query_size )/ 2 ** 20))


def server_network_setup():
    """
    Sets up server's socket and binds it to localhost on port 4470.
    Waits for a connection from the client. Returns the connection
    socket when a connection has been established.

    :return: socket representing the server-client connection
    """
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.bind(('localhost', 4470))
    serv.listen(1)

    # accept connection from client
    connectionsocket, _ = serv.accept()

    return connectionsocket

def server_FHE_setup(received_data: List[bytes]) -> Tuple[Pyfhel, bytes]:
    """
    Reconstruct the client's Pyfhel context (including the
    public, relinearization and rotation key), and the
    client query.

    :param received_data: list with Pyfhel context, public, relinearization,
                          rotation key, and the client's query.
    :returns:
        pyfhelobj: Pyfhel object representing the client's FHE context
        serialized_query: client's query
    """
    pyfhelobj = Pyfhel()
    pyfhelobj.from_bytes_context(received_data[0])
    pyfhelobj.from_bytes_public_key(received_data[1])
    pyfhelobj.from_bytes_relin_key(received_data[2])
    # pyfhelobj.from_bytes_rotate_key(received_data[3])

    # serialized_query = received_data[4]
    serialized_query = received_data[3]

    return pyfhelobj, serialized_query

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
            all_powers[k] = reconstruct_power(encrypted_query, k + 1)
    all_powers = all_powers[::-1]

    return all_powers

def prepare_server_response(pyfhelobj: Pyfhel, all_powers: List[PyCtxt], 
                            server_preprocessed_filename: str) -> List[bytes]:
    """
    Computes the polynomials (while in encrypted form; FHE magic happens here)
    and returns the resulting ciphertexts.

    :param pyfhelobj: the Pyfhel object, needed for relinearization after multiplications
    :param all_powers: client's encrypted powers
    :param server_preprocessed_filename: filename where server's prepocessed items are
                                         (see server_offline.py)
    :return: evaluated polynomials in encrypted form
    """

    # get server's preprocessed items
    g = open(server_preprocessed_filename, 'rb')
    poly_coeffs = pickle.load(g)

    # the columns are used
    transposed_poly_coeffs = np.transpose(poly_coeffs).tolist()

    # Server sends alpha ciphertexts, obtained from performing dot_product between the polynomial coefficients from the preprocessed server database and all the powers Enc(y), ..., Enc(y^{minibin_capacity})
    evaluated_polynomials = []
    for i in range(ALPHA):
        # the rows with index multiple of (B/alpha+1) have only 1s

        dot_product = all_powers[0]
        for j in range(1, MINIBIN_CAP):
            dot_product = dot_product + transposed_poly_coeffs[(MINIBIN_CAP + 1) * i + j] * all_powers[j]
            
            # # ValueError: not enough relinearization keys
            # ~dot_product
            
            # # ValueError: not enough relinearization keys
            # # pyfhelobj.relinearize(dot_product)

        dot_product = dot_product + transposed_poly_coeffs[(MINIBIN_CAP + 1) * i + MINIBIN_CAP]
        evaluated_polynomials.append(dot_product.to_bytes())

    return evaluated_polynomials

if __name__ == "__main__":
    main()
