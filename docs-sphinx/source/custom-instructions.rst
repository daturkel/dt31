Custom Instructions
===================

dt31's instruction set can be extended with custom instructions. This allows you to add domain-specific operations while maintaining the same clean syntax as built-in instructions.

Why Custom Instructions?
-------------------------

Custom instructions are useful for:

- Adding domain-specific operations (e.g., graphics, physics, crypto)
- Simplifying common patterns into single instructions
- Educational purposes (teaching instruction set design)
- Experimenting with new CPU features

Basic Example
-------------

Here's a simple custom instruction that squares a number:

.. code-block:: python

   from dt31 import DT31
   from dt31.instructions import UnaryOperation
   from dt31.operands import Operand, Reference

   class SQUARE(UnaryOperation):
       """Square a value."""

       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("SQUARE", a, out)

       def _calc(self, cpu: DT31) -> int:
           value = self.a.resolve(cpu)
           return value * value

   # Use it programmatically
   from dt31 import I, L, R

   cpu = DT31()
   program = [
       I.CP(L[5], R.a),
       SQUARE(R.a),          # a = 25
       I.NOUT(R.a, L[1]),
   ]

   cpu.run(program)  # Output: 25

Instruction Base Classes
-------------------------

dt31 provides helper classes for common instruction patterns:

UnaryOperation
~~~~~~~~~~~~~~

For instructions with one input operand:

.. code-block:: python

   from dt31.instructions import UnaryOperation
   from dt31.operands import Operand, Reference

   class TRIPLE(UnaryOperation):
       """Multiply a value by 3."""

       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("TRIPLE", a, out)

       def _calc(self, cpu: DT31) -> int:
           return self.a.resolve(cpu) * 3

**Pattern:**
- Inherit from ``UnaryOperation``
- Implement ``_calc(self, cpu)`` to compute the result
- The result is automatically stored in ``out`` (defaults to first operand)

BinaryOperation
~~~~~~~~~~~~~~~

For instructions with two input operands:

.. code-block:: python

   from dt31.instructions import BinaryOperation
   from dt31.operands import Operand, Reference

   class CLAMP(BinaryOperation):
       """Clamp a value between 0 and maximum."""

       def __init__(self, value: Operand, maximum: Operand, out: Reference | None = None):
           super().__init__("CLAMP", value, maximum, out)

       def _calc(self, cpu: DT31) -> int:
           val = self.a.resolve(cpu)
           max_val = self.b.resolve(cpu)
           return max(0, min(val, max_val))

**Pattern:**
- Inherit from ``BinaryOperation``
- Implement ``_calc(self, cpu)`` using ``self.a`` and ``self.b``
- Result stored in ``out`` (defaults to first operand)

NullaryOperation
~~~~~~~~~~~~~~~~

For instructions with no input operands (only output):

.. code-block:: python

   from dt31.instructions import NullaryOperation
   from dt31.operands import Reference

   class RND(NullaryOperation):
       """Generate a random bit (0 or 1)."""

       def __init__(self, out: Reference):
           super().__init__("RND", out)

       def _calc(self, cpu: DT31) -> int:
           import random
           return random.randint(0, 1)

**Pattern:**
- Inherit from ``NullaryOperation``
- No input operands, only an output destination
- Useful for generators (random, time, input)

Custom Instruction Base Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For full control, inherit from ``Instruction`` directly:

.. code-block:: python

   from dt31.instructions import Instruction

   class SWAP(Instruction):
       """Swap two register values."""

       def __init__(self, a: Reference, b: Reference):
           super().__init__("SWAP")
           self.a = a
           self.b = b

       def execute(self, cpu: DT31) -> None:
           val_a = self.a.resolve(cpu)
           val_b = self.b.resolve(cpu)
           self.a.store(cpu, val_b)
           self.b.store(cpu, val_a)

       def __repr__(self) -> str:
           return f"SWAP({self.a!r}, {self.b!r})"

       def assembly_text(self) -> str:
           return f"SWAP {self.a}, {self.b}"

**Requirements when inheriting from Instruction:**
- Implement ``execute(self, cpu)`` to perform the operation
- Implement ``__repr__()`` for Python representation
- Implement ``assembly_text()`` for assembly representation

Using Custom Instructions
--------------------------

In Python Programs
~~~~~~~~~~~~~~~~~~

Simply use your custom instruction class in program lists:

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()

   program = [
       I.CP(L[5], R.a),
       SQUARE(R.a),          # Custom instruction
       I.NOUT(R.a, L[1]),    # Built-in instruction
   ]

   cpu.run(program)

In Assembly Text
~~~~~~~~~~~~~~~~

To use custom instructions in assembly, pass them to ``parse_program()``:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   cpu = DT31()

   custom_instructions = {
       "SQUARE": SQUARE,
       "TRIPLE": TRIPLE,
       "CLAMP": CLAMP,
   }

   assembly = """
   CP 5, R.a
   SQUARE R.a        ; a = 25
   TRIPLE R.a        ; a = 75
   NOUT R.a, 1
   """

   program = parse_program(assembly, custom_instructions=custom_instructions)
   cpu.run(program)

With the CLI
~~~~~~~~~~~~

Create a Python file exporting an ``INSTRUCTIONS`` dict:

.. code-block:: python

   # my_instructions.py
   from dt31.instructions import UnaryOperation, BinaryOperation
   from dt31.operands import Operand, Reference

   class SQUARE(UnaryOperation):
       """Square a value."""
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("SQUARE", a, out)

       def _calc(self, cpu) -> int:
           return self.a.resolve(cpu) ** 2

   class TRIPLE(UnaryOperation):
       """Multiply by 3."""
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("TRIPLE", a, out)

       def _calc(self, cpu) -> int:
           return self.a.resolve(cpu) * 3

   # Export instructions dict (required)
   INSTRUCTIONS = {
       "SQUARE": SQUARE,
       "TRIPLE": TRIPLE,
   }

Then use with ``--custom-instructions``:

.. code-block:: bash

   dt31 --custom-instructions my_instructions.py program.dt

**Security Warning:** Loading custom instruction files executes arbitrary Python code. Only load files from trusted sources.

Complete Example
----------------

Here's a complete example with multiple custom instructions:

.. code-block:: python

   """Custom math operations for dt31."""
   from dt31 import DT31
   from dt31.instructions import UnaryOperation, BinaryOperation
   from dt31.operands import Operand, Reference

   class ABS(UnaryOperation):
       """Absolute value."""
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("ABS", a, out)

       def _calc(self, cpu: DT31) -> int:
           return abs(self.a.resolve(cpu))

   class POW(BinaryOperation):
       """Raise to power: a^b."""
       def __init__(self, base: Operand, exp: Operand, out: Reference | None = None):
           super().__init__("POW", base, exp, out)

       def _calc(self, cpu: DT31) -> int:
           base = self.a.resolve(cpu)
           exp = self.b.resolve(cpu)
           return base ** exp

   class MIN(BinaryOperation):
       """Minimum of two values."""
       def __init__(self, a: Operand, b: Operand, out: Reference | None = None):
           super().__init__("MIN", a, b, out)

       def _calc(self, cpu: DT31) -> int:
           return min(self.a.resolve(cpu), self.b.resolve(cpu))

   # Export for CLI use
   INSTRUCTIONS = {
       "ABS": ABS,
       "POW": POW,
       "MIN": MIN,
   }

   if __name__ == "__main__":
       from dt31 import I, L, R
       from dt31.parser import parse_program

       cpu = DT31()

       assembly = """
       CP -5, R.a
       ABS R.a           ; a = 5
       NOUT R.a, 1

       CP 2, R.b
       CP 8, R.c
       POW R.b, R.c      ; b = 256
       NOUT R.b, 1

       CP 42, R.d
       MIN R.a, R.d, R.e ; e = min(5, 42) = 5
       NOUT R.e, 1
       """

       program = parse_program(assembly, custom_instructions=INSTRUCTIONS)
       cpu.run(program)
       # Output:
       # 5
       # 256
       # 5

Best Practices
--------------

Naming Conventions
~~~~~~~~~~~~~~~~~~

- Use UPPERCASE names for instruction classes
- Use descriptive abbreviations (``SQUARE`` not ``SQ``)
- Avoid conflicts with built-in instructions

Type Hints
~~~~~~~~~~

Always include type hints for better IDE support:

.. code-block:: python

   def __init__(self, a: Operand, out: Reference | None = None):
       super().__init__("MYOP", a, out)

   def _calc(self, cpu: DT31) -> int:
       return self.a.resolve(cpu)

Documentation
~~~~~~~~~~~~~

Add docstrings to explain what your instruction does:

.. code-block:: python

   class CLAMP(BinaryOperation):
       """Clamp value between 0 and maximum.

       Args:
           value: The value to clamp
           maximum: The maximum allowed value
           out: Where to store result (defaults to value)

       Returns:
           Value clamped to range [0, maximum]
       """

Error Handling
~~~~~~~~~~~~~~

Handle edge cases gracefully:

.. code-block:: python

   class SAFEDIV(BinaryOperation):
       """Division with zero check."""

       def _calc(self, cpu: DT31) -> int:
           a = self.a.resolve(cpu)
           b = self.b.resolve(cpu)
           if b == 0:
               return 0  # Or raise exception
           return a // b

Testing
~~~~~~~

Test your custom instructions thoroughly:

.. code-block:: python

   def test_square():
       from dt31 import DT31, I, L, R

       cpu = DT31()
       program = [
           I.CP(L[5], R.a),
           SQUARE(R.a),
       ]
       cpu.run(program)
       assert cpu.get_register('a') == 25

Advanced: Stateful Instructions
--------------------------------

Instructions can maintain state across executions:

.. code-block:: python

   from dt31.instructions import NullaryOperation
   from dt31.operands import Reference

   class COUNTER(NullaryOperation):
       """Incremental counter (starts at 0)."""

       _count = 0  # Class variable for state

       def __init__(self, out: Reference):
           super().__init__("COUNTER", out)

       def _calc(self, cpu: DT31) -> int:
           current = COUNTER._count
           COUNTER._count += 1
           return current

   # Usage:
   # COUNTER R.a  ; a = 0
   # COUNTER R.b  ; b = 1
   # COUNTER R.c  ; c = 2

**Note:** Stateful instructions can make programs harder to reason about. Use sparingly.
