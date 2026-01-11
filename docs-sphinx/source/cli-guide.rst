Command-Line Interface
======================

The dt31 CLI provides tools for executing, validating, and formatting dt31 assembly programs.
After installing dt31, the ``dt31`` command becomes available in your terminal.

Commands Overview
-----------------

The dt31 CLI has three main commands:

- **run**: Execute ``.dt`` assembly files
- **check**: Validate syntax without executing
- **format**: Format assembly files with consistent style

Use ``--help`` with any command to see all available options::

   dt31 --help
   dt31 run --help
   dt31 check --help
   dt31 format --help

Run
---

Execute ``.dt`` assembly files with the ``run`` command.

Basic Usage
~~~~~~~~~~~

::

   dt31 run program.dt

This parses and executes ``program.dt``. The CLI automatically detects which registers your program
uses and creates a CPU with those registers.

Options
~~~~~~~

**Debug Mode**

Use ``-d`` or ``--debug`` to enable step-by-step execution output::

   dt31 run --debug program.dt

This prints each instruction before execution and shows the CPU state.

**CPU Configuration**

Configure the CPU's memory and stack size::

   dt31 run --memory 512 program.dt       # Use 512 slots of memory (default: 256)
   dt31 run --stack-size 512 program.dt   # Use stack size of 512 (default: 256)

**Register Configuration**

By default, the CLI auto-detects which registers your program uses. To override this::

   dt31 run --registers a,b,c,d,e program.dt

The CLI will validate that all registers used in your program are included in the list.

**Custom Instructions**

Load custom instruction definitions from a Python file::

   dt31 run --custom-instructions my_instructions.py program.dt

.. warning::
   The ``--custom-instructions`` flag executes arbitrary Python code. Only load files from trusted sources.

**CPU State Dumps**

Capture CPU state to JSON files for debugging::

   dt31 run --dump error program.dt         # Dump state on error only
   dt31 run --dump success program.dt       # Dump state on successful completion
   dt31 run --dump all program.dt           # Dump state on both error and success
   dt31 run --dump none program.dt          # Never dump (default)

By default, dumps are saved with auto-generated timestamped filenames like ``program_crash_20251130_143022.json``
or ``program_final_20251130_143022.json``. Specify a custom filename::

   dt31 run --dump error --dump-file crash.json program.dt

Error dumps include the CPU state, error information, traceback, and the instruction that caused the error.
Success dumps include the final CPU state after execution completes.

Exit Codes
~~~~~~~~~~

The ``run`` command uses these exit codes:

+-------+------------------------------------------+
| Code  | Meaning                                  |
+=======+==========================================+
| 0     | Program executed successfully            |
+-------+------------------------------------------+
| 1     | Error (file not found, parse error, etc.)|
+-------+------------------------------------------+
| 130   | Execution interrupted (Ctrl+C)           |
+-------+------------------------------------------+

Examples
~~~~~~~~

::

   # Execute a program
   dt31 run countdown.dt

   # Run with debug output
   dt31 run --debug program.dt

   # Use custom memory size
   dt31 run --memory 1024 program.dt

   # Specify registers explicitly
   dt31 run --registers a,b,c,d,e program.dt

   # Load custom instructions
   dt31 run --custom-instructions my_instructions.py program.dt

   # Dump CPU state on error
   dt31 run --dump error --dump-file crash.json program.dt

Check Command
-------------

Validate the syntax of ``.dt`` assembly files without executing them.

Basic Usage
~~~~~~~~~~~

::

   dt31 check program.dt

This parses ``program.dt`` and reports any syntax errors. Parsing stops at the first error in each file.

Multiple Files
~~~~~~~~~~~~~~

Check multiple files at once::

   dt31 check program1.dt program2.dt program3.dt

Use glob patterns to check many files::

   dt31 check "*.dt"                 # Check all .dt files in current directory
   dt31 check "**/*.dt"              # Check all .dt files recursively

Options
~~~~~~~

**Custom Instructions**

Validate files that use custom instructions::

   dt31 check --custom-instructions my_instructions.py program.dt

Exit Codes
~~~~~~~~~~

+-------+---------------------------------------+
| Code  | Meaning                               |
+=======+=======================================+
| ``0`` | All files are valid                   |
+-------+---------------------------------------+
| ``1`` | Error (file not found, parse error)   |
+-------+---------------------------------------+

Examples
~~~~~~~~

::

   # Validate a single file
   dt31 check program.dt

   # Validate with custom instructions
   dt31 check --custom-instructions custom.py prog.dt

   # Validate multiple files
   dt31 check program1.dt program2.dt

   # Validate all .dt files
   dt31 check "*.dt"

   # Validate all .dt files recursively
   dt31 check "**/*.dt"

Format
------

Format ``.dt`` assembly files with consistent style. By default, formats files in-place.

Basic Usage
~~~~~~~~~~~

::

   dt31 format program.dt                    # Format in-place
   dt31 format --check program.dt            # Check if formatting needed (CI/pre-commit)
   dt31 format --diff program.dt             # Show diff without modifying
   dt31 format program1.dt program2.dt       # Format multiple files
   dt31 format "*.dt"                        # Format with glob patterns

Formatting Options
~~~~~~~~~~~~~~~~~~

All options have sensible defaults. Override them to customize the output style.

+----------------------------------+---------------------+--------------------------------------------+
| Option                           | Default             | Description                                |
+==================================+=====================+============================================+
| ``--indent-size N``              | 4                   | Spaces per indentation level               |
+----------------------------------+---------------------+--------------------------------------------+
| ``--label-inline``               | False               | Place labels on same line as instruction   |
+----------------------------------+---------------------+--------------------------------------------+
| ``--no-blank-line-before-label`` | False               | Don't add blank line before labels         |
+----------------------------------+---------------------+--------------------------------------------+
| ``--comment-margin N``           | 2                   | Spaces before inline comment semicolon     |
+----------------------------------+---------------------+--------------------------------------------+
| ``--align-comments``             | False               | Auto-align inline comments                 |
+----------------------------------+---------------------+--------------------------------------------+
| ``--comment-column N``           | Auto-calculated     | Column for aligned comments (if enabled)   |
+----------------------------------+---------------------+--------------------------------------------+
| ``--strip-comments``             | False               | Remove all comments                        |
+----------------------------------+---------------------+--------------------------------------------+
| ``--show-default-args``          | False               | Show args even when they match defaults    |
+----------------------------------+---------------------+--------------------------------------------+

Examples
~~~~~~~~

**Default formatting:**

.. code-block:: nasm

   ; Input
   CP 5,R.a
   loop:NOUT R.a,1
   SUB R.a,1

   ; Output (default settings)
       CP 5, R.a

   loop:
       NOUT R.a, 1
       SUB R.a, 1

**Custom style** (``--indent-size 2 --label-inline --no-blank-line-before-label``):

.. code-block:: nasm

     CP 5, R.a
   loop: NOUT R.a, 1
     SUB R.a, 1

**Comment alignment** (``--align-comments``):

.. code-block:: nasm

   ; Before
   CP 5, R.a ; Initialize
   ADD R.a, R.b, R.c ; Sum

   ; After
       CP 5, R.a          ; Initialize
       ADD R.a, R.b, R.c  ; Sum

Exit Codes
~~~~~~~~~~

- ``0``: Success (formatted or already formatted, or ``--check`` passed)
- ``1``: Error (file not found, parse error, or ``--check`` failed)

Register Auto-Detection
-----------------------

The CLI automatically detects which registers your program uses and creates a CPU with exactly
those registers. This means you don't need to manually specify registers in most cases.

For example, if your program uses ``R.a`` and ``R.b``, the CLI creates a CPU with registers
``a`` and ``b``.

If you explicitly provide ``--registers``, the CLI validates that all registers used in the
program are included in your list. If any are missing, it will report an error.

Error Handling
--------------

The CLI provides helpful error messages for common issues:

- **File not found**: Clear message indicating which file couldn't be found
- **Parse errors**: Line number and description of syntax errors
- **Runtime errors**: Exception message with optional CPU state (in debug mode)
- **Register errors**: List of missing registers when validation fails

Next Steps
----------

Now that you understand the CLI, you can explore:

- The complete :doc:`reference/instruction-set` for all available instructions
- The Python API documentation for programmatic usage
- Example programs in the `GitHub repository <https://github.com/daturkel/dt31/tree/main/examples>`_
