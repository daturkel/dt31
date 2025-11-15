Assembly Syntax Reference
=========================

Formal specification of the dt31 assembly language syntax.

Grammar Overview
----------------

Assembly programs consist of lines containing:

- Instructions with operands
- Label definitions
- Comments
- Blank lines (ignored)

Basic Structure
---------------

.. code-block:: text

   [label:] [INSTRUCTION [operand [, operand ...]]] [; comment]

**Rules:**

- Square brackets indicate optional elements
- Whitespace (spaces/tabs) is flexible
- Newlines separate statements

Instructions
------------

Format
~~~~~~

.. code-block:: text

   INSTRUCTION operand1, operand2, operand3

**Rules:**

- Instruction names are **case-insensitive**
- Operands are separated by commas
- Spaces around commas are optional
- Number of operands depends on instruction

**Examples:**

.. code-block:: nasm

   CP 5, R.a
   ADD R.a, R.b
   JGT loop, R.a, 0

Case Insensitivity
~~~~~~~~~~~~~~~~~~

All of these are valid:

.. code-block:: nasm

   ADD R.a, 1
   add R.a, 1
   Add R.a, 1
   ADD R.a, 1

Labels
------

Definition
~~~~~~~~~~

Labels mark positions in code:

.. code-block:: text

   label_name:

**Rules:**

- Must start with a letter or underscore
- Can contain letters, numbers, underscores
- Are **case-sensitive**
- Must be unique within a program
- Colon (``:``) is required

**Valid labels:**

.. code-block:: nasm

   loop:
   my_function:
   _internal:
   label123:
   LOOP:            ; Different from 'loop' (case-sensitive)

**Invalid labels:**

.. code-block:: text

   123label:        ; Can't start with number
   my-label:        ; Hyphens not allowed
   loop loop:       ; Spaces not allowed

Label on Same Line
~~~~~~~~~~~~~~~~~~

Labels can appear on the same line as an instruction:

.. code-block:: nasm

   start: CP 0, R.a
   loop: ADD R.a, 1

This is equivalent to:

.. code-block:: nasm

   start:
   CP 0, R.a
   loop:
   ADD R.a, 1

Operands
--------

Numeric Literals
~~~~~~~~~~~~~~~~

Integer constants:

.. code-block:: text

   [+-]?[0-9]+

**Examples:**

.. code-block:: nasm

   CP 42, R.a       ; Positive
   CP -5, R.b       ; Negative
   CP 0, R.c        ; Zero

Character Literals
~~~~~~~~~~~~~~~~~~

Single characters in single quotes:

.. code-block:: text

   '[character]'

**Examples:**

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

Registers
~~~~~~~~~

Register references:

.. code-block:: text

   R.name

**Rules:**

- ``R.`` prefix is **required**
- Name must start with letter or underscore
- Can contain letters, numbers, underscores
- Names are **case-sensitive**

**Examples:**

.. code-block:: nasm

   CP 5, R.a
   ADD R.counter, 1
   MUL R._temp, R.value

**Case sensitivity:**

.. code-block:: nasm

   R.a              ; Different from R.A
   R.counter        ; Different from R.Counter

Memory References
~~~~~~~~~~~~~~~~~

Direct memory access:

.. code-block:: text

   [address]
   M[address]

Both forms are equivalent. Address can be a literal or register.

**Examples:**

.. code-block:: nasm

   ; Direct with literal
   CP 42, [100]
   CP 42, M[100]    ; Same as above

   ; Indirect with register
   CP 100, R.a
   CP 42, [R.a]     ; Store at memory[100]
   CP 42, M[R.a]    ; Same as above

Label References
~~~~~~~~~~~~~~~~

Reference to a label (for jumps/calls):

.. code-block:: text

   label_name

**Examples:**

.. code-block:: nasm

   JMP end
   CALL my_function
   JGT loop, R.a, 0

Comments
--------

Single-line comments start with ``;`` and continue to end of line:

.. code-block:: nasm

   ; Full-line comment
   CP 5, R.a        ; Inline comment
   ADD R.a, 1       ; a += 1

Whitespace
----------

Flexible Spacing
~~~~~~~~~~~~~~~~

These are all valid:

.. code-block:: nasm

   CP 5, R.a
   CP    5,    R.a
   CP 5,R.a
   CP 5 , R.a

Indentation
~~~~~~~~~~~

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

Blank Lines
~~~~~~~~~~~

Blank lines are ignored:

.. code-block:: nasm

   CP 5, R.a

   ADD R.a, 1


   NOUT R.a, 1

Complete Grammar
----------------

In EBNF-like notation:

.. code-block:: text

   program        = line*
   line           = [label] [instruction] [comment] NEWLINE
   label          = IDENTIFIER ":"
   instruction    = INSTRUCTION [operand ("," operand)*]
   operand        = literal | register | memory | label_ref
   literal        = NUMBER | CHARACTER
   register       = "R." IDENTIFIER
   memory         = "[" (NUMBER | register) "]"
                  | "M[" (NUMBER | register) "]"
   label_ref      = IDENTIFIER
   comment        = ";" TEXT

   INSTRUCTION    = [A-Za-z]+          ; Case-insensitive
   IDENTIFIER     = [A-Za-z_][A-Za-z0-9_]*
   NUMBER         = [+-]?[0-9]+
   CHARACTER      = "'" . "'"

Operand Type Summary
--------------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Type
     - Syntax
     - Examples
   * - Numeric literal
     - ``NUMBER``
     - ``42``, ``-5``, ``0``
   * - Character literal
     - ``'CHAR'``
     - ``'A'``, ``'!'``, ``'\n'``
   * - Register
     - ``R.name``
     - ``R.a``, ``R.counter``, ``R._temp``
   * - Memory (direct)
     - ``[NUMBER]`` or ``M[NUMBER]``
     - ``[100]``, ``M[100]``
   * - Memory (indirect)
     - ``[R.name]`` or ``M[R.name]``
     - ``[R.a]``, ``M[R.idx]``
   * - Label
     - ``name``
     - ``loop``, ``my_function``

Case Sensitivity Summary
------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Element
     - Case Sensitive?
     - Example
   * - Instructions
     - No
     - ``ADD`` = ``add`` = ``Add``
   * - Registers
     - Yes
     - ``R.a`` ≠ ``R.A``
   * - Labels
     - Yes
     - ``loop`` ≠ ``Loop``
   * - Keywords (R, M)
     - No
     - ``R.a`` = ``r.a``, ``M[0]`` = ``m[0]``

Common Syntax Errors
--------------------

Missing Comma
~~~~~~~~~~~~~

.. code-block:: nasm

   ; Wrong
   ADD R.a R.b

   ; Correct
   ADD R.a, R.b

Missing R. Prefix
~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Wrong
   CP 5, a

   ; Correct
   CP 5, R.a

Missing Colon in Label
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Wrong
   loop
       ADD R.a, 1

   ; Correct
   loop:
       ADD R.a, 1

Invalid Label Name
~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ; Wrong (starts with number)
   1loop:

   ; Wrong (contains hyphen)
   my-loop:

   ; Correct
   loop1:
   my_loop:

Character Without Quotes
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Wrong
   OOUT H, 0

   ; Correct
   OOUT 'H', 0
   ; Or
   OOUT 72, 0       ; ASCII code

Example Programs
----------------

Hello World
~~~~~~~~~~~

.. code-block:: nasm

   ; Print "Hi!"
   OOUT 'H', 0
   OOUT 'i', 0
   OOUT '!', 1

Countdown Loop
~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Count from 5 to 1
   CP 5, R.a             ; Copy 5 into register a
   loop:
       NOUT R.a, 1       ; Output a with newline
       SUB R.a, 1        ; Decrement a
       JGT loop, R.a, 0  ; Jump if a > 0

Factorial Function
~~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Calculate factorial of 5
   CP 5, R.a
   CALL factorial
   NOUT R.a, 1
   JMP end

   factorial:
       ; Base case: n <= 1
       JGT recursive, R.a, 1
       CP 1, R.a
       RET

   recursive:
       ; Save n, call factorial(n-1)
       PUSH R.a
       SUB R.a, 1
       CALL factorial
       POP R.b
       MUL R.a, R.b
       RET

   end:

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

Next Steps
----------

- See :doc:`instruction-set` for all available instructions
- Learn :doc:`/tutorials/writing-programs` for practical usage
- Check :doc:`/how-to/parsing-assembly` for conversion between formats
- Try :doc:`/tutorials/cli-guide` for running assembly files
