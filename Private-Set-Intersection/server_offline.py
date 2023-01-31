from math import log2
import pickle
from time import time

from rich.console import Console

from auxiliary_functions import coeffs_from_roots, read_file_return_list
from constants import *
from oprf import server_prf_offline_parallel
from oprf_constants import GENERATOR_ORDER, G, OPRF_SERVER_KEY
from simple_hash import Simple_hash

# simple_hashed_data is padded with MSG_PADDING
MSG_PADDING = 2 ** (SIGMA_MAX - OUTPUT_BITS + int(log2(NUM_OF_HASHES)) + 1) + 1

if __name__ == "__main__":

    # for prettier printing
    console = Console()

    with console.status("[bold green]Server offline in progress...") as status:

        # store server's set in memory 
        server_set = read_file_return_list("server_set")

        # key * generator of elliptic curve (EC)
        key_gen_point = (OPRF_SERVER_KEY % GENERATOR_ORDER) * G

        t0 = time()

        # server's items multiplied by server's key * generator of the EC
        PRFed_server_set = set(server_prf_offline_parallel(server_set, key_gen_point))

        t1 = time()

        console.log("[green]OPRF preprocessing finished. Time taken: {:.2f}s.[/green]".format(t1-t0))

        # Server's OPRFed items are hashed and padded (see simple_hash.py)
        SH = Simple_hash(HASH_SEEDS)
        SH.insert_entries(PRFed_server_set)
        SH.pad_bins()

        t2 = time()

        console.log("[green]Simple hashing finished. Time taken: {:.2f}s.[/green]".format(t2-t1))

        # Here we perform the partitioning:
        # Namely, we partition each bin into alpha minibins with B/alpha items each
        # We represent each minibin as the coefficients of a polynomial of degree B/alpha that vanishes in all the entries of the mininbin
        # Therefore, each minibin will be represented by B/alpha + 1 coefficients; notice that the leading coeff = 1
        poly_coeffs = SH.partition()

        print(type(poly_coeffs))
        print(type(poly_coeffs[0]))
        print(poly_coeffs[0])
        print(type(poly_coeffs[0][0]))

        f = open('server_preprocessed', 'wb')
        pickle.dump(poly_coeffs, f)
        f.close()
        
        t3 = time()

        console.log("[green]Poly coefficients from roots finished. Time taken: {:.2f}s.[/green]".format(t3-t2))

        console.log("[blue]Server offline total time: {:.2f}s[/blue]".format(t3-t0))
