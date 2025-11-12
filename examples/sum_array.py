"""Sum array elements using DT31 assembly.

Demonstrates memory operations by reading numbers into memory until user enters 0,
then summing all the numbers.
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, Label, R

# Read numbers into memory until 0, then sum them
sum_array = [
    # R.a = sum accumulator, R.b = last input, R.c = stack size
    # Read number into R.b
    read_loop := Label("read_loop"),
    I.NIN(R.b),
    # Push R.b to stack
    I.PUSH(R.b),
    # Accumulate counter
    I.ADD(R.c, L[1]),
    # If R.b > 0, loop back
    I.JIF(read_loop, R.b),
    # Pop off the 0
    I.POP(),
    # Decrement counter (since we pushed the 0)
    I.ADD(R.c, L[-1]),
    # If the counter is 0, skip to output (no numbers to sum)
    I.JEQ(output := Label("output"), R.c, L[0]),
    # Sum loop: pop and accumulate
    sum_loop := Label("sum_loop"),
    # Pop to R.b
    I.POP(R.b),
    # R.a += R.b
    I.ADD(R.a, R.b),
    # Decrement counter
    I.ADD(R.c, L[-1]),
    # Loop back if more items remain
    I.RJGT(sum_loop, R.c, L[0]),
    # Output result
    output,
    I.NOUT(R.a, L[1]),
]

if __name__ == "__main__":
    cpu = DT31(registers=["a", "b", "c"])
    print("Enter numbers to sum (enter 0 to finish):")
    cpu.run(sum_array, debug=False)
