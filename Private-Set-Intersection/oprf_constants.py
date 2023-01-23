from fastecdsa.curve import P192
from fastecdsa.point import Point
from math import log2
from constants import SIGMA_MAX

MASK = 2 ** SIGMA_MAX - 1

NUM_OF_PROCESSES = 4

# Curve parameters
curve_used = P192
prime_of_curve_equation = curve_used.p
order_of_generator = curve_used.q
log_p = int(log2(prime_of_curve_equation)) + 1
G = Point(curve_used.gx, curve_used.gy, curve=curve_used) #generator of the curve_used