dt31 Documentation
==================

A toy computer emulator in Python with a simple instruction set and virtual machine.

Features
--------

- **Simple CPU Architecture**: Configurable registers, fixed-size memory, and stack-based operations
- **Rich Instruction Set**: 60+ instructions including arithmetic, bitwise operations, logic, control flow, and I/O
- **Assembly Support**: Two-pass assembler with label resolution for jumps and function calls
- **Intuitive API**: Clean operand syntax (``R.a``, ``M[100]``, ``L[42]``, ``LC['A']``)
- **Debug Mode**: Step-by-step execution with state inspection
- **Pure Python**: Zero runtime dependencies

Documentation Contents
----------------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   getting-started

.. toctree::
   :maxdepth: 2
   :caption: Tutorials
   :glob:
   :hidden:

   tutorials/*

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   :hidden:

   api/index

Quick Example
-------------

.. code-block:: python

   from dt31 import DT31, I, R, L

   cpu = DT31()

   program = [
       I.CP(10, R.a),           # Copy 10 into register a
       I.CP(5, R.b),            # Copy 5 into register b
       I.ADD(R.a, R.b),         # a = a + b
       I.NOUT(R.a, L[1]),       # Output a with newline
   ]

   cpu.run(program)
   # 15

Project Links
-------------

- `GitHub Repository <https://github.com/daturkel/dt31>`_
- `PyPI Package <https://pypi.org/project/dt31/>`_
