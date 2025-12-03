Assembly Syntax Reference
=========================

Formal specification of the dt31 assembly language syntax.

.. NOTE::
   While the :doc:`parser </api/api-parser>` may be more lenient than the grammar proscribes,
   users should stick to the grammar specification in order to ensure forwards-compatibility.

Grammar Overview
----------------

A line of dt31 assembly source code matches the following syntax:

.. code-block:: text

   [label:] [INSTRUCTION [operand [, operand ...]]] [; comment]

Statements must be separated by at least one newline and whitespace is not significant.

Instructions
------------

Instruction names are case-insensitive and are automatically converted to all-caps during parsing
before being looked up.

The instruction must be separated by the first operand by whitespace while operands are separated
from each other by commas. Any additional whitespace is ignored.

The number of operands is instruction-dependent. Some operands support an optional last operand which,
if omitted, will take on a default value.

.. code-block:: nasm

   CP 5, R.a
   ADD R.a, R.b
   JGT loop, R.a, 0

Operands
--------

Literals
~~~~~~~~

Integer literals are written without any special syntax. They may not contain preceding zeros or commas.

.. code-block:: nasm

   CP 42, R.a       ; Positive
   CP -5, R.b       ; Negative
   CP 0, R.c        ; Zero

Character literals are surrounded by single quotes. They are stored as `ordinal values <https://docs.python.org/3/library/functions.html#ord>`_
under the hood, but metadata is stored such that the :doc:`debugger </debugging-programs>` will display them as characters.

.. code-block:: nasm

   OOUT 'H', 0      ; Letter
   OOUT '!', 0      ; Symbol
   OOUT ' ', 0      ; Space
   OOUT '\n', 0     ; Escape sequence (newline)

**Supported escape sequences:**

- ``\n`` - Newline (ASCII 10)
- ``\t`` - Tab (ASCII 9)
- ``\'`` - Single quote
- ``\\`` - Backslash

Register References
~~~~~~~~~~~~~~~~~~~

Registers are written with a ``R.`` preceding the **case-sensitive** register name.
Register names must be valid `Python identifier <https://docs.python.org/3/reference/lexical_analysis.html#identifiers>`_
but must not begin with two underscores ``__``.

.. code-block:: text

   OOUT R.name
   ADD R.case_SENSITIVE, R.b_1

Memory References
~~~~~~~~~~~~~~~~~

Memory is written using square brackets ``[]`` surrounding any other valid operand which will be interpreted as the memory address.
Optionally, the square brackets can be preceded by an ``M`` to match the :class:`dt31.operands.M` shorthand.

.. code-block:: nasm

   ; Direct with literal
   CP 42, [100]
   CP 42, M[100]    ; Same as above

   ; Indirect with register
   CP 100, R.a
   CP 42, [R.a]     ; Store at memory[100]
   CP 42, M[R.a]    ; Same as above

   ; Arbitrary levels of indirection
   CP 100, [0]
   CP 20, [[0]]     ; Store at memory[100]
   CP 50, [[[R.a]]] ; Store at memory[memory[memory[R.a]]]

Labels
~~~~~~

Labels are referred to by their names with no special syntax.

.. code-block:: nasm

   JMP end
   CALL my_function
   JGT loop, R.a, 0

Label Definitions
-----------------

Labels mark positions in code and are demarcated by the label name followed by a colon:

.. code-block:: text

   label_name:

**Rules:**

- Labels can contain letters, numbers, underscores
- Labels are **case-sensitive**
- Labels must be unique within a program

Labels can appear on the same line as an instruction or before them:

.. code-block:: nasm

   start: CP 0, R.a
   loop: ADD R.a, 1

This is equivalent to:

.. code-block:: nasm

   start:
   CP 0, R.a
   loop:
   ADD R.a, 1

...which is equivalent to:

.. code-block:: nasm

   start: CP 0, R.a

   loop:

   ADD R.a, 1

Comments
--------

Single-line comments start with ``;`` and continue to end of line:

.. code-block:: nasm

   ; Full-line comment
   CP 5, R.a        ; Inline comment
   ADD R.a, 1       ; a += 1

Whitespace
----------

These are all valid:

.. code-block:: nasm

   CP 5, R.a
   CP    5,    R.a
   CP 5,R.a
   CP 5 , R.a

Indentation is cosmetic (ignored by parser):

.. code-block:: nasm

   ; Not indented
   CP 5, R.a
   loop:
   SUB R.a, 1

   ; Indented (more readable)
   CP 5, R.a
   loop:
       SUB R.a, 1

Blank lines are ignored:

.. code-block:: nasm

   CP 5, R.a

   ADD R.a, 1


   NOUT R.a, 1

Differences from Python API
----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Element
     - Assembly
     - Python
   * - Literals
     - ``42``, ``-5``
     - ``L[42]``, ``L[-5]``
   * - Characters
     - ``'A'``
     - ``LC["A"]``
   * - Memory
     - ``[100]`` or ``M[100]``
     - ``M[100]``
   * - Labels
     - ``loop``
     - ``Label("loop")``
   * - Instructions
     - ``ADD R.a, 1``
     - ``I.ADD(R.a, L[1])``
