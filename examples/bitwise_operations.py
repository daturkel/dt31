"""Bitwise operations demonstration using DT31 assembly.

Shows various bitwise operations: AND, OR, XOR, NOT, shift left, shift right.
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, R

# Demonstrate bitwise operations
bitwise_ops = [
    # Get two numbers from user
    I.NIN(R.a),
    I.NIN(R.b),
    # Bitwise AND
    I.BAND(R.a, R.b, R.c),
    I.NOUT(R.c, L[1]),
    # Bitwise OR
    I.BOR(R.a, R.b, R.c),
    I.NOUT(R.c, L[1]),
    # Bitwise XOR
    I.BXOR(R.a, R.b, R.c),
    I.NOUT(R.c, L[1]),
    # Bitwise NOT of first number
    I.BNOT(R.a, R.c),
    I.NOUT(R.c, L[1]),
    # Bit shift left (R.a << 2)
    I.BSL(R.a, L[2], R.c),
    I.NOUT(R.c, L[1]),
    # Bit shift right (R.a >> 1)
    I.BSR(R.a, L[1], R.c),
    I.NOUT(R.c, L[1]),
]

if __name__ == "__main__":
    cpu = DT31(registers=["a", "b", "c"])
    print("Enter two numbers for bitwise operations:")
    print("Results will be: AND, OR, XOR, NOT(first), first<<2, first>>1")
    cpu.run(bitwise_ops, debug=False)
