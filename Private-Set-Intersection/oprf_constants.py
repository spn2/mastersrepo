from math import log2

from fastecdsa.curve import P192
from fastecdsa.point import Point

from constants import SIGMA_MAX

MASK = 2 ** SIGMA_MAX - 1
"""
Integer used to mask.
"""

NUM_OF_PROCESSES = 8
"""
Used for parallel computation. Should probably set to number of cores on your system.
"""

# Elliptic curve constants
CURVE = P192
"""
A "fastecdsa" elliptic curve.
The curve is a Weierstrass curve generated over the prime field P-192, as described in section 4.2.1 of
https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-186-draft.pdf
"""
LOG_P = int(log2(CURVE.p)) + 1
"""
An integer equal to the number of bits needed to represent the modulus of the curve.
Modulus being the p in the curve equation y^2 = x^3 + ax + b (mod p).
"""
BASE_ORDER = CURVE.q
"""
The order of the base (i.e the point that generates all other points on the curve) point of the curve.
"""
G = Point(CURVE.gx, CURVE.gy, curve=CURVE)
"""
The base/generator of the curve represented as a "fastecdsa point.
"""

# client/server keys
CLIENT_OPRF_KEY = 12345678910111213141516171819222222222222
"""
Client's OPRF key.
"""
SERVER_OPRF_KEY = 1234567891011121314151617181920
"""
Server's OPRF key.
"""
