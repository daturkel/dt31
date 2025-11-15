API Overview
============

The dt31 Python API is organized into several modules. This page provides a high-level overview with links to detailed API documentation.

Core Modules
------------

:doc:`api-cpu`
~~~~~~~~~~~~~~

The ``dt31.cpu`` module contains the ``DT31`` class, which represents the virtual CPU.

**Key class:**

- ``DT31`` - The main CPU class

**Common methods:**

- ``run(program, debug=False)`` - Execute a program
- ``step(debug=False)`` - Execute one instruction
- ``load(program)`` - Load a program without running
- ``get_register(name)`` - Read register value
- ``set_register(name, value)`` - Write register value
- ``get_memory(address)`` - Read memory value
- ``set_memory(address, value)`` - Write memory value

**Properties:**

- ``state`` - Complete CPU state snapshot
- ``halted`` - Whether execution has stopped
- ``ip`` - Current instruction pointer

:doc:`api-instructions`
~~~~~~~~~~~~~~~~~~~~~~~

The ``dt31.instructions`` module contains all instruction classes.

**Base classes:**

- ``Instruction`` - Base class for all instructions
- ``NullaryOperation`` - Base for instructions with no input operands
- ``UnaryOperation`` - Base for instructions with one input operand
- ``BinaryOperation`` - Base for instructions with two input operands

**Built-in instructions:**

- Arithmetic: ``ADD``, ``SUB``, ``MUL``, ``DIV``, ``MOD``
- Bitwise: ``BAND``, ``BOR``, ``BXOR``, ``BNOT``, ``BSL``, ``BSR``
- Comparison: ``LT``, ``GT``, ``LE``, ``GE``, ``EQ``, ``NE``
- Logic: ``AND``, ``OR``, ``XOR``, ``NOT``
- Control flow: ``JMP``, ``JEQ``, ``JNE``, ``JGT``, ``JLT``, ``JGE``, ``JLE``, ``JIF``, ``CALL``, ``RET``
- Stack: ``PUSH``, ``POP``, ``SEMP``
- I/O: ``NOUT``, ``OOUT``, ``NIN``, ``OIN``
- Data: ``CP``
- Special: ``NOOP``, ``BRK``, ``BRKD``, ``EXIT``
- Random: ``RND``, ``RINT``

:doc:`api-operands`
~~~~~~~~~~~~~~~~~~~

The ``dt31.operands`` module contains operand types.

**Operand types:**

- ``Literal`` - Constant numeric values
- ``CharLiteral`` - Character constants (``LC``)
- ``Register`` - CPU register references (``R``)
- ``Memory`` - Memory address references (``M``)
- ``Label`` - Jump/call targets

**Convenience objects:**

- ``L`` - Literal factory (e.g., ``L[42]``)
- ``LC`` - Character literal factory (e.g., ``LC["A"]``)
- ``R`` - Register accessor (e.g., ``R.a``)
- ``M`` - Memory accessor (e.g., ``M[100]``)

:doc:`api-parser`
~~~~~~~~~~~~~~~~~

The ``dt31.parser`` module converts assembly text to Python programs.

**Key function:**

- ``parse_program(text, custom_instructions=None)`` - Parse assembly text into instruction list

:doc:`api-assembler`
~~~~~~~~~~~~~~~~~~~~

The ``dt31.assembler`` module converts Python programs to assembly text.

**Key function:**

- ``program_to_text(program)`` - Convert instruction list to assembly text

:doc:`api-cli`
~~~~~~~~~~~~~~

The ``dt31.cli`` module provides the command-line interface.

**Key function:**

- ``main(argv=None)`` - Entry point for CLI

:doc:`api-exceptions`
~~~~~~~~~~~~~~~~~~~~~

The ``dt31.exceptions`` module defines custom exception types.

**Exception hierarchy:**

- ``DT31Error`` - Base exception
  - ``StackOverflowError``
  - ``StackUnderflowError``
  - ``MemoryAccessError``
  - ``RegisterNotFoundError``
  - ``InvalidJumpError``
  - ``ParseError``

Quick Start Examples
--------------------

Creating and Running Programs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[10], R.a),
       I.ADD(R.a, L[5]),
       I.NOUT(R.a, L[1]),
   ]
   cpu.run(program)

Parsing Assembly
~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   cpu = DT31()
   assembly = """
   CP 10, R.a
   ADD R.a, 5
   NOUT R.a, 1
   """
   program = parse_program(assembly)
   cpu.run(program)

Custom Instructions
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31, I, L, R
   from dt31.instructions import UnaryOperation
   from dt31.operands import Operand, Reference

   class DOUBLE(UnaryOperation):
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("DOUBLE", a, out)

       def _calc(self, cpu: DT31) -> int:
           return self.a.resolve(cpu) * 2

   cpu = DT31()
   program = [
       I.CP(L[5], R.a),
       DOUBLE(R.a),
       I.NOUT(R.a, L[1]),  # Output: 10
   ]
   cpu.run(program)

Full API Documentation
----------------------

For complete API documentation with all methods, parameters, and return types, see the auto-generated documentation:

- `pdoc-generated API docs <https://daturkel.github.io/dt31/dt31.html>`_

The pdoc documentation includes:

- Complete method signatures with type hints
- Detailed parameter descriptions
- Return type information
- Exception specifications
- Source code links
- Inheritance hierarchies

Module Index
------------

.. toctree::
   :maxdepth: 1

   api-cpu
   api-instructions
   api-operands
   api-parser
   api-assembler
   api-cli
   api-exceptions

Design Principles
-----------------

The dt31 API follows these principles:

**Intuitive Syntax**

- Clean operand notation: ``R.a``, ``M[100]``, ``L[42]``
- Natural instruction usage: ``I.ADD(R.a, R.b)``
- Python walrus operator support for labels

**Type Safety**

- Comprehensive type hints throughout
- Strict operand type checking
- IDE autocomplete support

**Flexibility**

- Both assembly text and Python API
- Configurable CPU (registers, memory, stack)
- Extensible instruction set

**Zero Dependencies**

- Pure Python implementation
- No runtime dependencies
- Easy to install and distribute

Next Steps
----------

- Browse :doc:`api-cpu` for CPU methods
- See :doc:`api-instructions` for instruction reference
- Check :doc:`/tutorials/writing-programs` for usage examples
- Learn :doc:`/tutorials/custom-instructions` to extend dt31
