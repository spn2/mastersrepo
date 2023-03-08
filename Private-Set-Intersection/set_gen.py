from random import sample
from typing import List, Tuple

from constants import SERVER_SIZE, CLIENT_SIZE, INTERSECTION_SIZE

def main():

	client_set, server_set, intersection = generate_data_sets(SERVER_SIZE, CLIENT_SIZE, INTERSECTION_SIZE)

	write_list_to_file("client_set", client_set)
	write_list_to_file("server_set", server_set)
	write_list_to_file("intersection", intersection)


def generate_data_sets(server_size: int, client_size: int, intersection_size: int) -> Tuple[List[int], List[int]]:
    """
    Generates two disjoint sets of integers with the given sizes and intersection size.
    The integers must be less than the order of the generator of the elliptic curve
    (e.g., 192-bit integers if P192 is used). Since we use the sample function, we are 
	limited to 2 ** 63 - 1 (see max_int).

    :param server_size: the size of the set for the server
    :param client_size: the size of the set for the client
    :param intersection_size: the size of the intersection between the sets
    :return: a tuple containing the client set, server set and their intersection
    """

	# maximum integer allowed for python's sample function
    max_int = 2 ** 63 - 1

    # Generate a disjoint union of integers for both sets
    disjoint_union = sample(range(max_int), server_size + client_size)

    # Split the intersection and assign it to the server and client sets
    intersection = disjoint_union[:intersection_size]
    server_set = intersection + disjoint_union[intersection_size: server_size + intersection_size]
    client_set = intersection + disjoint_union[server_size + intersection_size: server_size + client_size]

    return client_set, server_set, intersection

def write_list_to_file(filename: str, items: List) -> None:
    """
    Writes the items in the given list to a file with the specified name.

    :param filename: The name of the file to write to.
    :param items: The list of items to write to the file.
    :return: None
    """
    with open(filename, 'w') as f:
        for item in items:
            f.write(str(item) + '\n')


if __name__ == "__main__":
    main()
