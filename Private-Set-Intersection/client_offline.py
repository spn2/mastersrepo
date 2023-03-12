import pickle
from time import time

from rich.console import Console

from auxiliary_functions import *
from oprf import client_prf_offline
from oprf_constants import BASE_ORDER, G, CLIENT_OPRF_KEY

def main():
    # for prettier printing
    console = Console()

    with console.status("[bold red]Client offline in progress...") as status:

        t0 = time()

        # key * generator of elliptic curve
        client_point_precomputed = (CLIENT_OPRF_KEY % BASE_ORDER) * G

        # store client's set in memory 
        client_set = read_file_return_list_of_int("client_set")

        # Client's items are encoded on the elliptic curve, retrieve the x and y coords of each point (item)
        encoded_client_set = client_prf_offline((client_set, client_point_precomputed))

        t1 = time()

        console.log("[yellow]OPRF preprocessing finished. Time taken: {:.2f}s.[/yellow]".format(t1-t0))


        # write the preprocessed client's set to disk
        g = open('client_preprocessed', 'wb')
        pickle.dump(encoded_client_set, g)
        g.close()

        t2 = time()

        console.log("[blue]Client offline total time: {:.2f}s[/blue]".format(t2-t0))



if __name__ == "__main__":
    main()