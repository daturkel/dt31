"""Factorial calculator using DT31 assembly.

Calculates and prints the factorial of a number (N from user input). This implementation
doesn't use labels or any sort of memoization, instead it just loops with a relative jump.
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, R

# Calculate factorial of N
factorial = [
    # Get number from user
    I.NIN(R.a),
    # Initialize result in R.b = 1
    I.CP(L[1], R.b),
    # If 1 >= R.a (i.e., R.a <= 1), jump to end (result is 1)
    I.RJGE(L[4], L[1], R.a),
    # R.b = R.b * R.a
    I.MUL(R.b, R.a),
    # Decrement R.a
    I.SUB(R.a, L[1]),
    # Loop back if R.a > 1
    I.RJGT(L[-3], R.a, L[1]),
    # Print result
    I.NOUT(R.b, L[1]),
]

if __name__ == "__main__":
    cpu = DT31(registers=["a", "b"])
    cpu.run(factorial, debug=False)
