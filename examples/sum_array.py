"""Sum array elements using DT31 assembly.

Demonstrates memory operations by reading numbers into memory until user enters 0,
then summing all the numbers.
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, R

# Read numbers into memory until 0, then sum them
sum_array = [
    # R.a = sum accumulator, R.b = last input, R.c = stack size
    # 0: Read number into R.b,
    I.NIN(R.b),
    # 1: Push R.b to stack
    I.PUSH(R.b),
    # 2: Accumulate counter
    I.ADD(R.c, L[1]),
    # 3: If R.b] > 0, loop back
    I.JIF(L[0], R.b),
    # 4: Pop off the 0
    I.POP(),
    # 5: If the counter is 0, skip to output
    I.JEQ(L[10], R.c, L[1]),
    # 6: Pop to R.b
    I.POP(R.b),
    # 7: R.a += R.b
    I.ADD(R.a, R.b),
    # 8: Decrement counter
    I.ADD(R.c, L[-1]),
    # 9: Loop back
    I.JMP(L[5]),
    # 10: Output result
    I.NOUT(R.a, L[1]),  # 10
]

cpu = DT31(registers=["a", "b", "c"])
print("Enter numbers to sum (enter 0 to finish):")
cpu.run(sum_array, debug=False)
