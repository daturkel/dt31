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

Let's write a simple countdown program:

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

Assembly Syntax
---------------

You can also write programs in text-based assembly syntax:

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

Using the Command Line
----------------------

Save your assembly code to a ``.dt`` file and run it directly:

.. code-block:: bash

   # Create countdown.dt
   cat > countdown.dt << 'EOF'
   CP 5, R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1
       JGT loop, R.a, 0
   EOF

   # Execute it
   dt31 countdown.dt

Debug Mode
~~~~~~~~~~

Run with the ``--debug`` flag to see step-by-step execution:

.. code-block:: bash

   dt31 --debug countdown.dt

Next Steps
----------

- Check out the :doc:`tutorials/index` for more detailed examples
- Browse the :doc:`api/index` for complete documentation
- Explore the `examples directory <https://github.com/daturkel/dt31/tree/main/examples>`_ on GitHub
