"""Factorial calculator using DT31 assembly with labels.

Demonstrates using named labels for control flow instead of relative jumps.
Calculates and prints the factorial of a number (N from user input).
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, Label, R

# Define labels for code clarity


# Calculate factorial of N
factorial = [
    # Get number from user
    I.NIN(R.a),
    # Initialize result in R.b = 1
    I.CP(L[1], R.b),
    # If R.a <= 1, jump to end (result is 1)
    I.RJGE(end := Label("end"), L[1], R.a),
    # Mark the beginning of the loop
    loop := Label("loop"),
    # R.b = R.b * R.a
    I.MUL(R.b, R.a),
    # Decrement R.a
    I.SUB(R.a, L[1]),
    # Loop back if R.a > 1
    I.RJGT(loop, R.a, L[1]),
    # Mark the end
    end,
    # Print result
    I.NOUT(R.b, L[1]),
]

if __name__ == "__main__":
    cpu = DT31(registers=["a", "b"])
    print("Enter number to compute factorial:")
    cpu.run(factorial, debug=False)
