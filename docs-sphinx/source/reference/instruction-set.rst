Instruction Set Reference
=========================

Complete reference of all built-in dt31 instructions, organized by category.

Notation
--------

- ``<operand>`` - Any operand (literal, register, memory, label)
- ``<value>`` - Numeric operand (literal, register, memory)
- ``<ref>`` - Reference operand (register or memory)
- ``<label>`` - Label operand
- ``[optional]`` - Optional parameter

Most arithmetic and logic instructions can take an optional third operand specifying where to store the result. If omitted, the result is stored in the first operand.

Data Movement
-------------

CP (Copy)
~~~~~~~~~

Copy a value from source to destination.

**Syntax:** ``CP <value>, <ref>``

**Example:**

.. code-block:: nasm

   CP 42, R.a        ; a = 42
   CP R.a, R.b       ; b = a
   CP [100], R.c     ; c = memory[100]

Arithmetic Operations
---------------------

ADD (Add)
~~~~~~~~~

Add two values.

**Syntax:** ``ADD <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   ADD R.a, 5        ; a = a + 5
   ADD R.a, R.b      ; a = a + b
   ADD R.a, R.b, R.c ; c = a + b

SUB (Subtract)
~~~~~~~~~~~~~~

Subtract second value from first.

**Syntax:** ``SUB <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   SUB R.a, 5        ; a = a - 5
   SUB R.a, R.b      ; a = a - b
   SUB R.a, R.b, R.c ; c = a - b

MUL (Multiply)
~~~~~~~~~~~~~~

Multiply two values.

**Syntax:** ``MUL <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   MUL R.a, 3        ; a = a * 3
   MUL R.a, R.b      ; a = a * b
   MUL R.a, R.b, R.c ; c = a * b

DIV (Divide)
~~~~~~~~~~~~

Integer division.

**Syntax:** ``DIV <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   DIV R.a, 2        ; a = a / 2
   DIV R.a, R.b      ; a = a / b
   DIV R.a, R.b, R.c ; c = a / b

**Note:** Raises ``ZeroDivisionError`` if divisor is zero.

MOD (Modulo)
~~~~~~~~~~~~

Remainder after division.

**Syntax:** ``MOD <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   MOD R.a, 10       ; a = a % 10
   MOD R.a, R.b      ; a = a % b
   MOD R.a, R.b, R.c ; c = a % b

Bitwise Operations
------------------

BAND (Bitwise AND)
~~~~~~~~~~~~~~~~~~

Bitwise AND of two values.

**Syntax:** ``BAND <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   BAND R.a, 15      ; a = a & 15
   BAND R.a, R.b     ; a = a & b

BOR (Bitwise OR)
~~~~~~~~~~~~~~~~

Bitwise OR of two values.

**Syntax:** ``BOR <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   BOR R.a, 1        ; a = a | 1
   BOR R.a, R.b      ; a = a | b

BXOR (Bitwise XOR)
~~~~~~~~~~~~~~~~~~

Bitwise XOR of two values.

**Syntax:** ``BXOR <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   BXOR R.a, 255     ; a = a ^ 255
   BXOR R.a, R.b     ; a = a ^ b

BNOT (Bitwise NOT)
~~~~~~~~~~~~~~~~~~

Bitwise NOT (one's complement).

**Syntax:** ``BNOT <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   BNOT R.a          ; a = ~a
   BNOT R.a, R.b     ; b = ~a

BSL (Bit Shift Left)
~~~~~~~~~~~~~~~~~~~~

Shift bits left.

**Syntax:** ``BSL <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   BSL R.a, 1        ; a = a << 1 (multiply by 2)
   BSL R.a, R.b      ; a = a << b

BSR (Bit Shift Right)
~~~~~~~~~~~~~~~~~~~~~

Shift bits right.

**Syntax:** ``BSR <value>, <value>, [<ref>]``

**Example:**

.. code-block:: nasm

   BSR R.a, 1        ; a = a >> 1 (divide by 2)
   BSR R.a, R.b      ; a = a >> b

Comparison Operations
---------------------

All comparison instructions store the result (1 for true, 0 for false) in the output operand.

LT (Less Than)
~~~~~~~~~~~~~~

Check if first value is less than second.

**Syntax:** ``LT <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   LT R.a, 10, R.c   ; c = 1 if a < 10, else 0
   LT R.a, R.b, R.c  ; c = 1 if a < b, else 0

GT (Greater Than)
~~~~~~~~~~~~~~~~~

Check if first value is greater than second.

**Syntax:** ``GT <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   GT R.a, 10, R.c   ; c = 1 if a > 10, else 0

LE (Less Than or Equal)
~~~~~~~~~~~~~~~~~~~~~~~

Check if first value is less than or equal to second.

**Syntax:** ``LE <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   LE R.a, 10, R.c   ; c = 1 if a <= 10, else 0

GE (Greater Than or Equal)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Check if first value is greater than or equal to second.

**Syntax:** ``GE <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   GE R.a, 10, R.c   ; c = 1 if a >= 10, else 0

EQ (Equal)
~~~~~~~~~~

Check if two values are equal.

**Syntax:** ``EQ <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   EQ R.a, 0, R.c    ; c = 1 if a == 0, else 0

NE (Not Equal)
~~~~~~~~~~~~~~

Check if two values are not equal.

**Syntax:** ``NE <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   NE R.a, 0, R.c    ; c = 1 if a != 0, else 0

Logical Operations
------------------

AND (Logical AND)
~~~~~~~~~~~~~~~~~

Logical AND of two values (both non-zero = 1, else 0).

**Syntax:** ``AND <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   AND R.a, R.b, R.c ; c = 1 if a and b are both non-zero

OR (Logical OR)
~~~~~~~~~~~~~~~

Logical OR of two values (either non-zero = 1, else 0).

**Syntax:** ``OR <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   OR R.a, R.b, R.c  ; c = 1 if a or b is non-zero

XOR (Logical XOR)
~~~~~~~~~~~~~~~~~

Logical XOR of two values (exactly one non-zero = 1, else 0).

**Syntax:** ``XOR <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   XOR R.a, R.b, R.c ; c = 1 if exactly one is non-zero

NOT (Logical NOT)
~~~~~~~~~~~~~~~~~

Logical NOT (0 becomes 1, non-zero becomes 0).

**Syntax:** ``NOT <value>, <ref>``

**Example:**

.. code-block:: nasm

   NOT R.a, R.b      ; b = 1 if a == 0, else 0

Control Flow - Unconditional Jumps
-----------------------------------

JMP (Jump)
~~~~~~~~~~

Jump to a label unconditionally.

**Syntax:** ``JMP <label>``

**Example:**

.. code-block:: nasm

   JMP end
   ; ... skipped code ...
   end:

RJMP (Relative Jump)
~~~~~~~~~~~~~~~~~~~~

Jump by offset (forward or backward).

**Syntax:** ``RJMP <value>``

**Example:**

.. code-block:: nasm

   RJMP 2            ; Skip next 2 instructions
   NOUT R.a, 1       ; Skipped
   NOUT R.b, 1       ; Skipped
   NOUT R.c, 1       ; Executed

Control Flow - Conditional Jumps
---------------------------------

All conditional jumps have both absolute (label) and relative (offset) versions.

JEQ / RJEQ (Jump if Equal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump if two values are equal.

**Syntax:** ``JEQ <label>, <value>, <value>`` or ``RJEQ <offset>, <value>, <value>``

**Example:**

.. code-block:: nasm

   JEQ done, R.a, 0   ; Jump to done if a == 0
   RJEQ 2, R.a, R.b   ; Skip 2 instructions if a == b

JNE / RJNE (Jump if Not Equal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump if two values are not equal.

**Syntax:** ``JNE <label>, <value>, <value>``

**Example:**

.. code-block:: nasm

   JNE loop, R.a, 0   ; Jump to loop if a != 0

JGT / RJGT (Jump if Greater Than)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump if first value is greater than second.

**Syntax:** ``JGT <label>, <value>, <value>``

**Example:**

.. code-block:: nasm

   JGT loop, R.a, 0   ; Jump to loop if a > 0

JLT / RJLT (Jump if Less Than)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump if first value is less than second.

**Syntax:** ``JLT <label>, <value>, <value>``

**Example:**

.. code-block:: nasm

   JLT loop, R.a, 10  ; Jump to loop if a < 10

JGE / RJGE (Jump if Greater or Equal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump if first value is greater than or equal to second.

**Syntax:** ``JGE <label>, <value>, <value>``

**Example:**

.. code-block:: nasm

   JGE done, R.a, 100 ; Jump to done if a >= 100

JLE / RJLE (Jump if Less or Equal)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump if first value is less than or equal to second.

**Syntax:** ``JLE <label>, <value>, <value>``

**Example:**

.. code-block:: nasm

   JLE loop, R.a, 10  ; Jump to loop if a <= 10

JIF / RJIF (Jump if Truthy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Jump if value is non-zero.

**Syntax:** ``JIF <label>, <value>``

**Example:**

.. code-block:: nasm

   JIF continue, R.a  ; Jump if a != 0

Function Calls
--------------

CALL (Call Function)
~~~~~~~~~~~~~~~~~~~~

Call a function (pushes return address to stack).

**Syntax:** ``CALL <label>``

**Example:**

.. code-block:: nasm

   CALL my_function
   ; Returns here

   my_function:
       ; ... function code ...
       RET

RCALL (Relative Call)
~~~~~~~~~~~~~~~~~~~~~~

Call function by offset.

**Syntax:** ``RCALL <value>``

**Example:**

.. code-block:: nasm

   RCALL 2           ; Call function 2 instructions ahead

RET (Return)
~~~~~~~~~~~~

Return from function (pops return address from stack).

**Syntax:** ``RET``

**Example:**

.. code-block:: nasm

   my_function:
       ; ... function code ...
       RET           ; Return to caller

Stack Operations
----------------

PUSH (Push to Stack)
~~~~~~~~~~~~~~~~~~~~

Push a value onto the stack.

**Syntax:** ``PUSH <value>``

**Example:**

.. code-block:: nasm

   PUSH R.a          ; Push a onto stack
   PUSH 42           ; Push literal onto stack

POP (Pop from Stack)
~~~~~~~~~~~~~~~~~~~~

Pop a value from the stack.

**Syntax:** ``POP [<ref>]``

**Example:**

.. code-block:: nasm

   POP R.a           ; Pop into register a
   POP               ; Pop and discard

SEMP (Stack Empty)
~~~~~~~~~~~~~~~~~~

Check if stack is empty (1 if empty, 0 otherwise).

**Syntax:** ``SEMP <ref>``

**Example:**

.. code-block:: nasm

   SEMP R.a          ; a = 1 if stack is empty

Input/Output
------------

NOUT (Numeric Output)
~~~~~~~~~~~~~~~~~~~~~

Output a number.

**Syntax:** ``NOUT <value>, <value>``

The second operand controls newline: 0 = no newline, 1 = with newline.

**Example:**

.. code-block:: nasm

   NOUT R.a, 1       ; Print a with newline
   NOUT 42, 0        ; Print 42 without newline

OOUT (Ordinal Output)
~~~~~~~~~~~~~~~~~~~~~

Output a character by ASCII code.

**Syntax:** ``OOUT <value>, <value>``

The second operand controls newline: 0 = no newline, 1 = with newline.

**Example:**

.. code-block:: nasm

   OOUT 'H', 0       ; Print 'H'
   OOUT 65, 0        ; Print 'A' (ASCII 65)
   OOUT 10, 0        ; Print newline character

NIN (Numeric Input)
~~~~~~~~~~~~~~~~~~~

Read a number from input.

**Syntax:** ``NIN <ref>``

**Example:**

.. code-block:: nasm

   NIN R.a           ; Read number into a

OIN (Ordinal Input)
~~~~~~~~~~~~~~~~~~~

Read a single character from input.

**Syntax:** ``OIN <ref>``

**Example:**

.. code-block:: nasm

   OIN R.a           ; Read character into a (as ASCII code)

Special Instructions
--------------------

NOOP (No Operation)
~~~~~~~~~~~~~~~~~~~

Do nothing.

**Syntax:** ``NOOP``

**Example:**

.. code-block:: nasm

   NOOP              ; Does nothing

BRK (Breakpoint)
~~~~~~~~~~~~~~~~

Trigger debugger breakpoint (if in debug mode).

**Syntax:** ``BRK``

**Example:**

.. code-block:: nasm

   CP 5, R.a
   BRK               ; Pause here in debug mode
   MUL R.a, 2

BRKD (Breakpoint with Dump)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Trigger breakpoint and dump CPU state.

**Syntax:** ``BRKD``

**Example:**

.. code-block:: nasm

   BRKD              ; Pause and show state

EXIT (Exit)
~~~~~~~~~~~

Halt program execution immediately.

**Syntax:** ``EXIT``

**Example:**

.. code-block:: nasm

   JEQ early_exit, R.a, 0
   ; ... normal code ...
   JMP end

   early_exit:
       EXIT          ; Stop immediately

   end:

Randomness
----------

RND (Random Bit)
~~~~~~~~~~~~~~~~

Generate a random bit (0 or 1).

**Syntax:** ``RND <ref>``

**Example:**

.. code-block:: nasm

   RND R.a           ; a = 0 or 1 (random)

RINT (Random Integer)
~~~~~~~~~~~~~~~~~~~~~

Generate a random integer in a range (inclusive).

**Syntax:** ``RINT <value>, <value>, <ref>``

**Example:**

.. code-block:: nasm

   RINT 1, 10, R.a   ; a = random integer from 1 to 10
   RINT R.min, R.max, R.result

Quick Reference Table
---------------------

.. list-table::
   :header-rows: 1
   :widths: 15 35 50

   * - Category
     - Instructions
     - Purpose
   * - Data
     - CP
     - Copy values
   * - Arithmetic
     - ADD SUB MUL DIV MOD
     - Basic math
   * - Bitwise
     - BAND BOR BXOR BNOT BSL BSR
     - Bit manipulation
   * - Comparison
     - LT GT LE GE EQ NE
     - Value comparison (result 0/1)
   * - Logic
     - AND OR XOR NOT
     - Boolean logic (result 0/1)
   * - Jumps
     - JMP RJMP
     - Unconditional branching
   * - Conditional
     - JEQ JNE JGT JLT JGE JLE JIF (+ R versions)
     - Conditional branching
   * - Functions
     - CALL RCALL RET
     - Function calls
   * - Stack
     - PUSH POP SEMP
     - Stack manipulation
   * - I/O
     - NOUT OOUT NIN OIN
     - Input/output operations
   * - Random
     - RND RINT
     - Random number generation
   * - Special
     - NOOP BRK BRKD EXIT
     - Control and debugging
