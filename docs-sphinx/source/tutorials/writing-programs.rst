Writing Programs
================

dt31 programs can be written in two ways: as ``.dt`` text files using assembly syntax or programmatically using the Python API. This tutorial covers both approaches and how to work with each.

Two Ways to Write Programs
---------------------------

Assembly and Python are equivalent - you can convert between them freely:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Assembly (``.dt`` file)
     - Python API
   * - .. code-block:: nasm

          CP 5, R.a
          loop:
              NOUT R.a, 1
              SUB R.a, 1
              JGT loop, R.a, 0

     - .. code-block:: python

          from dt31 import DT31, I, L, Label, R

          cpu = DT31()
          program = [
              I.CP(5, R.a),
              loop := Label("loop"),
              I.NOUT(R.a, L[1]),
              I.SUB(R.a, L[1]),
              I.JGT(loop, R.a, L[0]),
          ]
          cpu.run(program)

Both produce the same output: ``5 4 3 2 1``

**When to use each:**

- **Assembly (.dt files)**: Best for standalone programs, learning, and when you want human-readable text files
- **Python API**: Best for generating programs dynamically, integrating with Python code, or meta-programming

Assembly Syntax
---------------

Basic Syntax Rules
~~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; This is a comment
   INSTRUCTION operand1, operand2, operand3

   ; Example:
   CP 42, R.a        ; Copy 42 into register a
   ADD R.a, 10       ; Add 10 to register a
   NOUT R.a, 1       ; Output: 52

**Rules:**

- Instructions are **case-insensitive** (``ADD``, ``add``, and ``Add`` all work)
- Operands are separated by commas (spaces around commas are optional)
- Comments start with ``;`` and continue to end of line
- Blank lines and indentation are ignored (use them for readability)
- Register and label names are **case-sensitive**

Labels
~~~~~~

Labels mark positions in code for jumps and function calls:

.. code-block:: nasm

   ; Label on its own line
   loop:
       ADD R.a, 1
       JLT loop, R.a, 10

   ; Label on same line as instruction
   start: CP 0, R.a

Label names must contain only alphanumeric characters and underscores.

Operand Types
~~~~~~~~~~~~~

Assembly syntax differs from Python for operands:

.. list-table::
   :header-rows: 1
   :widths: 20 30 30 20

   * - Type
     - Assembly Syntax
     - Python Syntax
     - Description
   * - Numeric literal
     - ``42``, ``-5``
     - ``L[42]``, ``L[-5]``
     - Integer constants
   * - Character literal
     - ``'A'``, ``'!'``
     - ``LC["A"]``, ``LC["!"]``
     - Character (ASCII)
   * - Register
     - ``R.a``
     - ``R.a``
     - CPU register
   * - Memory (direct)
     - ``[100]`` or ``M[100]``
     - ``M[100]``
     - Memory address 100
   * - Memory (indirect)
     - ``[R.a]`` or ``M[R.a]``
     - ``M[R.a]``
     - Memory at address in R.a
   * - Label
     - ``loop``
     - ``Label("loop")``
     - Jump target

**Key differences:**

1. **Literals**: In assembly, bare numbers are literals (no ``L[...]`` wrapper needed)
2. **Characters**: Use single quotes ``'A'`` instead of ``LC["A"]``
3. **Memory**: The ``M`` prefix is optional in assembly (both ``[100]`` and ``M[100]`` work)
4. **Labels**: Bare identifiers are labels in assembly (no ``Label(...)`` constructor needed)
5. **Registers**: The ``R.`` prefix is **required** in both syntaxes

Running Assembly Files
~~~~~~~~~~~~~~~~~~~~~~

Execute ``.dt`` files directly with the CLI:

.. code-block:: bash

   dt31 program.dt

For more CLI options, see :doc:`cli-guide`.

Python API
----------

Creating Programs
~~~~~~~~~~~~~~~~~

Programs are lists of instructions, easily accessed using the ``I`` namespace or imported from ``dt31.instructions``:

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()

   program = [
       I.CP(L[42], R.a),      # Copy 42 to register a
       I.ADD(R.a, L[8]),      # Add 8 to register a
       I.NOUT(R.a, L[1]),     # Output result with newline
   ]

   cpu.run(program)  # Output: 50

Operands in Python
~~~~~~~~~~~~~~~~~~

**Literals:**

.. code-block:: python

   from dt31 import I, L, LC, R

   program = [
       I.CP(L[42], R.a),           # Numeric literal
       I.ADD(R.a, L[-5]),          # Negative number
       I.OOUT(LC["H"], L[0]),      # Character literal
   ]

``LC`` is a convenience: ``LC["A"]`` equals ``L[ord("A")]``. However, `LC` literals do maintain metadata denoting that they represent a character so that they are displayed as characters during debugging.

**Registers:**

.. code-block:: python

   from dt31 import I, L, R

   program = [
       I.CP(L[10], R.a),      # R.a = 10
       I.CP(R.a, R.b),        # R.b = R.a
       I.ADD(R.a, R.b),       # R.a = R.a + R.b
   ]

**Memory:**

.. code-block:: python

   from dt31 import I, L, M, R

   program = [
       # Direct memory access
       I.CP(L[42], M[100]),       # Store 42 at address 100
       I.CP(M[100], R.a),         # Load from address 100

       # Indirect memory access
       I.CP(L[100], R.a),         # R.a = 100 (the address)
       I.CP(L[99], M[R.a]),       # Store 99 at memory[R.a]
   ]

Labels with the Walrus Operator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use Python's walrus operator (``:=``) to define and use labels in one line:

.. code-block:: python

   from dt31 import DT31, I, L, Label, R

   cpu = DT31()

   program = [
       I.CP(L[5], R.a),
       loop := Label("loop"),      # Define and assign
       I.NOUT(R.a, L[1]),
       I.SUB(R.a, L[1]),
       I.JGT(loop, R.a, L[0]),     # Use the label
   ]

   cpu.run(program)

Converting Between Formats
---------------------------

Parse Assembly from Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``parse_program()`` to load assembly text:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   cpu = DT31()

   assembly = """
   CP 5, R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1
       JGT loop, R.a, 0
   """

   program = parse_program(assembly)
   cpu.run(program)

Convert Python to Assembly Text
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use ``program_to_text()`` to generate ``.dt`` files:

.. code-block:: python

   from dt31 import I, L, Label, R
   from dt31.assembler import program_to_text

   program = [
       I.CP(L[5], R.a),
       loop := Label("loop"),
       I.NOUT(R.a, L[1]),
       I.SUB(R.a, L[1]),
       I.JGT(loop, R.a, L[0]),
   ]

   text = program_to_text(program)
   print(text)

Output:

.. code-block:: nasm

       CP 5, R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1, R.a
       JGT loop, R.a, 0

Complete Example: Factorial
----------------------------

Here's the same factorial program in both syntaxes:

Assembly Version
~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; factorial.dt
   ; Calculate factorial of 5

   CP 5, R.a
   CALL factorial
   NOUT R.a, 1
   JMP end

   factorial:
       ; Base case: if n <= 1, return 1
       JGT recursive_case, R.a, 1
       CP 1, R.a
       RET

   recursive_case:
       PUSH R.a                 ; Save n
       SUB R.a, 1               ; n-1
       CALL factorial           ; factorial(n-1)
       POP R.b                  ; Restore n
       MUL R.a, R.b             ; n * factorial(n-1)
       RET

   end:

Run with: ``dt31 factorial.dt``

Python Version
~~~~~~~~~~~~~~

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

   cpu.run(program)  # Output: 120

Both produce: ``120``

Working with CPU State
----------------------

Customizing the CPU
~~~~~~~~~~~~~~~~~~~

Configure CPU settings when creating instances:

.. code-block:: python

   from dt31 import DT31

   # Custom registers
   cpu = DT31(registers=["x", "y", "z", "counter"])

   # Custom memory and stack size too
   cpu = DT31(
       registers=["a", "b", "c", "d", "e"],
       memory_size=512,
       stack_size=512
   )

Inspecting State
~~~~~~~~~~~~~~~~

Access CPU state during or after execution:

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[42], R.a),
       I.ADD(R.a, L[8]),
   ]

   cpu.run(program)

   # Read register values
   print(cpu.get_register('a'))  # 50

   # Read/write memory
   cpu.set_memory(100, 255)
   print(cpu.get_memory(100))    # 255

   # Get full state snapshot
   state = cpu.state
   print(state['registers'])     # {'a': 50, 'b': 0, 'c': 0, 'ip': 2}

Step-by-Step Execution
~~~~~~~~~~~~~~~~~~~~~~~

Execute one instruction at a time:

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[5], R.a),
       I.ADD(R.a, L[10]),
       I.NOUT(R.a, L[1]),
   ]

   # Load program without running
   cpu.load(program)

   # Execute one step at a time
   for _ in program:
       cpu.step(debug=True)  # Prints each instruction

Or use ``cpu.run(program, debug=True)`` to debug the entire program.

Next Steps
----------

- Learn :doc:`advanced-topics` like recursion and stack manipulation
- Explore :doc:`custom-instructions` to extend dt31
- See :doc:`cli-guide` for command-line options
- Check :doc:`/reference/assembly-syntax` for the formal grammar
- Browse :doc:`/how-to/parsing-assembly` for conversion details
