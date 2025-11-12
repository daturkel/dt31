"""Memoized factorial calculator using DT31 assembly.

Demonstrates using memory to store and retrieve previously calculated factorial values.
This version caches factorial results in memory, with the cache growing as large as needed.

Memory layout:
- M[N]: Cached factorial value for n=N

Register usage:
- R.a: Input value N
- R.b: Loop counter for computing factorials
- R.c: Accumulated factorial result
- R.max: Max cached value (starts at 1, grows as we compute more)

Algorithm:
1. Read input N into R.a
2. If N <= R.max, return M[N] directly (cache hit)
3. Otherwise, compute factorial from R.max+1 to N, storing each result in memory
4. Return M[N]
"""

import dt31.instructions as I
from dt31.cpu import DT31
from dt31.operands import L, Label, M, R

factorial_memoized = [
    # Initialize R.max = 1 (max cached value) and M[1] = 1 (factorial(1) = 1)
    I.CP(L[1], R.max),
    I.CP(L[1], M[1]),
    # Main loop start
    start := Label("start"),
    # Get input N into R.a
    I.NIN(R.a),
    # If N <= R.max (max cached), we have a cache hit
    I.RJGE(cache_hit := Label("cache_hit"), R.max, R.a),
    # Cache miss: need to compute from R.max+1 to R.a
    # R.b = R.max + 1 (start computing from here)
    I.CP(R.max, R.b),
    I.ADD(R.b, L[1]),
    # R.c = M[R.max] (result of previous factorial)
    I.CP(M[R.max], R.c),
    # Compute loop: calculate factorial(R.b) and store in M[R.b]
    compute_loop := Label("compute_loop"),
    # R.c = R.c * R.b (compute next factorial)
    I.MUL(R.c, R.b),
    # Store result in M[R.b]
    I.CP(R.c, M[R.b]),
    # Update max cached value R.max = R.b
    I.CP(R.b, R.max),
    # Increment R.b for next iteration
    I.ADD(R.b, L[1]),
    # If R.b <= R.a, continue computing
    I.RJGE(compute_loop, R.a, R.b),
    # Jump to output
    I.RJMP(output := Label("output")),
    # Cache hit: result is already in M[R.a]
    cache_hit,
    # (no computation needed)
    # Output the result M[R.a]
    output,
    I.NOUT(M[R.a], L[1]),
    # Loop back to start for another calculation
    I.RJMP(start),
]

if __name__ == "__main__":
    cpu = DT31(registers=["a", "b", "c", "max"])
    print("The program caches results in memory - try entering")
    print("the same number twice or increasing numbers to see")
    print("instant lookups! Press Ctrl+C to exit.")
    cpu.run(factorial_memoized, debug=False)
