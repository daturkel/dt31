Debugging Programs
==================

This guide covers techniques for finding and fixing bugs in dt31 programs.

dt31 provides three main approaches to debugging:

1. **CLI Debug Options** - Use ``--debug`` and ``--dump`` flags for quick debugging
2. **Breakpoint Instructions** - Insert ``BRK`` and ``BRKD`` into your programs
3. **Python API** - Programmatically inspect and control execution

CLI debug options
-----------------

Debug mode (``--debug``)
~~~~~~~~~~~~~~~~~~~~

The easiest way to debug is with ``--debug`` mode:

.. code-block:: bash

   dt31 run --debug program.dt

This shows each instruction with its result and the CPU state after execution.

Example output:

.. code-block:: text

   CP(a=5, b=R.a) -> 5
   {'R.a': 5, 'R.ip': 1, 'stack': []}
   ADD(a=R.a, b=3, out=R.a) -> 8
   {'R.a': 8, 'R.ip': 2, 'stack': []}
   8
   NOUT(a=R.a, b=1) -> 0
   {'R.a': 8, 'R.ip': 3, 'stack': []}

**Understanding the Output:**

- Each line shows: ``instruction -> return value``
- The state dict shows registers (``R.name``), instruction pointer (``R.ip``), and stack contents
- Memory is only shown for non-zero addresses (e.g., ``'M[100]': 42``)
- Program output (like from ``NOUT``) appears inline between instructions

CPU dumps (``--dump``)
~~~~~~~~~~~~~~~~~~

Capture complete CPU state to JSON:

.. code-block:: bash

   # Dump on errors
   dt31 run --dump error program.dt

   # Dump on success
   dt31 run --dump success program.dt

   # Always dump
   dt31 run --dump all program.dt

When a crash occurs, you'll see:

.. code-block:: text

   Runtime error: integer division or modulo by zero
   CPU state dumped to: program_crash_20251130_164430.json

This creates JSON files with complete CPU state and error information.

**Dump File Contents:**

The JSON file contains complete CPU state and error details:

.. code-block:: json

   {
     "cpu_state": {
       "registers": {"a": 10, "b": 0, "ip": 2},
       "memory": [0, 0, 0, ...],
       "stack": [],
       "program": "CP 10, R.a\nCP 0, R.b\nDIV R.a, R.b",
       "config": {"memory_size": 256, "stack_size": 256}
     },
     "error": {
       "type": "ZeroDivisionError",
       "message": "integer division or modulo by zero",
       "instruction": {
         "repr": "DIV(a=R.a, b=R.b, out=R.a)",
         "str": "DIV R.a, R.b, R.a"
       },
       "traceback": "..."
     }
   }

Breakpoint instructions
-----------------------

Insert breakpoint instructions directly into your programs for targeted debugging.

BRK
~~~

The ``BRK`` instruction pauses execution, dumps the CPU state, and waits for you to press Enter:

.. code-block:: nasm

   CP 5, R.a
   ADD R.a, 10
   BRK          ; Pause here, show state, wait for Enter
   MUL R.a, 2

When execution reaches ``BRK``, you'll see:

.. code-block:: text

   BRK -> 0
   {'R.a': 15, 'R.ip': 2, 'stack': []}

Press Enter to continue execution.

BRKD
~~~~

The ``BRKD`` instruction dumps state and switches to debug mode for the rest of execution:

.. code-block:: nasm

   CP 5, R.a
   ADD R.a, 10
   BRKD         ; Switch to step-by-step debug mode from here
   MUL R.a, 2
   SUB R.a, 5

After ``BRKD`` executes, every subsequent instruction will print its state before waiting for Enter.

Python API debugging
--------------------

For maximum control, use the Python API to programmatically inspect and control execution.

Step-by-step execution
~~~~~~~~~~~~~~~~~~~~~~

Execute instructions one at a time with full control:

.. code-block:: python

   from dt31 import DT31
   from dt31.exceptions import EndOfProgram
   from dt31.parser import parse_program

   cpu = DT31()
   program = parse_program(open("program.dt").read())
   cpu.load(program)

   # Execute one instruction at a time
   try:
       while True:
           print(f"\n--- Instruction {cpu.ip} ---")
           print(f"Before: {cpu.get_register('a')=}")

           cpu.step(debug=True)

           print(f"After: {cpu.get_register('a')=}")

           # Add breakpoint conditions
           if cpu.get_register('a') > 100:
               print("BREAKPOINT: a > 100")
               break
   except EndOfProgram:
       print("Program finished")

Watching memory changes
~~~~~~~~~~~~~~~~~~~~~~~

Track when specific memory addresses change during execution:

.. code-block:: python

   from dt31 import DT31, I, L, M, R
   from dt31.exceptions import EndOfProgram

   cpu = DT31()
   watched_address = 100
   last_value = None

   program = [
       I.CP(L[42], M[100]),
       I.ADD(M[100], L[10]),
       I.CP(M[100], R.a),
   ]

   cpu.load(program)

   try:
       while True:
           cpu.step()
           current = cpu.get_memory(watched_address)
           if current != last_value:
               print(f"Memory[{watched_address}] changed: {last_value} -> {current}")
               last_value = current
   except EndOfProgram:
       print("Program finished")

This is useful for tracking data corruption or unexpected memory modifications.

Inspecting CPU state
~~~~~~~~~~~~~~~~~~~~

Access CPU state during or after execution:

.. code-block:: python

   from dt31 import DT31, I, L, M, R

   cpu = DT31()
   program = [
       I.CP(L[42], R.a),
       I.ADD(R.a, L[10]),
       I.CP(L[100], M[0]),
   ]

   cpu.run(program)

   # Read registers
   print(cpu.get_register('a'))  # 52
   print(cpu.get_register('b'))  # 0

   # Read memory
   print(cpu.get_memory(0))      # 100

   # Get full state
   state = cpu.state
   print(state)  # Dict with 'M[addr]': value, 'R.name': value, 'stack': [...], 'ip': value
