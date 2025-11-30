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
-----------

LT, GT, LE, GE, EQ, NE (comparison operators)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Compare two values and store the result (1 for true, 0 for false).

These instructions perform comparisons: less than, greater than, less than or equal to,
greater than or equal to, equal, and not equal. Like the arithmetic operators, they
support an optional third argument to specify where to store the result.

**Syntax:** ``INST ref, op``, ``INST op, op, ref`` for any of ``LT``, ``GT``, ``LE``, ``GE``, ``EQ``, and ``NE``

**Examples:**

.. code-block:: nasm

   LT 5, 10, R.a     ; R.a = 1 (5 < 10)
   GT R.a, R.b, R.c  ; R.c = 1 if R.a > R.b, else 0
   LE [0], 100       ; [0] = 1 if [0] <= 100, else 0
   GE R.a, 0         ; R.a = 1 if R.a >= 0, else 0
   EQ R.a, R.b       ; R.a = 1 if R.a == R.b, else 0
   NE 5, 5, R.x      ; R.x = 0 (5 == 5)

Boolean logic
-------------

AND, OR, XOR (logical operators)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Perform logical operations on two values, treating nonzero values as true.

These instructions implement boolean logic: ``AND`` returns 1 if both operands are nonzero,
``OR`` returns 1 if either operand is nonzero, and ``XOR`` returns 1 if exactly one operand
is nonzero. Like other binary operators, they support an optional third argument for output.

**Syntax:** ``INST ref, op``, ``INST op, op, ref`` for any of ``AND``, ``OR``, and ``XOR``

**Examples:**

.. code-block:: nasm

   AND R.a, R.b   ; R.a = 1 if both are truthy, else 0
   AND 0, 1, R.c  ; R.c = 0 (first is falsy)
   OR R.x, R.y    ; R.x = 1 if either is truthy, else 0
   OR 0, 5, R.d   ; R.d = 1 (second is truthy)
   XOR R.a, 1     ; R.a = 1 if exactly one is truthy, else 0
   XOR 1, 1, R.e  ; R.e = 0 (both are truthy)

NOT (logical negation)
~~~~~~~~~~~~~~~~~~~~~~

Negate a value, returning 1 if the value is zero (falsy), 0 otherwise.

This instruction implements logical NOT, treating zero as false and any nonzero value
as true. Like other unary operators, it supports an optional second argument for output.

**Syntax:** ``NOT ref``, ``NOT op, ref``

**Examples:**

.. code-block:: nasm

   NOT 0, R.a  ; R.a = 1 (0 is falsy)
   NOT 5, R.b  ; R.b = 0 (5 is truthy)
   NOT R.a     ; R.a = NOT R.a (negates in place)

Control flow
------------

JMP (unconditional jump)
~~~~~~~~~~~~~~~~~~~~~~~~

Jump unconditionally to a destination in the program.

This instruction sets the instruction pointer to the specified destination, which can be
a label, a literal instruction number, or a value stored in a register or memory.

**Syntax:** ``JMP dest``

**Examples:**

.. code-block:: nasm

   JMP start  ; Jump to the label 'start'
   JMP 10     ; Jump to instruction 10
   JMP R.a    ; Jump to the instruction number in R.a

JEQ, JNE, JGT, JGE (conditional jumps)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump to a destination if a comparison is true.

These instructions compare two values and jump if the condition is met:

- ``JEQ``: Jump if equal (a = b)
- ``JNE``: Jump if not equal (a ≠ b)
- ``JGT``: Jump if greater than (a > b)
- ``JGE``: Jump if greater than or equal to (a >= b)

**Syntax:** ``INST dest, op, op`` for any of ``JEQ``, ``JNE``, ``JGT``, and ``JGE``

**Examples:**

.. code-block:: nasm

   ; Count down from 5 to 1
   CP 5, R.a
   loop:
       NOUT R.a, 1
       SUB R.a, 1
       JGT loop, R.a, 0  ; Jump to loop if R.a > 0

   ; Jump if values are equal
   JEQ done, R.a, R.b    ; Jump to 'done' if R.a == R.b

   ; Jump if not equal
   JNE continue, R.x, 0  ; Jump to 'continue' if R.x != 0

JIF (conditional jump on truthy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump to a destination if a value is nonzero (truthy).

This instruction provides a simple way to jump based on a single condition, treating
any nonzero value as true.

**Syntax:** ``JIF dest, op``

**Examples:**

.. code-block:: nasm

   JIF continue, R.a  ; Jump to 'continue' if R.a is nonzero
   JIF loop, [0]      ; Jump to 'loop' if [0] is nonzero

Functions
---------

.. _call-call-function:

CALL (call function)
~~~~~~~~~~~~~~~~~~~~

Call a function by jumping to it and pushing the return address onto the stack.

This instruction saves the address of the next instruction on the stack, then jumps
to the specified destination. Use :ref:`RET <ret-return-from-function>` to return from the function.

**Syntax:** ``CALL dest``

**Examples:**

.. code-block:: nasm

   CALL greet         ; Call the function at label 'greet'
   CALL R.a           ; Call the function at the address in R.a

   ; Example function
   greet:
       COUT 'H', 0
       COUT 'i', 0
       COUT '!', 1
       RET

.. _ret-return-from-function:

RET (return from function)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Return from a function by popping the return address from the stack and jumping to it.

This instruction pops a value from the stack and sets the instruction pointer to it,
returning control to the instruction after the corresponding :ref:`CALL <call-call-function>`.

**Syntax:** ``RET``

**Examples:**

.. code-block:: nasm

   ; Simple function that prints "OK"
   print_ok:
       COUT 'O', 0
       COUT 'K', 1
       RET            ; Return to caller

Stack operations
----------------

PUSH (push to stack)
~~~~~~~~~~~~~~~~~~~~

Push a value onto the stack.

This instruction takes a value and pushes it onto the top of the stack. The stack
can be used for temporary storage or to pass values between functions.

**Syntax:** ``PUSH op``

**Examples:**

.. code-block:: nasm

   PUSH 42            ; Push literal 42 onto stack
   PUSH R.a           ; Push value of R.a onto stack
   PUSH [0]           ; Push value at [0] onto stack

POP (pop from stack)
~~~~~~~~~~~~~~~~~~~~

Pop a value from the stack, optionally storing it.

This instruction removes the top value from the stack. If an argument is provided,
the popped value is stored there; otherwise it's discarded.

**Syntax:** ``POP``, ``POP ref``

**Examples:**

.. code-block:: nasm

   POP R.a            ; Pop top value into R.a
   POP [0]            ; Pop top value into [0]
   POP                ; Pop and discard top value

SEMP (stack empty check)
~~~~~~~~~~~~~~~~~~~~~~~~~

Check if the stack is empty and store the result (1 if empty, 0 if not).

This instruction is useful for implementing stack-based algorithms where you need
to know if there are values remaining on the stack.

**Syntax:** ``SEMP ref``

**Examples:**

.. code-block:: nasm

   SEMP R.a           ; R.a = 1 if stack is empty, 0 otherwise
   JIF done, R.a      ; Jump to 'done' if stack is empty
