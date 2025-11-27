dt31 Documentation
==================

dt31 is a toy computer emulator in Python with a simple instruction set and virtual machine.

Highlights
--------

- **Simple CPU Architecture**: Configurable registers, memory, and stack.
- **Rich Instruction Set**: Dozens of instructions for arithmetic, logic, etc.
- **Native and Python Syntax**: Write directly with an assembly-like syntax or directly in Python.
- **Two-Pass Assembler**: Automatic resolution of labels for jumps and function calls.
- **Debug Mode**: Step-by-step execution with state inspection.
- **Command-line tools**: Run, syntax-check, or format code from the command line.
- **Pure Python Implementation**: Zero dependencies.

.. toctree::
   :maxdepth: 1
   :caption: Guides
   :hidden:
   :glob:

   getting-started
   *

.. toctree::
   :maxdepth: 2
   :caption: Reference and API
   :hidden:

   reference/index
   api/index

Quick Example
-------------

Below you can see a simple program which writes constants to the ``a`` and ``b`` registers, adds them up, and prints the output.
The program can be written equivalently in both the assembly-style syntax or with the :doc:`Python API </api/index>`.
Click on the tabs to toggle between the two syntaxes.

.. tab:: dt31

   .. code-block:: nasm

      ; Write to two registers, add them, then print the sum

      CP 10, R.a    ; a = 10
      CP 5, R.b     ; b = 5
      ADD R.a, R.b  ; a = a + b
      NOUT R.a, 1   ; print a with a newline

      ; prints 15

.. tab:: python

   .. code-block:: python

      from dt31 import DT31, I, R, L

      # Create a CPU with default settings
      cpu = DT31()

      # Write to two registers, add them, then print the sum
      program = [
         I.CP(10, R.a),      # a = 10
         I.CP(5, R.b),       # b = 5
         I.ADD(R.a, R.b),    # a = a + b
         I.NOUT(R.a, L[1]),  # Print a with newline
      ]

      # prints 15
      cpu.run(program)

About These Docs
----------------

Navigate these docs using the left sidebar. There are tutorials to take you on a tour of dt31's features as well as
exhaustive assembly and API reference pages. A great place to get started is :doc:`getting-started`.

Project Links
-------------

- `GitHub Repository <https://github.com/daturkel/dt31>`_
- `PyPI Package <https://pypi.org/project/dt31/>`_
