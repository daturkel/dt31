Working with Examples
=====================

The dt31 repository includes numerous example programs demonstrating various features and techniques. This guide shows you how to explore and learn from them.

Finding Examples
----------------

Examples are in the `examples/ directory <https://github.com/daturkel/dt31/tree/main/examples>`_ and include both ``.dt`` assembly files and ``.py`` Python programs.

Assembly Examples (.dt)
~~~~~~~~~~~~~~~~~~~~~~~

**Basic programs:**

- ``hello.dt`` - Character output basics
- ``countdown.dt`` - Simple loop with conditional jump
- ``factorial.dt`` - Recursive factorial calculation
- ``factorize.dt`` - Integer factorization algorithm
- ``binomial_dist.dt`` - Statistical simulation

**Run any .dt file:**

.. code-block:: bash

   dt31 examples/countdown.dt

Python Examples (.py)
~~~~~~~~~~~~~~~~~~~~~

**Demonstrations:**

- ``hello_world.py`` - Stack manipulation
- ``fibonacci.py`` - User input and loops
- ``factorial_naive.py`` - Basic factorial
- ``factorial_with_labels.py`` - Using labels effectively
- ``factorial_memoized.py`` - Memoization technique
- ``simple_calculator.py`` - Function reuse pattern
- ``sum_array.py`` - Memory operations
- ``bitwise_operations.py`` - Bitwise instruction demos
- ``conditional_logic.py`` - Comparison and branching
- ``custom_instructions.py`` - Extending dt31

**Run Python examples:**

.. code-block:: bash

   uv run python examples/fibonacci.py
   # or
   python examples/fibonacci.py

Example Walkthroughs
--------------------

Hello World (Stack Version)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This demonstrates stack operations:

.. code-block:: python

   # examples/hello_world.py
   from dt31 import DT31, I, LC, L, M

   hello_world = [
       # Push characters in reverse order
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
       I.POP(M[1]),
       I.SEMP(M[2]),             # Check if empty
       I.OOUT(M[1], M[2]),       # Print char, newline if empty
       I.RJEQ(L[-3], M[2], L[0]), # Loop if not empty
   ]

**Key techniques:**

- Using stack for LIFO ordering
- ``SEMP`` to check stack state
- Relative jumps (``RJEQ``) for short loops
- Memory as temporary storage

**Run with debug:**

.. code-block:: bash

   cd examples
   python -c "from hello_world import *; cpu = DT31(); cpu.run(hello_world, debug=True)"

Countdown
~~~~~~~~~

Basic loop structure:

.. code-block:: nasm

   ; examples/countdown.dt
   CP 5, R.a             ; Counter starts at 5
   loop:
       NOUT R.a, 1       ; Print current value
       SUB R.a, 1        ; Decrement
       JGT loop, R.a, 0  ; Loop if a > 0

**Key concepts:**

- Labels for loop targets
- Conditional jumps (``JGT``)
- Counter pattern

**Try it:**

.. code-block:: bash

   dt31 examples/countdown.dt

Fibonacci Sequence
~~~~~~~~~~~~~~~~~~

Shows register swapping technique:

.. code-block:: python

   # examples/fibonacci.py (simplified)
   fibonacci = [
       I.NIN(R.c),           # Get N from user
       I.CP(L[1], R.b),      # Initialize: a=0, b=1

       loop := Label("loop"),
       I.NOUT(R.a, L[1]),    # Print current
       I.ADD(R.b, R.a),      # b = a + b
       I.SUB(R.b, R.a, R.a), # a = b - a (swap)
       I.SUB(R.c, L[1]),     # Decrement counter
       I.RJGT(loop, R.c, L[0]), # Loop if c > 0
   ]

**Key techniques:**

- Arithmetic swapping without temp variable
- User input with ``NIN``
- Register reuse

**Try with input:**

.. code-block:: bash

   echo "10" | uv run python examples/fibonacci.py

Factorial (Recursive)
~~~~~~~~~~~~~~~~~~~~~

Demonstrates recursion:

.. code-block:: nasm

   ; examples/factorial.dt
   CP 5, R.a
   CALL factorial
   NOUT R.a, 1
   JMP end

   factorial:
       JGT recursive_case, R.a, 1
       CP 1, R.a
       RET

   recursive_case:
       PUSH R.a          ; Save n
       SUB R.a, 1        ; n - 1
       CALL factorial    ; Recursive call
       POP R.b           ; Restore n
       MUL R.a, R.b      ; n * factorial(n-1)
       RET

   end:

**Key concepts:**

- Base case checking
- Stack for preserving values
- Recursive function calls
- ``CALL``/``RET`` mechanics

**Debug it:**

.. code-block:: bash

   dt31 --debug examples/factorial.dt

Simple Calculator
~~~~~~~~~~~~~~~~~

Shows function reuse:

.. code-block:: python

   # examples/simple_calculator.py (simplified)
   calculator = [
       I.NIN(R.a),
       I.NIN(R.b),
       I.CALL(add := Label("add")),
       I.CP(R.a, R.e),

       I.NIN(R.c),
       I.NIN(R.d),
       I.CP(R.c, R.a),
       I.CP(R.d, R.b),
       I.CALL(add),        # Reuse add function

       I.MUL(R.e, R.a),
       I.NOUT(R.e, L[1]),
       I.JMP(end := Label("end")),

       add,
       I.ADD(R.a, R.b),
       I.RET(),

       end,
   ]

**Key patterns:**

- Reusable functions
- Register-based calling convention
- DRY principle (Don't Repeat Yourself)

Sum Array
~~~~~~~~~

Memory and stack together:

.. code-block:: python

   # examples/sum_array.py (simplified)
   sum_array = [
       # Read numbers and push to stack
       read_loop := Label("read_loop"),
       I.NIN(R.b),
       I.PUSH(R.b),
       I.ADD(R.c, L[1]),
       I.JIF(read_loop, R.b),

       # Sum from stack
       sum_loop := Label("sum_loop"),
       I.POP(R.b),
       I.ADD(R.a, R.b),
       I.SUB(R.c, L[1]),
       I.JGT(sum_loop, R.c, L[0]),

       I.NOUT(R.a, L[1]),
   ]

**Key techniques:**

- Dynamic array size (stack-based)
- Sentinel value (0) for termination
- Counter tracking
- ``JIF`` for truthy checks

**Try it:**

.. code-block:: bash

   echo "10 20 30 0" | uv run python examples/sum_array.py

Custom Instructions
~~~~~~~~~~~~~~~~~~~

Extending dt31:

.. code-block:: python

   # examples/custom_instructions.py
   from dt31.instructions import UnaryOperation, BinaryOperation

   class SQUARE(UnaryOperation):
       def __init__(self, a, out=None):
           super().__init__("SQUARE", a, out)

       def _calc(self, cpu):
           return self.a.resolve(cpu) ** 2

   class CLAMP(BinaryOperation):
       def __init__(self, value, maximum, out=None):
           super().__init__("CLAMP", value, maximum, out)

       def _calc(self, cpu):
           val = self.a.resolve(cpu)
           max_val = self.b.resolve(cpu)
           return max(0, min(val, max_val))

**Key concepts:**

- Inheriting from operation base classes
- Implementing ``_calc`` method
- Using custom instructions in assembly

**See also:** :doc:`/tutorials/custom-instructions`

Learning Path
-------------

Beginner
~~~~~~~~

Start with these examples:

1. **hello.dt** - Basic output
2. **countdown.dt** - Loops and jumps
3. **fibonacci.py** - Input and simple algorithms
4. **factorial_with_labels.py** - Using labels effectively

Intermediate
~~~~~~~~~~~~

Move on to:

1. **simple_calculator.py** - Function reuse
2. **sum_array.py** - Memory and stack
3. **conditional_logic.py** - Branching logic
4. **bitwise_operations.py** - Bit manipulation

Advanced
~~~~~~~~

Challenge yourself with:

1. **factorial.dt** - Recursion
2. **factorial_memoized.py** - Optimization techniques
3. **binomial_dist.dt** - Complex algorithms
4. **factorize.dt** - Number theory
5. **custom_instructions.py** - Extending dt31

Modifying Examples
------------------

Experiment by changing examples:

Change Input
~~~~~~~~~~~~

.. code-block:: bash

   # Try different Fibonacci counts
   echo "20" | uv run python examples/fibonacci.py

Modify Code
~~~~~~~~~~~

.. code-block:: bash

   # Copy and edit
   cp examples/countdown.dt my_countdown.dt
   # Edit to count up instead of down
   dt31 my_countdown.dt

Add Debug Output
~~~~~~~~~~~~~~~~

Add ``NOUT`` statements to trace execution:

.. code-block:: nasm

   ; Original
   CP 5, R.a
   MUL R.a, 3

   ; With debug output
   CP 5, R.a
   NOUT R.a, 1        ; Debug: print a
   MUL R.a, 3
   NOUT R.a, 1        ; Debug: print result

Change Parameters
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Original: factorial of 5
   I.CP(L[5], R.a)

   # Modified: factorial of 10
   I.CP(L[10], R.a)

Extracting Patterns
-------------------

Common Patterns in Examples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Loop pattern:**

.. code-block:: nasm

   CP <initial>, R.counter
   loop:
       ; ... body ...
       SUB R.counter, 1
       JGT loop, R.counter, 0

**Function pattern:**

.. code-block:: nasm

   CALL function_name
   JMP end

   function_name:
       ; ... body ...
       RET

   end:

**Input validation:**

.. code-block:: nasm

   NIN R.a
   JLE error, R.a, 0    ; Check if valid
   ; ... process ...
   JMP end

   error:
       OOUT 'E', 0
       OOUT 'r', 0
       OOUT 'r', 1

   end:

Adapting Examples
-----------------

Use examples as templates:

Create a Countdown Timer
~~~~~~~~~~~~~~~~~~~~~~~~

Based on ``countdown.dt``:

.. code-block:: nasm

   ; Get starting value from user
   NIN R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1
       JGE loop, R.a, 0    ; Include zero

Create a Power Function
~~~~~~~~~~~~~~~~~~~~~~~

Based on ``factorial.dt``:

.. code-block:: nasm

   ; Calculate base^exponent
   NIN R.base
   NIN R.exp
   CP 1, R.result

   loop:
       JLE done, R.exp, 0
       MUL R.result, R.base
       SUB R.exp, 1
       JMP loop

   done:
       NOUT R.result, 1

Troubleshooting Examples
-------------------------

Example Won't Run
~~~~~~~~~~~~~~~~~

**Check Python path:**

.. code-block:: bash

   # From project root
   cd dt31
   uv run python examples/fibonacci.py

**Or set PYTHONPATH:**

.. code-block:: bash

   export PYTHONPATH=.
   python examples/fibonacci.py

Missing Dependencies
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Install dt31 in development mode
   pip install -e .

Unexpected Output
~~~~~~~~~~~~~~~~~

**Use debug mode:**

.. code-block:: bash

   dt31 --debug examples/program.dt

**Or in Python:**

.. code-block:: python

   cpu.run(program, debug=True)

Contributing Examples
---------------------

Want to add your own examples?

1. Create a clear, focused example
2. Add comments explaining key concepts
3. Include docstring describing purpose
4. Test thoroughly
5. Submit a pull request

Good examples:

- Demonstrate a specific technique
- Are well-commented
- Are concise (< 50 lines preferred)
- Include expected output in comments

Next Steps
----------

- Browse the `examples directory <https://github.com/daturkel/dt31/tree/main/examples>`_
- Try :doc:`/tutorials/writing-programs` to create your own
- Learn :doc:`debugging-programs` for troubleshooting
- Check :doc:`/tutorials/advanced-topics` for complex patterns
