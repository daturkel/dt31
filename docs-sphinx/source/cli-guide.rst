Command-Line Interface
======================

The ``dt31`` command-line tool lets you execute ``.dt`` assembly files directly, with options for debugging, custom configuration, and CPU state dumps.

Basic Usage
-----------

Run any ``.dt`` file:

.. code-block:: bash

   dt31 program.dt

Example program (``countdown.dt``):

.. code-block:: nasm

   ; Count down from 5
   CP 5, R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1
       JGT loop, R.a, 0

Run it:

.. code-block:: bash

   $ dt31 countdown.dt
   5
   4
   3
   2
   1

Debug Mode
----------

The ``--debug`` (or ``-d``) flag enables step-by-step execution with state inspection:

.. code-block:: bash

   dt31 --debug countdown.dt

**Output:**

.. code-block:: text

   [0] CP 5, R.a
   Registers: {'a': 5, 'b': 0, 'c': 0, 'ip': 1}

   [1] NOUT R.a, 1
   5
   Registers: {'a': 5, 'b': 0, 'c': 0, 'ip': 2}

   [2] SUB R.a, 1, R.a
   Registers: {'a': 4, 'b': 0, 'c': 0, 'ip': 3}

   [3] JGT loop, R.a, 0
   Registers: {'a': 4, 'b': 0, 'c': 0, 'ip': 1}

   ...

Debug mode shows:

- Instruction index and assembly text
- Program output
- Register state after each instruction
- Jumps and control flow

This is invaluable for understanding program execution and finding bugs.

Parse-Only Mode
---------------

Validate syntax without executing:

.. code-block:: bash

   dt31 --parse-only program.dt

or

.. code-block:: bash

   dt31 -p program.dt

**Use cases:**

- Check syntax before running
- Validate generated assembly
- Part of a build pipeline

If parsing succeeds, the command exits with code 0. If there are syntax errors, it prints the error and exits with code 1.

CPU Configuration
-----------------

Customize the CPU's hardware configuration:

Custom Registers
~~~~~~~~~~~~~~~~

Specify registers with ``--registers``:

.. code-block:: bash

   dt31 --registers x,y,z,counter program.dt

This creates registers ``R.x``, ``R.y``, ``R.z``, and ``R.counter``.

**Note:** If you don't specify registers, dt31 auto-detects them from your program (any register referenced becomes available).

Memory Size
~~~~~~~~~~~

Set memory size in bytes with ``--memory``:

.. code-block:: bash

   dt31 --memory 1024 program.dt

Default is 256 bytes. Use larger memory for programs with lots of data.

Stack Size
~~~~~~~~~~

Set stack size with ``--stack-size``:

.. code-block:: bash

   dt31 --stack-size 512 program.dt

Default is 256 slots. Increase for deeply recursive programs.

Combined Configuration
~~~~~~~~~~~~~~~~~~~~~~

Combine all options:

.. code-block:: bash

   dt31 --registers a,b,c,d,e --memory 1024 --stack-size 512 program.dt

Custom Instructions
-------------------

Load custom instructions from a Python file:

.. code-block:: bash

   dt31 --custom-instructions my_instructions.py program.dt

or

.. code-block:: bash

   dt31 -i my_instructions.py program.dt

The Python file must export an ``INSTRUCTIONS`` dict:

.. code-block:: python

   # my_instructions.py
   from dt31.instructions import UnaryOperation
   from dt31.operands import Operand, Reference

   class TRIPLE(UnaryOperation):
       """Multiply a value by 3."""
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("TRIPLE", a, out)

       def _calc(self, cpu) -> int:
           return self.a.resolve(cpu) * 3

   # Required: export INSTRUCTIONS dict
   INSTRUCTIONS = {
       "TRIPLE": TRIPLE,
   }

Then use in your ``.dt`` file:

.. code-block:: nasm

   CP 5, R.a
   TRIPLE R.a        ; a = 15
   NOUT R.a, 1

**Security Warning:** This executes arbitrary Python code. Only load trusted files.

CPU State Dumps
---------------

Capture CPU state to JSON files for debugging crashes or analyzing execution:

Dump Modes
~~~~~~~~~~

Use ``--dump`` to control when state is saved:

.. code-block:: bash

   # Dump only on errors
   dt31 --dump error program.dt

   # Dump only on successful completion
   dt31 --dump success program.dt

   # Dump always (both success and error)
   dt31 --dump all program.dt

   # Never dump (default)
   dt31 --dump none program.dt

Dump Files
~~~~~~~~~~

By default, dumps are saved to ``{filename}_{status}_{timestamp}.json``:

.. code-block:: bash

   dt31 --dump error crash.dt
   # Creates: crash_error_20231113_143022.json (if it crashes)

Specify a custom filename with ``--dump-file``:

.. code-block:: bash

   dt31 --dump error --dump-file debug_state.json program.dt

Dump Contents
~~~~~~~~~~~~~

Dump files contain complete CPU state:

.. code-block:: javascript

   {
     "cpu_state": {
       "registers": {"a": 10, "b": 0, "ip": 2},
       "memory": [0, 0, 0, ...],  // Full memory array
       "stack": [],
       "program": "CP 10, R.a\nCP 0, R.b\nDIV R.a, R.b",
       "config": {
         "memory_size": 256,
         "stack_size": 256,
         "wrap_memory": false
       }
     },
     "error": {
       "type": "ZeroDivisionError",
       "message": "integer division or modulo by zero",
       "instruction": {
         "repr": "DIV(a=R.a, b=R.b, out=R.a)",
         "str": "DIV R.a, R.b, R.a"
       },
       "traceback": "..."  // Full traceback string
     }
   }

**Use cases:**

- Debug crashes (``--dump error``)
- Verify final state (``--dump success``)
- Compare states across runs
- Share reproducible bugs

Example: Debugging a Crash
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   dt31 --dump error --debug crash.dt

This combines debug output with error dumps, giving you both step-by-step execution and final state.

Complete Examples
-----------------

Basic Execution
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Simple run
   dt31 factorial.dt

   # With debug output
   dt31 --debug factorial.dt

   # Validate only
   dt31 --parse-only factorial.dt

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Large memory
   dt31 --memory 2048 bigdata.dt

   # Many registers
   dt31 --registers a,b,c,d,e,f,g,h complex.dt

   # Deep recursion
   dt31 --stack-size 1024 recursive.dt

Development Workflow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Validate syntax
   dt31 --parse-only program.dt

   # 2. Run with debug
   dt31 --debug program.dt

   # 3. Production run with error dumps
   dt31 --dump error program.dt

Custom Instructions
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Use custom instructions
   dt31 -i extensions.py program.dt

   # Combined with debug
   dt31 -i extensions.py --debug program.dt

Help and Version
----------------

Get help:

.. code-block:: bash

   dt31 --help

Show version:

.. code-block:: bash

   dt31 --version

Exit Codes
----------

The CLI uses standard exit codes:

- **0**: Success
- **1**: Parse error or runtime error
- **2**: File not found or invalid arguments

Useful for scripting:

.. code-block:: bash

   if dt31 --parse-only program.dt; then
       echo "Valid syntax"
       dt31 program.dt
   else
       echo "Syntax error"
       exit 1
   fi

Tips and Tricks
---------------

Redirecting Output
~~~~~~~~~~~~~~~~~~

Redirect program output to files:

.. code-block:: bash

   dt31 program.dt > output.txt
   dt31 program.dt 2> errors.txt
   dt31 program.dt > output.txt 2>&1  # Both stdout and stderr

Piping Input
~~~~~~~~~~~~

Pipe input to programs:

.. code-block:: bash

   echo "5" | dt31 factorial.dt
   cat numbers.txt | dt31 sum.dt

Batch Processing
~~~~~~~~~~~~~~~~

Process multiple files:

.. code-block:: bash

   for f in *.dt; do
       echo "Running $f"
       dt31 "$f"
   done

Quick Syntax Check
~~~~~~~~~~~~~~~~~~

Check all files in a directory:

.. code-block:: bash

   find . -name "*.dt" -exec dt31 --parse-only {} \;

Common Issues
-------------

"Register not found"
~~~~~~~~~~~~~~~~~~~~

If you see this error, either:

1. Let dt31 auto-detect registers (don't use ``--registers``)
2. Or include all registers you use in ``--registers``

.. code-block:: bash

   # Auto-detect (recommended)
   dt31 program.dt

   # Or specify all
   dt31 --registers a,b,c,temp,counter program.dt

"Stack overflow"
~~~~~~~~~~~~~~~~

Increase stack size:

.. code-block:: bash

   dt31 --stack-size 1024 program.dt

"Memory access out of bounds"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Increase memory size:

.. code-block:: bash

   dt31 --memory 512 program.dt

Custom instruction not found
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure:

1. Your Python file exports ``INSTRUCTIONS`` dict
2. Instruction names are UPPERCASE
3. File path is correct

.. code-block:: bash

   dt31 -i ./instructions.py program.dt  # Relative path
   dt31 -i /full/path/instructions.py program.dt  # Absolute path
