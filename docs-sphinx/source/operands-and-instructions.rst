Operands and Instructions
=========================

dt31 programs are written as a series of **instructions**, where each instruction takes zero
or more **operands** as its arguments. This guide will take you through the different operand
types as well as some common instructions you'll use. See the :doc:`reference/instruction-set`
for a comprehensive instruction listing.

Operands (and labels)
---------------------

Operands are what are passed to dt31 instructions. We'll define the three operand types, plus labels, as well as some
operand groups which serve as helpful shorthand.

The three operand types
~~~~~~~~~~~~~~~~~~~~~~~

The core operand types are literals, register references, memory refrences, and labels. Let's
take a look at each.

**Literals** are bare integers or characters, e.g. ``20``, ``-5``, ``'!'``. We typically use them
because we want to store their value some where, or occasionally to toggle the behavior of an instruction.

**Register references** are values stored in predefined locations called registers, e.g. ``R.a``, ``R.start``.
A dt31 CPU is defined with a fixed set of registers and only known registers can be referenced. However,
the user can choose what registers they want to make available when initializing the CPU.

**Memory references** are values stored in indexed memory, e.g. ``[5]``, ``[R.a]``, ``[[2]]``. A dt31 CPU
has a fixed number of slots in memory, where each slot can store one integer or one character.

The syntax for memory references is very flexible: ``[5]`` points to the value at index 5; if ``R.a = 3``, then ``[R.a]``
points to the value at index 3; memory references can even be recursive, so if ``[2] = 9``, then ``[[2]]``
points to the value at index 9.

Labels
~~~~~~

**Labels** are named references to user-defined points in the program, e.g. ``start``, ``inner_loop``, ``end``.
As an illustrative example, consider the following program:

.. code-block:: nasm

   ; output "abcdef\n"

   ; initialize [0] = a
      CP 'a', [0]

   ; output [0], then increment it
   ; if letter is "less than" 'f', return to loop_start
   loop_start:
      COUT [0]
      ADD [0], 1
      JGE loop_start, 'f', [0]
   ; print newline
      COUT '\n'

The line ``loop_start:`` defines a label right before the ``COUT [0]`` instruction. When we reach the ``JGE loop_start, 'f', [0]``
instruction, it checks to see if 'f' (Unicode codepoint 102) is greater than or equal to the character at ``[0]``; if it is, we
repeat the loop by jumping back to ``loop_start``, otherwise we just continue to the next instruction.

Labels get resolved during assembly to their corresponding `instruction pointer <https://en.wikipedia.org/wiki/Program_counter>`__,
and they behave correctly with both instructions expecting an absolute instruction pointer or a relative offset.

Operand groups
~~~~~~~~~~~~~~

It's useful to define a few **operand groups** so that we can easily describe what operands are valid arguments for different instructions.

**Operand** refers to literals, register references, and memory references, but **not** labels.

.. note::
   Labels are not considered a *true* operand type in dt31 because they are resolved to literals during assembly and have semantics
   that make them appropriate only in certain circumstances. Technically you may be able to use labels anywhere a literal is expected
   in dt31 but this should be considered undefined behavior and is not officially supported at this time.

**Reference** refers to just register references and memory references.

**Destination** refers to literals, register references, memory references, *and* labels.

You will see these names used below (in shorthand as ``op``, ``ref``, and ``dest``) to indicate the types of operands an instruction supports.
A handfull of arguments must be a memory reference, which will is denoted as ``mem``.

+---------------+---------+-----------+-------------+
|               | Operand | Reference | Destination |
+===============+=========+===========+=============+
| Literal       | ✓       |           | ✓           |
+---------------+---------+-----------+-------------+
| Register Ref. | ✓       | ✓         | ✓           |
+---------------+---------+-----------+-------------+
| Memory Ref.   | ✓       | ✓         | ✓           |
+---------------+---------+-----------+-------------+
| Label         |         |           | ✓           |
+---------------+---------+-----------+-------------+

Basics and I/O
--------------

CP (copy)
~~~~~~~~~

Copy a value from source to destination.

**Syntax:** ``CP op, ref``

**Examples:**

.. code-block:: nasm

   CP 42, R.a     ; a = 42
   CP R.a, R.b    ; b = a
   CP [100], R.c  ; c = [100]

NIN / CIN (number / character input)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Prompt the user for input. ``NIN`` accepts numeric input while ``CIN``
accepts a single character (including escape sequences like ``\n``) which is stored as its Unicode codepoint.

Problematic inputs will result in a runtime error crashing the program.

**Syntax:** ``OIN ref``, ``CIN ref``

**Examples:**

.. code-block:: nasm

   NIN R.a  ; write numeric input to register a
   CIN [5]  ; write character input to [5]

NOUT / COUT (number / character output)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Print a value to the terminal. ``NOUT`` prints a number while ``COUT``
prints a character. If the second argument is provided and is nonzero, a newline will
be printed as well.

Stored data is agnostic to whether it represents a character or a number, so
data entered as a number can be printed as a character and vice-versa, see below.

**Syntax:** ``NOUT op[, op=0]``, ``COUT op[, op=0]``

.. code-block:: nasm

   NOUT 15      ; print 15
   NOUT [0], 1  ; print the data at [0] with a newline
   NOUT 'a'     ; print 97
   COUT 'a', 1  ; print 'a\n'
   COUT R.a     ; print the data at R.a as a character

STRIN
~~~~~

Prompt the user for string input which will be stored in contiguous slots
of memory, followed by a ``0``.

**Syntax:** ``STRIN mem``

**Examples:**

.. code-block:: nasm

   STRIN [0]    ; write string input to memory, starting at [0]
   STRIN [R.a]  ; write string input to memory, starting at [R.a]

STROUT
~~~~~~

Print a string value to the terminal. The string value starts at the provided
memory address and continues until a ``0`` is encountered. If the second argument is provided
and is nonzero, a newline will be printed as well.

**Syntax:** ``STROUT mem[, op=0]``

**Examples:**

.. code-block:: nasm

   STROUT [0], 1    ; print the string starting at [0] with a newline
   STROUT [R.a], 1  ; print the string starting at [R.a]

Math
----

ADD, SUB, MUL, DIV (arithmetic)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Perform arithmetic between two arguments, overwriting the first argument or optionally writing
to a third argument.

These instructions allow you to add, subtract, multiply, or divide. Division rounds
down, so ``DIV 5, 2, R.a`` would set ``R.a`` to 2.

Common binary operators all share the same behavior over their arguments: the first
two arguments are the operands while a third optional argument (which must be a reference)
can be used to specify output. If the third argument is not provided, the output defaults
to the first argument, and if the first argument is not a reference, the operation will fail.

**Syntax:** ``INST ref, op``, ``INST op, op, ref`` for any of ``ADD``, ``SUB``, ``MUL``, and ``DIV``

**Examples:**

.. code-block:: nasm

   ADD 5, 2, R.a      ; R.a = 5 + 2
   ADD [0], 1         ; [0] = [0] + 1
   ADD 1, 2           ; ERROR, can't write output to first argument (literal 1)
   SUB R.a, R.b, R.c  ; R.c = R.a - R.b
   MUL [0], [0]       ; [0] = [0] * [0]
   DIV [5], 2         ; [5] = [5] / 2 (rounded down)

MOD (modulo)
~~~~~~~~~~~~

Calculate the the remainder after division (aka the modulus).

This operation shares the binary operator behavior with the arithmetic operators: the
optional third argument can be used to specify an output destination.

**Syntax:** ``MOD op, op, ref``, ``MOD ref, op``

**Examples:**

.. code-block:: nasm

   MOD 5, 2, R.a  ; R[a] = 5 % 2 = 1
   MOD [0], 3     ; [0] = [0] % 3
   MOD 1, 2       ; ERROR, can't write output to first argument (literal 1)

Comparisons

Boolean logic

Jumps

Call, ret

Push, pop, semp
