"""Simple calculator demonstrating function calls and code reuse.

Shows how CALL/RET enables writing modular code with reusable functions.
Calculates (a + b) * (c + d) by reusing an 'add' function.
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, Label, R

# Program that computes (a + b) * (c + d) using a reusable add function
# Demonstrates how functions enable code reuse without duplication
calculator = [
    # Get four numbers from user
    I.NIN(R.a),  # First number
    I.NIN(R.b),  # Second number
    I.NIN(R.c),  # Third number
    I.NIN(R.d),  # Fourth number
    # Compute a + b by calling add function
    # add function expects inputs in R.a and R.b, returns result in R.a
    I.CALL(add := Label("add")),
    # Save result of (a + b) in R.e
    I.CP(R.a, R.e),
    # Compute c + d by calling add function again
    I.CP(R.c, R.a),  # Move c to R.a
    I.CP(R.d, R.b),  # Move d to R.b
    I.CALL(add),
    # Now multiply: R.e * R.a = (a + b) * (c + d)
    I.MUL(R.e, R.a),
    # Print result
    I.NOUT(R.e, L[1]),
    # Exit
    I.JMP(end := Label("end")),
    # Reusable add function
    # Input: R.a, R.b
    # Output: R.a = R.a + R.b
    add,
    I.ADD(R.a, R.b),
    I.RET(),
    end,
]

cpu = DT31(registers=["a", "b", "c", "d", "e"])
print("Simple calculator: (a + b) * (c + d)")
print("Enter four numbers:")
cpu.run(calculator, debug=False)
