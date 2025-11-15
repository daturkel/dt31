Advanced Topics
===============

This tutorial covers advanced programming techniques in dt31, including control flow with functions and recursion, stack operations, and memory manipulation.

Functions and Recursion
-----------------------

Basic Function Calls
~~~~~~~~~~~~~~~~~~~~

Use ``CALL`` and ``RET`` to create reusable functions:

.. code-block:: nasm

   ; Main program
   CALL print_greeting
   CALL print_greeting
   JMP end

   ; Function definition
   print_greeting:
       OOUT 'H', 0
       OOUT 'i', 0
       OOUT '!', 1
       RET

   end:

**Output:**

.. code-block:: text

   Hi!
   Hi!

Functions automatically use the stack to store return addresses, allowing them to be called multiple times from different locations.

Function Parameters via Registers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass data to functions through registers:

.. code-block:: nasm

   ; Calculate (a + b) * (c + d)
   NIN R.a
   NIN R.b
   CALL add           ; R.a = a + b
   CP R.a, R.e        ; Save result

   NIN R.c
   NIN R.d
   CP R.c, R.a        ; Move c to R.a
   CP R.d, R.b        ; Move d to R.b
   CALL add           ; R.a = c + d

   MUL R.e, R.a       ; R.e = (a+b) * (c+d)
   NOUT R.e, 1
   JMP end

   ; Add function: R.a = R.a + R.b
   add:
       ADD R.a, R.b
       RET

   end:

This demonstrates the calling convention pattern:

1. Place arguments in specific registers
2. Call the function
3. Read result from the output register

Recursion
~~~~~~~~~

Functions can call themselves for recursive algorithms. Here's factorial:

.. code-block:: nasm

   ; Calculate factorial of 5
   CP 5, R.a
   CALL factorial
   NOUT R.a, 1
   JMP end

   ; Factorial function
   ; Input: R.a = n
   ; Output: R.a = n!
   factorial:
       ; Base case: if n <= 1, return 1
       JGT recursive_case, R.a, 1
       CP 1, R.a
       RET

   recursive_case:
       ; Recursive case: n * factorial(n-1)
       PUSH R.a                 ; Save n on stack
       SUB R.a, 1               ; R.a = n - 1
       CALL factorial           ; R.a = factorial(n-1)
       POP R.b                  ; Restore n to R.b
       MUL R.a, R.b             ; R.a = n * factorial(n-1)
       RET

   end:

**Output:** ``120``

**Key pattern for recursion:**

1. Check base case (exit condition)
2. ``PUSH`` values you need to preserve
3. Modify arguments and ``CALL`` recursively
4. ``POP`` preserved values
5. Combine results and ``RET``

Python Version
~~~~~~~~~~~~~~

The same factorial in Python:

.. code-block:: python

   from dt31 import DT31, I, L, Label, R

   cpu = DT31()

   factorial = Label("factorial")
   recursive_case = Label("recursive_case")

   program = [
       I.CP(L[5], R.a),
       I.CALL(factorial),
       I.NOUT(R.a, L[1]),
       I.JMP(end := Label("end")),

       factorial,
       I.JGT(recursive_case, R.a, L[1]),
       I.CP(L[1], R.a),
       I.RET(),

       recursive_case,
       I.PUSH(R.a),
       I.SUB(R.a, L[1]),
       I.CALL(factorial),
       I.POP(R.b),
       I.MUL(R.a, R.b),
       I.RET(),

       end,
   ]

   cpu.run(program)

Stack Operations
----------------

The Stack
~~~~~~~~~

dt31 includes a stack for:

- Temporary value storage
- Function call return addresses (automatic)
- Passing data between code sections

Stack operations:

- ``PUSH value`` - Push a value onto the stack
- ``POP [destination]`` - Pop top value (optionally to a destination)
- ``SEMP destination`` - Check if stack is empty (1 if empty, 0 otherwise)

Basic Stack Usage
~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Store values on stack
   CP 10, R.a
   PUSH R.a          ; Stack: [10]

   CP 20, R.a
   PUSH R.a          ; Stack: [10, 20]

   CP 30, R.a
   PUSH R.a          ; Stack: [10, 20, 30]

   ; Retrieve in reverse order (LIFO)
   POP R.b           ; R.b = 30, Stack: [10, 20]
   POP R.c           ; R.c = 20, Stack: [10]
   POP R.a           ; R.a = 10, Stack: []

   ; Check if empty
   SEMP R.d          ; R.d = 1 (stack is empty)

Processing with Stack
~~~~~~~~~~~~~~~~~~~~~

Use the stack to reverse processing order:

.. code-block:: python

   from dt31 import DT31, I, L, Label, LC, M

   cpu = DT31()

   # Print "hello, world!" using stack
   program = [
       # Push characters in reverse
       I.PUSH(LC["!"]),
       I.PUSH(LC["d"]),
       I.PUSH(LC["l"]),
       I.PUSH(LC["r"]),
       I.PUSH(LC["o"]),
       I.PUSH(LC["w"]),
       I.PUSH(LC[" "]),
       I.PUSH(LC[","]),
       I.PUSH(LC["o"]),
       I.PUSH(LC["l"]),
       I.PUSH(LC["l"]),
       I.PUSH(LC["e"]),
       I.PUSH(LC["h"]),

       # Pop and print until empty
       loop := Label("loop"),
       I.POP(M[1]),              # Pop to memory
       I.SEMP(M[2]),             # Check if empty
       I.OOUT(M[1], M[2]),       # Print with newline if empty
       I.JEQ(loop, M[2], L[0]),  # Loop if not empty
   ]

   cpu.run(program)  # Output: hello, world!

This technique is useful when you need LIFO (Last-In-First-Out) behavior.

Memory Operations
-----------------

Direct Memory Access
~~~~~~~~~~~~~~~~~~~~

Access memory using fixed addresses:

.. code-block:: nasm

   ; Store values in memory
   CP 100, [0]
   CP 200, [1]
   CP 300, [2]

   ; Read values from memory
   CP [0], R.a       ; R.a = 100
   CP [1], R.b       ; R.b = 200
   CP [2], R.c       ; R.c = 300

   ; Sum them
   ADD R.a, R.b
   ADD R.a, R.c
   NOUT R.a, 1       ; Output: 600

Indirect Memory Access
~~~~~~~~~~~~~~~~~~~~~~

Use register values as memory addresses:

.. code-block:: nasm

   ; Store array at addresses 10-14
   CP 5, [10]
   CP 15, [11]
   CP 25, [12]
   CP 35, [13]
   CP 45, [14]

   ; Sum array using indirect addressing
   CP 0, R.sum       ; sum = 0
   CP 10, R.i        ; i = 10 (start address)

   loop:
       ADD R.sum, [R.i]   ; sum += memory[i]
       ADD R.i, 1         ; i++
       JLT loop, R.i, 15  ; if i < 15, loop

   NOUT R.sum, 1     ; Output: 125

This pattern is essential for array processing.

Array Processing Pattern
~~~~~~~~~~~~~~~~~~~~~~~~

Complete example: read numbers until 0, then sum them:

.. code-block:: python

   from dt31 import DT31, I, L, Label, R

   cpu = DT31(registers=["a", "b", "c"])

   program = [
       # Read numbers and push to stack
       read_loop := Label("read_loop"),
       I.NIN(R.b),
       I.PUSH(R.b),
       I.ADD(R.c, L[1]),         # Count items
       I.JIF(read_loop, R.b),    # Loop if not 0

       # Remove the 0 we just pushed
       I.POP(),
       I.ADD(R.c, L[-1]),

       # Sum from stack
       I.JEQ(output := Label("output"), R.c, L[0]),
       sum_loop := Label("sum_loop"),
       I.POP(R.b),
       I.ADD(R.a, R.b),
       I.ADD(R.c, L[-1]),
       I.JGT(sum_loop, R.c, L[0]),

       # Output result
       output,
       I.NOUT(R.a, L[1]),
   ]

   cpu.run(program)

**Input:** ``10 20 30 0``
**Output:** ``60``

Conditional Logic
-----------------

Comparison Instructions
~~~~~~~~~~~~~~~~~~~~~~~

dt31 provides comparison instructions that store boolean results:

.. code-block:: nasm

   CP 10, R.a
   CP 20, R.b

   LT R.a, R.b, R.c   ; R.c = 1 (a < b is true)
   GT R.a, R.b, R.c   ; R.c = 0 (a > b is false)
   EQ R.a, R.b, R.c   ; R.c = 0 (a == b is false)

Use these with conditional jumps for if-then-else logic.

If-Then-Else Pattern
~~~~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Find maximum of two numbers
   NIN R.a
   NIN R.b

   ; If a > b, jump to use_a
   JGT use_a, R.a, R.b
   ; else: b is max
   CP R.b, R.max
   JMP output

   use_a:
       CP R.a, R.max

   output:
       NOUT R.max, 1

Find Maximum of Three
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Read three numbers
   NIN R.a
   NIN R.b
   NIN R.c

   ; Start with a as max
   CP R.a, R.max

   ; If b > max, update max
   JLE skip_b, R.b, R.max
   CP R.b, R.max

   skip_b:
   ; If c > max, update max
   JLE skip_c, R.c, R.max
   CP R.c, R.max

   skip_c:
   ; Output the maximum
   NOUT R.max, 1

This uses conditional jumps to skip updates when the condition isn't met.

Advanced Jump Instructions
--------------------------

Relative Jumps
~~~~~~~~~~~~~~

Use relative jumps (``RJMP``, ``RJEQ``, etc.) to jump by offset instead of using labels:

.. code-block:: nasm

   CP 5, R.a
   ; Jump forward 2 instructions
   RJMP 2
   CP 10, R.a        ; Skipped
   CP 20, R.a        ; Skipped
   NOUT R.a, 1       ; R.a is still 5

Relative jumps can make code more compact when you don't need descriptive labels, but named labels are usually clearer.

Jump If (JIF)
~~~~~~~~~~~~~

``JIF`` jumps if a value is non-zero (truthy):

.. code-block:: nasm

   CP 1, R.a
   JIF continue, R.a  ; Jumps (1 is truthy)
   CP 99, R.b         ; Skipped

   continue:
   CP 0, R.a
   JIF skip, R.a      ; Doesn't jump (0 is falsy)
   CP 42, R.c         ; Executes

   skip:

This is useful for boolean-style logic.

Complete Example: Fibonacci with Loop
--------------------------------------

An advanced example combining registers and loops:

.. code-block:: python

   from dt31 import DT31, I, L, Label, R

   cpu = DT31(registers=["n", "a", "b", "i"])

   program = [
       # Get N from user
       I.NIN(R.n),

       # Initialize: fib(0)=0, fib(1)=1
       I.CP(L[0], R.a),
       I.CP(L[1], R.b),
       I.CP(L[2], R.i),

       # Base cases
       I.JEQ(output, R.n, L[0]),   # If n==0, output 0
       I.JEQ(output_b, R.n, L[1]), # If n==1, output 1

       # Loop to calculate fib(n)
       loop := Label("loop"),
       I.ADD(R.b, R.a),       # b = a + b (next fib)
       I.SUB(R.b, R.a, R.a),  # a = b - a (swap: old b)
       I.ADD(R.i, L[1]),      # i++
       I.JLE(loop, R.i, R.n), # if i <= n, loop

       # Output result
       output_b := Label("output_b"),
       I.CP(R.b, R.a),
       output := Label("output"),
       I.NOUT(R.a, L[1]),
   ]

   cpu.run(program)

**Try:** Input ``10`` to get ``55`` (the 10th Fibonacci number)
