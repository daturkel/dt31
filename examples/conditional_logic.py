"""Conditional logic demonstration using DT31 assembly.

Demonstrates comparison operations and conditional jumps by finding the maximum
of three numbers.
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import R, L

# Find maximum of three numbers
find_max = [
    # Get three numbers from user into R.a, R.b, R.c
    I.NIN(R.a),
    I.NIN(R.b),
    I.NIN(R.c),
    # Assume R.a is max (stored in R.a)
    # Compare R.a with R.b: if R.b > R.a, copy R.b to R.a
    I.RJGT(L[2], R.b, R.a),
    I.RJMP(L[2]),
    I.CP(R.b, R.a),
    # Compare R.a with R.c: if R.c > R.a, copy R.c to R.a
    I.RJGT(L[2], R.c, R.a),
    I.RJMP(L[2]),
    I.CP(R.c, R.a),
    # Output the maximum
    I.NOUT(R.a, L[1]),
]

cpu = DT31(registers=["a", "b", "c"])
print("Enter three numbers to find the maximum:")
cpu.run(find_max, debug=False)
