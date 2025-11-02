"""Fibonacci sequence generator using DT31 assembly.

Calculates and prints the first N Fibonacci numbers (N from user input).
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, Label, R

# Calculate first N Fibonacci numbers
fibonacci = [
    # Set R.c to the amount of fibonacci numbers to produce
    I.NIN(R.c),
    # Initialize: R.b = 1 (R.a = 0 by default)
    I.CP(1, R.b),
    loop := Label("loop"),
    # Print current value (R.a) with a newline
    I.NOUT(R.a, L[1]),
    # R.b = R.a + R.b
    I.ADD(R.b, R.a),
    # R.a = R.b - R.a
    I.SUB(R.b, R.a, R.a),
    # Decrement counter
    I.SUB(R.c, 1),
    # Loop if counter > 0
    I.RJGT(loop, R.c, 0),
]

cpu = DT31(registers=["a", "b", "c"])
print("Enter number of Fibonacci numbers to generate:")
cpu.run(fibonacci, debug=False)
