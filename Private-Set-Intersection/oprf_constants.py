from math import log2

from fastecdsa.curve import P192
from fastecdsa.point import Point

from constants import SIGMA_MAX

MASK = 2 ** SIGMA_MAX - 1

# for parallel computation
NUM_OF_PROCESSES = 8

# Curve parameters
CURVE = P192
prime_of_curve_equation = CURVE.p
LOG_P = int(log2(prime_of_curve_equation)) + 1
GENERATOR_ORDER = CURVE.q
# curve generator
G = Point(CURVE.gx, CURVE.gy, curve=CURVE)

# OPRF keys
OPRF_CLIENT_KEY = 12345678910111213141516171819222222222222
OPRF_SERVER_KEY = 1234567891011121314151617181920
