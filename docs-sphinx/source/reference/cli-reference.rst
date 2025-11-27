CLI Reference
=============

Complete reference for the ``dt31`` command-line interface.

Synopsis
--------

.. code-block:: text

   dt31 [OPTIONS] FILE

Basic Usage
-----------

.. code-block:: bash

   dt31 program.dt

Global Options
--------------

``--help``, ``-h``
~~~~~~~~~~~~~~~~~~

Show help message and exit.

.. code-block:: bash

   dt31 --help

``--version``
~~~~~~~~~~~~~

Show version number and exit.

.. code-block:: bash

   dt31 --version

Execution Options
-----------------

``--debug``, ``-d``
~~~~~~~~~~~~~~~~~~~

Enable debug mode with step-by-step execution output.

.. code-block:: bash

   dt31 --debug program.dt
   dt31 -d program.dt

**Output includes:**

- Instruction index and assembly text
- Register state after each instruction
- Program output inline
- Control flow (jumps, calls, returns)

**Example output:**

.. code-block:: text

   [0] CP 5, R.a
   Registers: {'a': 5, 'b': 0, 'c': 0, 'ip': 1}

   [1] NOUT R.a, 1
   5
   Registers: {'a': 5, 'b': 0, 'c': 0, 'ip': 2}

``--parse-only``, ``-p``
~~~~~~~~~~~~~~~~~~~~~~~~~

Validate syntax without executing the program.

.. code-block:: bash

   dt31 --parse-only program.dt
   dt31 -p program.dt

**Exit codes:**

- ``0`` - Valid syntax
- ``1`` - Syntax errors

**Use cases:**

- Pre-flight checks
- Syntax validation in CI/CD
- Editor integration

CPU Configuration
-----------------

``--registers NAMES``
~~~~~~~~~~~~~~~~~~~~~

Specify custom register names (comma-separated).

.. code-block:: bash

   dt31 --registers a,b,c,d,e program.dt
   dt31 --registers x,y,z,counter,temp program.dt

**Default behavior:** Auto-detect registers from program.

**When to use:**

- When you want specific register names
- To catch typos (using undefined register will error)

``--memory SIZE``
~~~~~~~~~~~~~~~~~

Set memory size in bytes (integer).

.. code-block:: bash

   dt31 --memory 512 program.dt
   dt31 --memory 1024 program.dt

**Default:** ``256``

**When to use:**

- Programs that need more than 256 bytes
- Large data structures
- Avoiding ``MemoryAccessError``

``--stack-size SIZE``
~~~~~~~~~~~~~~~~~~~~~

Set stack size (integer).

.. code-block:: bash

   dt31 --stack-size 512 program.dt
   dt31 --stack-size 1024 program.dt

**Default:** ``256``

**When to use:**

- Deep recursion
- Heavy stack usage
- Avoiding ``StackOverflowError``

Custom Instructions
-------------------

``--custom-instructions PATH``, ``-i PATH``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Load custom instruction definitions from a Python file.

.. code-block:: bash

   dt31 --custom-instructions my_ops.py program.dt
   dt31 -i extensions.py program.dt

**Requirements:**

- Python file must export ``INSTRUCTIONS`` dict
- Instruction names must be UPPERCASE
- File is executed as Python code

**Example file:**

.. code-block:: python

   # my_ops.py
   from dt31.instructions import UnaryOperation
   from dt31.operands import Operand, Reference

   class TRIPLE(UnaryOperation):
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("TRIPLE", a, out)

       def _calc(self, cpu) -> int:
           return self.a.resolve(cpu) * 3

   INSTRUCTIONS = {"TRIPLE": TRIPLE}

**Security Warning:** Only load trusted files (executes arbitrary Python code).

CPU State Dumps
---------------

``--dump MODE``
~~~~~~~~~~~~~~~

Control when to dump CPU state to JSON.

.. code-block:: bash

   dt31 --dump error program.dt     # Dump on errors
   dt31 --dump success program.dt   # Dump on success
   dt31 --dump all program.dt       # Always dump
   dt31 --dump none program.dt      # Never dump (default)

**Modes:**

- ``error`` - Dump only when program crashes
- ``success`` - Dump only when program completes successfully
- ``all`` - Dump on both success and error
- ``none`` - Never dump (default)

**Default filename format:** ``{basename}_{status}_{timestamp}.json``

**Example filenames:**

- ``program_error_20231113_143022.json``
- ``factorial_success_20231113_144530.json``

``--dump-file PATH``
~~~~~~~~~~~~~~~~~~~~

Specify custom dump file path.

.. code-block:: bash

   dt31 --dump error --dump-file debug.json program.dt

**Note:** Requires ``--dump`` to be set to something other than ``none``.

Dump File Format
~~~~~~~~~~~~~~~~

JSON file with complete CPU state:

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

Exit Codes
----------

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Code
     - Meaning
   * - ``0``
     - Success
   * - ``1``
     - Parse error or runtime error
   * - ``2``
     - File not found or invalid arguments

**Usage in scripts:**

.. code-block:: bash

   if dt31 program.dt; then
       echo "Success"
   else
       echo "Failed with code $?"
   fi

Input/Output
------------

Standard Streams
~~~~~~~~~~~~~~~~

- **stdin** - Used by ``NIN`` and ``OIN`` instructions
- **stdout** - Used by ``NOUT`` and ``OOUT`` instructions
- **stderr** - Used for debug output and error messages

Redirecting Output
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Redirect program output
   dt31 program.dt > output.txt

   # Redirect errors only
   dt31 program.dt 2> errors.txt

   # Redirect both
   dt31 program.dt > output.txt 2>&1

Piping Input
~~~~~~~~~~~~

.. code-block:: bash

   # Pipe from echo
   echo "5" | dt31 factorial.dt

   # Pipe from file
   cat input.txt | dt31 process.dt

   # Pipe from another program
   generate_data | dt31 process.dt

Examples
--------

Basic Execution
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run a program
   dt31 hello.dt

   # With debug output
   dt31 --debug hello.dt

   # Validate syntax
   dt31 --parse-only hello.dt

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Large memory
   dt31 --memory 2048 bigdata.dt

   # Custom registers
   dt31 --registers x,y,z,temp complex.dt

   # Both
   dt31 --registers a,b,c --memory 512 --stack-size 512 program.dt

Debugging
~~~~~~~~~

.. code-block:: bash

   # Debug with state dumps on error
   dt31 --debug --dump error program.dt

   # Dump to specific file
   dt31 --dump all --dump-file state.json program.dt

Custom Instructions
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Load extensions
   dt31 -i my_instructions.py program.dt

   # With debug
   dt31 -i my_instructions.py --debug program.dt

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Validate all .dt files
   for f in *.dt; do
       dt31 --parse-only "$f" && echo "$f: OK"
   done

   # Run all programs
   for f in examples/*.dt; do
       echo "Running $f"
       dt31 "$f"
   done

CI/CD Integration
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Validation step
   dt31 --parse-only program.dt || exit 1

   # Test step with input
   echo "5" | dt31 program.dt > output.txt
   diff expected.txt output.txt || exit 1

Environment
-----------

No environment variables are currently used by dt31.

Files
-----

Input Files
~~~~~~~~~~~

- ``.dt`` - Assembly source files (required)
- ``.py`` - Custom instruction files (optional, with ``-i``)

Output Files
~~~~~~~~~~~~

- Dump files (JSON) - Created when using ``--dump``

Configuration Files
~~~~~~~~~~~~~~~~~~~

No configuration files are used. All configuration is via command-line flags.

Common Patterns
---------------

Development Workflow
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Validate
   dt31 -p program.dt

   # 2. Debug
   dt31 --debug program.dt

   # 3. Production run
   dt31 program.dt

Testing
~~~~~~~

.. code-block:: bash

   # Test with input file
   dt31 program.dt < test_input.txt > actual.txt
   diff expected.txt actual.txt

   # Test multiple inputs
   for input in tests/input_*.txt; do
       dt31 program.dt < "$input"
   done

Error Diagnosis
~~~~~~~~~~~~~~~

.. code-block:: bash

   # Capture error with dump
   dt31 --dump error --debug program.dt 2> error.log

   # Check exit code
   dt31 program.dt
   echo "Exit code: $?"

Limitations
-----------

File Size
~~~~~~~~~

No explicit limit, but very large programs may be slow to parse.

Path Length
~~~~~~~~~~~

Standard filesystem path limits apply.

Custom Instructions
~~~~~~~~~~~~~~~~~~~

Custom instruction files are loaded via ``exec()``, which has the same limitations as regular Python modules.

Comparison with Python API
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - CLI
     - Python Equivalent
   * - ``dt31 program.dt``
     - ``cpu.run(parse_program(open("program.dt").read()))``
   * - ``--debug``
     - ``cpu.run(program, debug=True)``
   * - ``--parse-only``
     - ``parse_program(text)`` (no run)
   * - ``--registers a,b,c``
     - ``DT31(registers=["a", "b", "c"])``
   * - ``--memory 512``
     - ``DT31(memory_size=512)``
   * - ``--stack-size 512``
     - ``DT31(stack_size=512)``
   * - ``-i custom.py``
     - ``parse_program(text, custom_instructions=INSTRUCTIONS)``

See Also
--------

- :doc:`/cli-guide` - Tutorial and examples
- :doc:`/reference/instruction-set` - Available instructions
- :doc:`/reference/assembly-syntax` - Assembly language syntax
- :doc:`/debugging-programs` - Debugging techniques
