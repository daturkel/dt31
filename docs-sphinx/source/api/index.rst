API Reference
=============

Complete API documentation for all dt31 modules.

.. contents:: Modules
   :local:
   :depth: 1

CPU Module
----------

The core CPU class that manages registers, memory, stack, and program execution.

.. automodule:: dt31.cpu
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Instructions Module
-------------------

All instruction definitions including arithmetic, logic, control flow, I/O, and more.

.. automodule:: dt31.instructions
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Operands Module
---------------

Operand types for referencing values: literals, registers, memory, and labels.

.. automodule:: dt31.operands
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Parser Module
-------------

Text-based assembly parser for reading `.dt` files.

.. automodule:: dt31.parser
   :members:
   :undoc-members:
   :show-inheritance:

Assembler Module
----------------

Two-pass assembler for label resolution.

.. automodule:: dt31.assembler
   :members:
   :undoc-members:
   :show-inheritance:

CLI Module
----------

Command-line interface for executing assembly files.

.. automodule:: dt31.cli
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions Module
-----------------

Exception classes used throughout dt31.

.. automodule:: dt31.exceptions
   :members:
   :undoc-members:
   :show-inheritance:
