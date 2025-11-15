Parsing and Converting Assembly
================================

This guide covers converting between assembly text and Python program objects.

Assembly to Python
------------------

Use ``parse_program()`` to convert assembly text to Python:

.. code-block:: python

   from dt31.parser import parse_program

   assembly = """
   CP 5, R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1
       JGT loop, R.a, 0
   """

   program = parse_program(assembly)
   # Returns list of Instruction objects

Now you can run it:

.. code-block:: python

   from dt31 import DT31

   cpu = DT31()
   cpu.run(program)

From Files
~~~~~~~~~~

Read assembly from ``.dt`` files:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   with open("program.dt") as f:
       assembly = f.read()

   program = parse_program(assembly)
   cpu = DT31()
   cpu.run(program)

With Custom Instructions
~~~~~~~~~~~~~~~~~~~~~~~~

Pass custom instructions to the parser:

.. code-block:: python

   from dt31.parser import parse_program
   from dt31.instructions import UnaryOperation
   from dt31.operands import Operand, Reference

   class TRIPLE(UnaryOperation):
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("TRIPLE", a, out)

       def _calc(self, cpu) -> int:
           return self.a.resolve(cpu) * 3

   custom_instructions = {"TRIPLE": TRIPLE}

   assembly = """
   CP 5, R.a
   TRIPLE R.a
   NOUT R.a, 1
   """

   program = parse_program(assembly, custom_instructions=custom_instructions)

Python to Assembly
------------------

Use ``program_to_text()`` to convert Python programs to assembly:

.. code-block:: python

   from dt31 import I, L, Label, R
   from dt31.assembler import program_to_text

   program = [
       I.CP(L[5], R.a),
       loop := Label("loop"),
       I.NOUT(R.a, L[1]),
       I.SUB(R.a, L[1]),
       I.JGT(loop, R.a, L[0]),
   ]

   text = program_to_text(program)
   print(text)

Output:

.. code-block:: nasm

       CP 5, R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1, R.a
       JGT loop, R.a, 0

Save to File
~~~~~~~~~~~~

.. code-block:: python

   from dt31 import I, L, Label, R
   from dt31.assembler import program_to_text

   program = [
       I.CP(L[10], R.a),
       I.ADD(R.a, L[5]),
       I.NOUT(R.a, L[1]),
   ]

   text = program_to_text(program)

   with open("generated.dt", "w") as f:
       f.write(text)

Round-Trip Conversion
---------------------

You can convert back and forth:

.. code-block:: python

   from dt31 import I, L, Label, R
   from dt31.parser import parse_program
   from dt31.assembler import program_to_text

   # Start with Python
   original = [
       I.CP(L[5], R.a),
       loop := Label("loop"),
       I.SUB(R.a, L[1]),
       I.JGT(loop, R.a, L[0]),
   ]

   # Convert to assembly
   assembly = program_to_text(original)
   print("Assembly:")
   print(assembly)

   # Parse back to Python
   parsed = parse_program(assembly)

   # Convert to assembly again
   assembly2 = program_to_text(parsed)
   print("\nRound-trip:")
   print(assembly2)

   # Should be identical
   assert assembly == assembly2

Parse Validation
----------------

Syntax Checking
~~~~~~~~~~~~~~~

Use ``parse_program()`` to validate syntax without running:

.. code-block:: python

   from dt31.parser import parse_program

   assembly = """
   CP 5, R.a
   INVALID_INSTRUCTION
   """

   try:
       program = parse_program(assembly)
       print("✓ Valid syntax")
   except Exception as e:
       print(f"✗ Parse error: {e}")

From CLI
~~~~~~~~

.. code-block:: bash

   dt31 --parse-only program.dt

This validates syntax and exits with:

- Code 0 if valid
- Code 1 if syntax errors

Handling Parse Errors
---------------------

Parse errors include line numbers:

.. code-block:: python

   from dt31.parser import parse_program

   assembly = """
   CP 5, R.a
   ADD R.a R.b    ; Missing comma
   NOUT R.a, 1
   """

   try:
       parse_program(assembly)
   except Exception as e:
       print(f"Error: {e}")
       # Error: Line 3: ...

Common parse errors:

- Missing commas between operands
- Invalid operand syntax
- Undefined instruction names
- Invalid label names

Parsing Details
---------------

Operand Syntax
~~~~~~~~~~~~~~

The parser recognizes these operand patterns:

.. code-block:: text

   ; Literals
   42              ; Integer
   -5              ; Negative integer
   'A'             ; Character literal

   ; Registers
   R.a             ; Register (R. prefix required)
   R.counter       ; Multi-character register name

   ; Memory
   [100]           ; Direct memory access
   M[100]          ; Alternative syntax
   [R.a]           ; Indirect memory access
   M[R.a]          ; Alternative syntax

   ; Labels
   loop            ; Label reference
   my_label        ; Multi-word labels with underscores

Whitespace and Comments
~~~~~~~~~~~~~~~~~~~~~~~

The parser ignores:

- Leading and trailing whitespace
- Blank lines
- Comments (anything after ``;``)
- Extra spaces around commas

These are all equivalent:

.. code-block:: nasm

   CP 5, R.a

   CP    5,    R.a

   CP 5,R.a

   CP 5, R.a    ; comment

Label Resolution
~~~~~~~~~~~~~~~~

Labels are resolved in a two-pass process:

1. **First pass:** Collect label positions
2. **Second pass:** Replace label references with instruction indices

.. code-block:: python

   from dt31.parser import parse_program

   assembly = """
   JMP end        ; Forward reference
   NOUT R.a, 1
   end:
   """

   # Parser resolves 'end' to instruction index 2
   program = parse_program(assembly)

Case Sensitivity
~~~~~~~~~~~~~~~~

- **Instructions:** Case-insensitive (``ADD``, ``add``, ``Add`` all work)
- **Registers:** Case-sensitive (``R.a`` ≠ ``R.A``)
- **Labels:** Case-sensitive (``loop`` ≠ ``Loop``)

.. code-block:: nasm

   ; Valid: different cases for instruction
   ADD R.a, 1
   add R.a, 1
   Add R.a, 1

   ; Invalid: wrong register case
   CP 5, R.A      ; If register is 'a' not 'A'

Auto-Detecting Registers
~~~~~~~~~~~~~~~~~~~~~~~~~

The parser can infer register names:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   assembly = """
   CP 5, R.counter
   ADD R.counter, R.step
   """

   program = parse_program(assembly)

   # Create CPU with auto-detected registers
   cpu = DT31(registers=["counter", "step"])
   cpu.run(program)

Or let the CLI auto-detect:

.. code-block:: bash

   dt31 program.dt  # Registers auto-detected

Programmatic Assembly Generation
---------------------------------

Generate assembly programmatically:

.. code-block:: python

   from dt31.assembler import program_to_text
   from dt31 import I, L, R

   def generate_multiplication_table(n):
       """Generate assembly for N times table."""
       program = [
           I.CP(L[1], R.i),  # i = 1
       ]

       # Add loop
       loop = Label("loop")
       program.extend([
           loop,
           I.CP(R.i, R.result),
           I.MUL(R.result, L[n]),
           I.NOUT(R.result, L[1]),
           I.ADD(R.i, L[1]),
           I.JLE(loop, R.i, L[10]),
       ])

       return program_to_text(program)

   # Generate 7 times table
   assembly = generate_multiplication_table(7)
   print(assembly)

Use Cases
---------

Code Generation
~~~~~~~~~~~~~~~

Generate dt31 programs from templates:

.. code-block:: python

   from dt31.assembler import program_to_text
   from dt31 import I, L, Label, R

   def generate_sum(numbers):
       """Generate program to sum a list of numbers."""
       program = [I.CP(L[0], R.sum)]

       for num in numbers:
           program.append(I.ADD(R.sum, L[num]))

       program.append(I.NOUT(R.sum, L[1]))

       return program_to_text(program)

   assembly = generate_sum([10, 20, 30, 40])
   print(assembly)

Testing
~~~~~~~

Use parsing in unit tests:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   def test_countdown():
       assembly = """
       CP 3, R.a
       loop:
           SUB R.a, 1
           JGT loop, R.a, 0
       """

       cpu = DT31()
       program = parse_program(assembly)
       cpu.run(program)

       assert cpu.get_register('a') == 0

Documentation
~~~~~~~~~~~~~

Include executable examples in docs:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   def run_example(assembly):
       """Run an assembly example and return output."""
       cpu = DT31()
       program = parse_program(assembly)

       output = []
       # Capture output...
       cpu.run(program)

       return output

Format Conversion
~~~~~~~~~~~~~~~~~

Convert between formats for different tools:

.. code-block:: python

   from dt31.parser import parse_program
   from dt31.assembler import program_to_text

   # Read assembly
   with open("program.dt") as f:
       assembly = f.read()

   # Parse and normalize
   program = parse_program(assembly)

   # Write normalized version
   normalized = program_to_text(program)
   with open("program_normalized.dt", "w") as f:
       f.write(normalized)

Limitations
-----------

Comments Not Preserved
~~~~~~~~~~~~~~~~~~~~~~

Comments are stripped during parsing:

.. code-block:: python

   from dt31.parser import parse_program
   from dt31.assembler import program_to_text

   assembly = """
   ; Important comment
   CP 5, R.a  ; This too
   """

   program = parse_program(assembly)
   text = program_to_text(program)
   # Comments are gone

**Workaround:** Keep original ``.dt`` files for documentation.

Formatting Not Preserved
~~~~~~~~~~~~~~~~~~~~~~~~~

Indentation and spacing are normalized:

.. code-block:: python

   # Input:
   #   CP    5,  R.a
   #     ADD R.a,1

   # Output:
   #   CP 5, R.a
   #   ADD R.a, 1
