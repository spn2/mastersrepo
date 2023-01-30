import pickle
from time import time

from rich.console import Console

from auxiliary_functions import *
from oprf import client_prf_offline
from oprf_constants import GENERATOR_ORDER, G, OPRF_CLIENT_KEY


if __name__ == "__main__":

    # for prettier printing
    console = Console()

    with console.status("[bold green]Client offline in progress...") as status:

        t0 = time()

        # key * generator of elliptic curve
        client_point_precomputed = (OPRF_CLIENT_KEY % GENERATOR_ORDER) * G

        # store client's set in memory 
        client_set = read_file_return_list("client_set")

        # Client's items are encoded on the elliptic curve, retrieve the x and y coords of each point (item)
        encoded_client_set = client_prf_offline((client_set, client_point_precomputed))

        console.log("[green]Client finished embedding items on ellipctic curve.[/green]")


        # write the preprocessed client's set to disk
        g = open('client_preprocessed', 'wb')
        pickle.dump(encoded_client_set, g)
        g.close()

        t1 = time()

        console.log("[blue]Client offline total time: {:.2f}s[/blue]".format(t1-t0))

        # print('Client OFFLINE time: {:.2f}s'.format(t1-t0))
