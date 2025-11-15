Getting Started
===============

Installation
------------

Install dt31 using pip:

.. code-block:: bash

   pip install dt31

Hello World
-----------

Let's start with a simple "Hello World" example:

.. code-block:: python

   from dt31 import DT31, LC, I

   cpu = DT31()

   program = [
       I.OOUT(LC["H"]),  # Output 'H'
       I.OOUT(LC["e"]),  # Output 'e'
       I.OOUT(LC["l"]),  # Output 'l'
       I.OOUT(LC["l"]),  # Output 'l'
       I.OOUT(LC["o"]),  # Output 'o'
   ]

   cpu.run(program)
   # Hello

Basic Concepts
--------------

The CPU
~~~~~~~

The DT31 CPU is the core of the emulator. It manages:

- **Registers**: General-purpose storage (default: ``a``, ``b``, ``c``)
- **Memory**: Fixed-size byte array (default: 256 slots)
- **Stack**: For temporary values and function calls (default: 256 slots)
- **Instruction Pointer**: Tracks current instruction (register ``ip``)

Create a CPU instance:

.. code-block:: python

   from dt31 import DT31

   # Default configuration
   cpu = DT31()

   # Custom configuration
   cpu = DT31(
       registers=['a', 'b', 'c', 'd', 'e'],  # 5 registers
       memory_size=512,  # 512 bytes of memory
       stack_size=512    # 512-slot stack
   )

Operands
~~~~~~~~

dt31 provides several operand types for referencing values:

- **Literals**: ``L[42]`` - Constant value 42
- **Character Literals**: ``LC["A"]`` - Shortcut for ``L[ord("A")]``
- **Registers**: ``R.a`` - Reference to register 'a'
- **Memory (Direct)**: ``M[100]`` - Memory address 100
- **Memory (Indirect)**: ``M[R.a]`` - Memory at address stored in register 'a'
- **Labels**: ``Label("loop")`` - Named jump targets

Instructions
~~~~~~~~~~~~

Instructions are written using the ``I`` namespace (imported as ``from dt31 import I`` or ``from dt31 import instructions as I``):

.. code-block:: python

   from dt31 import I, R, L

   program = [
       I.CP(42, R.a),      # Copy 42 into register a
       I.ADD(R.a, L[10]),  # Add 10 to register a (a = 52)
       I.NOUT(R.a, L[1]),  # Output register a with newline
   ]

Your First Program
------------------

Let's write a simple countdown program. You can write dt31 programs in two ways:

.. tabs::

   .. group-tab:: Python

      Write programs directly using the Python API:

      .. code-block:: python

         from dt31 import DT31, I, Label
         from dt31.operands import R, L

         cpu = DT31()

         program = [
             I.CP(5, R.a),               # Start counter at 5
             loop := Label("loop"),      # Mark loop start
             I.NOUT(R.a, L[1]),          # Print counter
             I.SUB(R.a, L[1]),           # Decrement counter
             I.JGT(loop, R.a, L[0]),     # Jump to loop if a > 0
         ]

         cpu.run(program)
         # 5
         # 4
         # 3
         # 2
         # 1

   .. group-tab:: Assembly

      Write programs in text-based assembly syntax and parse them:

      **Option 1: Parse from string**

      .. code-block:: python

         from dt31 import DT31
         from dt31.parser import parse_program

         cpu = DT31()

         assembly = """
         CP 5, R.a             ; Copy 5 into register a
         loop:
             NOUT R.a, 1       ; Output register a with newline
             SUB R.a, 1        ; Decrement a
             JGT loop, R.a, 0  ; Jump to loop if a > 0
         """

         program = parse_program(assembly)
         cpu.run(program)
         # 5
         # 4
         # 3
         # 2
         # 1

      **Option 2: Execute .dt file directly**

      Save to ``countdown.dt`` and run with the CLI:

      .. code-block:: nasm

         CP 5, R.a
         loop:
             NOUT R.a, 1
             SUB R.a, 1
             JGT loop, R.a, 0

      .. code-block:: bash

         dt31 countdown.dt

Command-Line Options
--------------------

The ``dt31`` command provides several useful options:

Debug Mode
~~~~~~~~~~

Run with the ``--debug`` flag to see step-by-step execution:

.. code-block:: bash

   dt31 --debug countdown.dt

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

Customize CPU settings from the command line:

.. code-block:: bash

   # Use custom memory size
   dt31 --memory 1024 program.dt

   # Specify registers explicitly
   dt31 --registers a,b,c,d,e program.dt

   # Set stack size
   dt31 --stack-size 512 program.dt

Parse Only
~~~~~~~~~~

Validate syntax without executing:

.. code-block:: bash

   dt31 --parse-only program.dt
