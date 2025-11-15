CPU API
=======

The ``dt31.cpu`` module contains the ``DT31`` class - the virtual CPU that executes programs.

.. automodule:: dt31.cpu
   :members:
   :undoc-members:
   :show-inheritance:

Overview
--------

The ``DT31`` class represents a simple CPU with:

- **Registers**: Named storage locations (default: a, b, c)
- **Memory**: Fixed-size integer array (default: 256 bytes)
- **Stack**: For temporary values and function calls (default: 256 slots)
- **Instruction Pointer (IP)**: Tracks current instruction

Creating a CPU
--------------

Basic
~~~~~

.. code-block:: python

   from dt31 import DT31

   cpu = DT31()  # Default: 3 registers, 256 memory, 256 stack

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   cpu = DT31(
       registers=["a", "b", "c", "d", "e"],  # 5 registers
       memory_size=512,                       # 512 bytes
       stack_size=1024,                       # 1024 stack slots
       wrap_memory=False                      # Don't wrap memory access
   )

Running Programs
----------------

Execute Entire Program
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[10], R.a),
       I.ADD(R.a, L[5]),
       I.NOUT(R.a, L[1]),
   ]

   cpu.run(program)                # Run to completion
   cpu.run(program, debug=True)    # Run with debug output

Step-by-Step Execution
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   cpu = DT31()
   cpu.load(program)  # Load without running

   while not cpu.halted:
       cpu.step(debug=True)  # Execute one instruction

Accessing State
---------------

Registers
~~~~~~~~~

.. code-block:: python

   # Read register
   value = cpu.get_register('a')

   # Write register
   cpu.set_register('a', 42)

Memory
~~~~~~

.. code-block:: python

   # Read memory
   value = cpu.get_memory(100)

   # Write memory
   cpu.set_memory(100, 255)

Complete State
~~~~~~~~~~~~~~

.. code-block:: python

   state = cpu.state  # Returns dict

   print(state['registers'])  # All registers
   print(state['memory'])     # Entire memory array
   print(state['stack'])      # Stack contents
   print(state['ip'])         # Instruction pointer
   print(state['halted'])     # Execution status

Properties
----------

``halted`` (bool)
~~~~~~~~~~~~~~~~~

Whether the CPU has finished executing.

.. code-block:: python

   if cpu.halted:
       print("Program finished")

``ip`` (int)
~~~~~~~~~~~~

Current instruction pointer.

.. code-block:: python

   print(f"At instruction {cpu.ip}")

``state`` (dict)
~~~~~~~~~~~~~~~~

Complete CPU state snapshot.

.. code-block:: python

   snapshot = cpu.state
   # Save for later analysis

Key Methods
-----------

``run(program, debug=False)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Execute a complete program.

**Parameters:**
- ``program`` (list): List of Instruction objects
- ``debug`` (bool): Enable step-by-step debug output

``step(debug=False)``
~~~~~~~~~~~~~~~~~~~~~

Execute one instruction.

**Parameters:**
- ``debug`` (bool): Print instruction and state

``load(program)``
~~~~~~~~~~~~~~~~~

Load a program without running it.

**Parameters:**
- ``program`` (list): List of Instruction objects

``get_register(name)``
~~~~~~~~~~~~~~~~~~~~~~

Read a register value.

**Parameters:**
- ``name`` (str): Register name

**Returns:** int

``set_register(name, value)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write a register value.

**Parameters:**
- ``name`` (str): Register name
- ``value`` (int): Value to write

``get_memory(address)``
~~~~~~~~~~~~~~~~~~~~~~~

Read from memory.

**Parameters:**
- ``address`` (int): Memory address

**Returns:** int

``set_memory(address, value)``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Write to memory.

**Parameters:**
- ``address`` (int): Memory address
- ``value`` (int): Value to write

Configuration
-------------

The CPU configuration affects program behavior:

Registers
~~~~~~~~~

- **Auto-detection**: If not specified, registers are created as needed
- **Custom names**: Any valid Python identifier
- **Case-sensitive**: ``a`` and ``A`` are different registers

Memory
~~~~~~

- **Fixed size**: Configured at creation
- **Zero-initialized**: All values start at 0
- **Access errors**: Out-of-bounds access raises ``MemoryAccessError``
- **Wrapping**: Optional (``wrap_memory=True``)

Stack
~~~~~

- **LIFO**: Last-in, first-out
- **Separate from memory**: Not accessible via memory addresses
- **Overflow protection**: Raises ``StackOverflowError`` when full
- **Underflow protection**: Raises ``StackUnderflowError`` when empty

Examples
--------

Fibonacci Calculator
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31, I, L, Label, R

   cpu = DT31(registers=["n", "a", "b", "i"])

   program = [
       I.NIN(R.n),
       I.CP(L[0], R.a),
       I.CP(L[1], R.b),
       I.CP(L[2], R.i),

       I.JEQ(output := Label("output"), R.n, L[0]),
       I.JEQ(output_b := Label("output_b"), R.n, L[1]),

       loop := Label("loop"),
       I.ADD(R.b, R.a),
       I.SUB(R.b, R.a, R.a),
       I.ADD(R.i, L[1]),
       I.JLE(loop, R.i, R.n),

       output_b,
       I.CP(R.b, R.a),
       output,
       I.NOUT(R.a, L[1]),
   ]

   cpu.run(program)

State Inspection
~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[42], R.a),
       I.CP(L[100], M[0]),
       I.PUSH(R.a),
   ]

   cpu.run(program)

   # Inspect final state
   print(f"Register a: {cpu.get_register('a')}")
   print(f"Memory[0]: {cpu.get_memory(0)}")
   print(f"Stack: {cpu.state['stack']}")

See Also
--------

- :doc:`/tutorials/writing-programs` - Using the API
- :doc:`/explanation/architecture` - How the CPU works
- :doc:`api-instructions` - Available instructions
