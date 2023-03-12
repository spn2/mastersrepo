from math import log2
import pickle
from time import time

from rich.console import Console

from auxiliary_functions import read_file_return_list_of_int
from constants import *
from oprf import server_prf_offline_parallel
from oprf_constants import BASE_ORDER, G, SERVER_OPRF_KEY
from simple_hash import SimpleHash

# simple_hashed_data is padded with MSG_PADDING
MSG_PADDING = 2 ** (SIGMA_MAX - OUTPUT_BITS + int(log2(NUM_OF_HASHES)) + 1) + 1

def main():
    # for prettier printing
    console = Console()

    with console.status("[bold red]Server offline in progress...") as status:

        # store server's set in memory 
        server_set = read_file_return_list_of_int("server_set")

        # key * generator of elliptic curve (EC)
        key_gen_point = (SERVER_OPRF_KEY % BASE_ORDER) * G

        t0 = time()

        # server's items multiplied by server's key * generator of the EC
        PRFed_server_set = set(server_prf_offline_parallel(server_set, key_gen_point))

        t1 = time()

        console.log("[yellow]OPRF preprocessing finished (server items are embedded on the ellipctic curve). Time taken: {:.2f}s.[/yellow]".format(t1-t0))

        # Server's OPRFed items are hashed and padded (see simple_hash.py)
        SH = SimpleHash(HASH_SEEDS)
        SH.insert_entries(PRFed_server_set)
        SH.pad_bins()

        t2 = time()

        console.log("[yellow]Simple hashing finished (server items are in bins). Time taken: {:.2f}s.[/yellow]".format(t2-t1))

        poly_coeffs = SH.partition(ALPHA, MINIBIN_CAP, PLAIN_MOD)

        f = open('server_preprocessed', 'wb')
        pickle.dump(poly_coeffs, f)
        f.close()
        
        t3 = time()

        console.log("[yellow]Finished partitioning (coefficients of minibin polynomials found). Time taken: {:.2f}s.[/yellow]".format(t3-t2))

        console.log("[blue]Server offline total time: {:.2f}s[/blue]".format(t3-t0))

if __name__ == "__main__":
    main()