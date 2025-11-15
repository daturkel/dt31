Architecture
============

This page explains how dt31's CPU and instruction execution model work under the hood.

CPU Components
--------------

The DT31 CPU has four main components:

Registers
~~~~~~~~~

**Purpose:** Fast, named storage locations.

**Implementation:** Python dict mapping names to integers.

**Default registers:** ``a``, ``b``, ``c``, plus ``ip`` (instruction pointer).

**Characteristics:**

- Named access (``R.a``, ``R.counter``)
- Case-sensitive names
- Dynamically created if auto-detection enabled
- Direct integer storage (no type conversions)

Memory
~~~~~~

**Purpose:** Larger, addressable storage array.

**Implementation:** Python list of integers (fixed size).

**Characteristics:**

- Zero-indexed addressing
- Fixed size (configured at creation, default 256)
- Zero-initialized
- Optional wrapping (out-of-bounds access wraps around if enabled)
- Bounds checking (raises ``MemoryAccessError`` if wrap disabled)

Stack
~~~~~

**Purpose:** Temporary storage and function call management.

**Implementation:** Python ``deque`` (double-ended queue).

**Characteristics:**

- LIFO (Last-In-First-Out) ordering
- Separate from memory (not memory-mapped)
- Fixed maximum size (default 256)
- Overflow/underflow protection
- Used automatically by ``CALL``/``RET`` for return addresses

Instruction Pointer (IP)
~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Track current instruction.

**Implementation:** Integer register (``ip``).

**Behavior:**

- Automatically increments after each instruction
- Modified by jumps and calls
- Accessible via ``cpu.ip``
- Program halts when IP goes out of bounds

Instruction Execution Model
----------------------------

Two-Phase Execution
~~~~~~~~~~~~~~~~~~~

Every instruction executes in two phases:

**Phase 1: Calculate**

The instruction computes its result using ``_calc()`` or directly in ``execute()``.

**Phase 2: Store**

The result is written to the output operand (if applicable).

**Example: ADD instruction**

.. code-block:: python

   class ADD(BinaryOperation):
       def _calc(self, cpu):
           # Phase 1: Calculate
           return self.a.resolve(cpu) + self.b.resolve(cpu)

       # Phase 2: Store (handled by BinaryOperation base class)

This separation allows:

- Clean instruction definitions
- Consistent output handling
- Easy testing (calculate without side effects)

Execution Flow
~~~~~~~~~~~~~~

.. code-block:: text

   1. Fetch instruction at IP
   2. Execute instruction:
      a. Resolve input operands
      b. Calculate result
      c. Store result (if applicable)
   3. Increment IP (or modify for jumps)
   4. Check if halted
   5. Repeat from step 1

**Special cases:**

- ``JMP``/``CALL``: Modify IP directly
- ``RET``: Pop return address from stack to IP
- ``EXIT``: Set halted flag immediately

Operand Resolution
------------------

Operands are resolved differently based on type:

Literals
~~~~~~~~

Return their constant value immediately.

.. code-block:: python

   L[42].resolve(cpu) # Returns: 42

Registers
~~~~~~~~~

Look up value in CPU's register dict.

.. code-block:: python

   R.a.resolve(cpu)  # Returns: cpu.registers['a']

Memory (Direct)
~~~~~~~~~~~~~~~

Index into memory array.

.. code-block:: python

   M[100].resolve(cpu)  # Returns: cpu.memory[100]

Memory (Indirect)
~~~~~~~~~~~~~~~~~

Two-step resolution:

1. Resolve the address operand
2. Index into memory with that address

.. code-block:: python

   M[R.a].resolve(cpu)  # Returns: cpu.memory[cpu.registers['a']]

Labels
~~~~~~

Resolve to instruction index.

.. code-block:: python

   Label("loop").resolve(cpu)  # Returns: 5 (instruction index)

Label Resolution
----------------

Two-Pass Assembly
~~~~~~~~~~~~~~~~~

Labels are resolved in two passes:

**Pass 1: Collect Labels**

- Scan program for label definitions
- Build mapping: ``{label_name: instruction_index}``

**Pass 2: Resolve References**

- Replace label references with instruction indices
- Create final instruction list

**Example:**

.. code-block:: nasm

   ; Source
   JMP end        ; Forward reference
   NOUT R.a, 1
   end:

   ; After Pass 1: {end: 2}
   ; After Pass 2: JMP 2

This allows forward and backward references to work correctly.

Function Calls
--------------

Call Mechanism
~~~~~~~~~~~~~~

``CALL`` instruction:

1. Push current IP + 1 to stack (return address)
2. Set IP to function label

``RET`` instruction:

1. Pop return address from stack
2. Set IP to that address

**Example execution:**

.. code-block:: nasm

   CALL func       ; 1: Push 2, jump to 4
   NOUT R.a, 1     ; 2: (skipped)
   JMP end         ; 3: (skipped)
   func: CP 5, R.a ; 4
   RET             ; 5: Pop 2, jump to 2
   end:            ; 6

Stack Frame
~~~~~~~~~~~

dt31 has no built-in stack frame concept. Functions manage their own state:

- Save values with ``PUSH`` before recursive calls
- Restore values with ``POP`` after
- Pass parameters via registers (calling convention)

Memory Model
------------

Addressing Modes
~~~~~~~~~~~~~~~~

**Direct:**

.. code-block:: nasm

   CP 42, [100]   ; memory[100] = 42

**Indirect:**

.. code-block:: nasm

   CP 100, R.a    ; R.a = 100
   CP 42, [R.a]   ; memory[100] = 42

**Array Access Pattern:**

.. code-block:: nasm

   CP 0, R.i           ; i = 0
   loop:
       CP 10, [R.i]    ; array[i] = 10
       ADD R.i, 1      ; i++
       JLT loop, R.i, 10

Bounds Checking
~~~~~~~~~~~~~~~

**With wrap disabled (default):**

- Out-of-bounds access raises ``MemoryAccessError``
- Negative addresses raise error

**With wrap enabled:**

- Addresses wrap around: ``address % memory_size``
- Negative addresses work: ``-1`` → ``memory_size - 1``

Design Decisions
----------------

Why Python Lists/Dicts?
~~~~~~~~~~~~~~~~~~~~~~~

**Simplicity:** Native Python data structures are easy to understand and debug.

**Performance:** Adequate for educational/toy CPU. Real CPUs would use arrays/registers.

**Flexibility:** Easy to serialize state (JSON dumps).

Why Separate Stack?
~~~~~~~~~~~~~~~~~~~

**Clarity:** Stack operations are conceptually different from memory access.

**Safety:** Can't accidentally corrupt stack via memory operations.

**Efficiency:** ``deque`` is optimized for stack operations.

Why Integer-Only?
~~~~~~~~~~~~~~~~~

**Simplicity:** No type conversions, no floating point edge cases.

**Assembly tradition:** Most assembly languages work with integers.

**Extensibility:** Users can implement floating point via custom instructions if needed.

Performance Characteristics
---------------------------

Time Complexity
~~~~~~~~~~~~~~~

- Register access: O(1) - dict lookup
- Memory access: O(1) - list index
- Stack operations: O(1) - deque operations
- Instruction execution: O(1) per instruction
- Label resolution: O(n) where n = program length (one-time cost)

Space Complexity
~~~~~~~~~~~~~~~~

- Registers: O(r) where r = number of registers
- Memory: O(m) where m = memory size
- Stack: O(s) where s = stack size
- Program: O(n) where n = number of instructions

**Total:** O(r + m + s + n)

For typical programs with default settings: ~512 integers + program size.

Limitations
-----------

No Concurrency
~~~~~~~~~~~~~~

Single-threaded execution only. No interrupts, no multitasking.

No I/O Buffering
~~~~~~~~~~~~~~~~

Input/output is synchronous and unbuffered.

No Memory Protection
~~~~~~~~~~~~~~~~~~~~

All memory is accessible. No segmentation or protection rings.

Fixed Word Size
~~~~~~~~~~~~~~~

Python integers (arbitrary precision), but treated as fixed-width for bitwise operations.

Extensibility
-------------

The architecture is designed to be extended:

**Custom Instructions:**

- Subclass ``Instruction`` or helper classes
- Implement ``_calc()`` or ``execute()``
- Register in ``INSTRUCTIONS`` dict

**Custom Operands:**

- Subclass ``Operand``
- Implement ``resolve()`` and ``store()`` methods

**Custom CPU Behavior:**

- Subclass ``DT31``
- Override ``step()`` or other methods

See :doc:`/tutorials/custom-instructions` for details.

Next Steps
----------

- See :doc:`design-philosophy` for why dt31 is designed this way
- Check :doc:`/api/api-cpu` for CPU API
- Learn :doc:`/tutorials/advanced-topics` for using these concepts
