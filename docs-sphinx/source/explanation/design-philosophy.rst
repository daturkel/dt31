Design Philosophy
=================

This page explains the principles and decisions behind dt31's design.

Core Principles
---------------

Educational First
~~~~~~~~~~~~~~~~~

**Goal:** Help people learn about CPU architecture and assembly programming.

**How:**

- Simple, understandable implementation
- Clear instruction names (``ADD`` not ``0x01``)
- Readable source code
- Comprehensive documentation
- Examples for every concept

**Trade-offs:**

- Performance sacrificed for clarity
- Features limited to core concepts
- No obscure CPU features

Zero Dependencies
~~~~~~~~~~~~~~~~~

**Goal:** Easy installation and distribution.

**How:**

- Pure Python implementation
- Standard library only
- No C extensions
- No external packages

**Benefits:**

- ``pip install dt31`` just works
- No compilation needed
- Easy to audit code
- Portable across platforms

**Trade-offs:**

- Slower than compiled alternatives
- Can't leverage specialized libraries

Intuitive API
~~~~~~~~~~~~~

**Goal:** Make writing programs feel natural.

**How:**

- Clean operand syntax: ``R.a``, ``M[100]``, ``L[42]``
- Pythonic patterns (walrus operator for labels)
- Familiar instruction names
- Consistent conventions

**Examples:**

.. code-block:: python

   # Intuitive
   I.ADD(R.a, L[5])
   loop := Label("loop")

   # vs. hypothetical alternatives
   Instruction(OP_ADD, Reg(0), Lit(5))
   loop = LabelDef(); program.append(loop)

Dual Syntax
~~~~~~~~~~~

**Goal:** Support both assembly text and Python API.

**Why:**

- Assembly: Traditional, standalone programs
- Python: Programmatic generation, integration

**Implementation:**

- Parser converts assembly → Python
- Assembler converts Python → assembly
- Round-trip conversion works

**Benefit:** Learn either way, use both interchangeably.

Design Decisions
----------------

Why Three Registers?
~~~~~~~~~~~~~~~~~~~~

**Choice:** Default to three registers (``a``, ``b``, ``c``).

**Rationale:**

- Enough for most examples (two operands + result)
- Simple to remember
- Forces thinking about register allocation
- Easily expandable when needed

**Alternative considered:** More registers by default.

**Why not:** Would make examples more complex.

Why Fixed-Size Memory?
~~~~~~~~~~~~~~~~~~~~~~

**Choice:** Memory is fixed-size array, configured at CPU creation.

**Rationale:**

- Matches real hardware constraints
- Forces awareness of memory limits
- Prevents unbounded growth
- Makes state dumps finite

**Alternative considered:** Dynamic/infinite memory.

**Why not:** Hides important constraint, less educational.

Why Case-Insensitive Instructions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Choice:** Instruction names are case-insensitive in assembly.

**Rationale:**

- Assembly tradition (varies by assembler)
- User-friendly for beginners
- ``ADD`` and ``add`` both work

**But:** Registers and labels are case-sensitive.

**Why:** More Pythonic (identifiers are case-sensitive).

Why No Memory-Mapped I/O?
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Choice:** I/O uses special instructions (``NIN``, ``NOUT``, etc.), not memory addresses.

**Rationale:**

- Simpler to understand
- Clearer separation of concerns
- No magic memory addresses
- Easier to implement

**Alternative considered:** Memory-mapped I/O (like real CPUs).

**Why not:** More complex, less clear for beginners.

Why Python?
~~~~~~~~~~~

**Choice:** Implement in Python, not C/C++/Rust.

**Rationale:**

- Readable implementation (matches documentation)
- Easy to modify and extend
- Platform-independent
- Large user base
- Good for prototyping

**Trade-offs:**

- Slower execution
- Higher memory usage

**Justification:** Speed doesn't matter for educational toy CPU.

Why No Floating Point?
~~~~~~~~~~~~~~~~~~~~~~~

**Choice:** Integer-only arithmetic.

**Rationale:**

- Simpler implementation
- Avoids floating point precision issues
- Matches most assembly language traditions
- Sufficient for core concepts

**Extensibility:** Users can add floating point via custom instructions if needed.

Why Two-Pass Assembly?
~~~~~~~~~~~~~~~~~~~~~~~

**Choice:** Use two-pass assembler for label resolution.

**Rationale:**

- Standard assembler technique
- Allows forward label references
- Educational value (learn how assemblers work)
- Clean implementation

**Alternative considered:** Single-pass with backpatching.

**Why not:** More complex, less clear.

API Design Choices
------------------

Why Walrus Operator for Labels?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Pattern:**

.. code-block:: python

   loop := Label("loop")

**Rationale:**

- Pythonic (uses modern Python feature)
- Define and reference in one line
- Reads naturally
- Compact

**Alternative:**

.. code-block:: python

   loop = Label("loop")
   program.append(loop)

**Why not:** More verbose, less elegant.

Why Namespace Objects (I, R, M)?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Pattern:**

.. code-block:: python

   I.ADD(R.a, M[100])

**Rationale:**

- Clean imports (``from dt31 import I, R, M``)
- IDE autocomplete works
- Clear what each thing is (``I`` = instruction, ``R`` = register, ``M`` = memory)
- Prevents namespace pollution

**Alternative:** Import everything individually.

**Why not:** Cluttered namespace, less organized.

Why Operand Types?
~~~~~~~~~~~~~~~~~~

**Choice:** Separate classes for ``Literal``, ``Register``, ``Memory``, etc.

**Rationale:**

- Type safety
- Clear semantics
- Extensible (users can add operand types)
- Enables compile-time checks

**Alternative:** Just use integers/strings.

**Why not:** Ambiguous, error-prone.

Pedagogical Philosophy
----------------------

Learning by Doing
~~~~~~~~~~~~~~~~~

dt31 is designed for hands-on learning:

- Small enough to understand completely
- Simple enough to modify
- Examples progress from basic to advanced
- Encourages experimentation

Incremental Complexity
~~~~~~~~~~~~~~~~~~~~~~

Features build on each other:

1. **Basic:** Arithmetic, registers, output
2. **Intermediate:** Loops, conditionals, memory
3. **Advanced:** Functions, recursion, custom instructions

Transparent Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Source code is documentation
- No "magic" - everything is explicit
- Comments explain why, not just what
- Design patterns are visible

Constraints as Learning
~~~~~~~~~~~~~~~~~~~~~~~

Limitations are educational:

- Fixed memory → think about space
- Limited registers → plan allocation
- Integer-only → understand representation
- Manual stack management → learn calling conventions

Trade-offs
----------

What We Sacrificed
~~~~~~~~~~~~~~~~~~

**Performance:**

- Python is slower than C/Rust
- No JIT compilation
- No optimization passes

**Realism:**

- No pipelining
- No caching
- No parallel execution
- No interrupts/exceptions

**Features:**

- No floating point (by default)
- No SIMD
- No memory protection
- No virtual memory

What We Gained
~~~~~~~~~~~~~~

**Clarity:**

- Readable implementation
- Understandable source
- Clear behavior

**Accessibility:**

- Easy to install
- Works everywhere
- Low barrier to entry

**Flexibility:**

- Easy to extend
- Simple to modify
- Quick to prototype

**Educational Value:**

- Teaches core concepts
- Shows tradeoffs clearly
- Encourages exploration

Future Directions
-----------------

Potential Enhancements
~~~~~~~~~~~~~~~~~~~~~~

While maintaining core principles, dt31 could add:

- **Macros**: Text replacement in assembly
- **File I/O**: Read/write files
- **Data section**: Separate code and data
- **Debugging API**: More introspection tools
- **Visualization**: Graphical CPU state viewer

What Won't Be Added
~~~~~~~~~~~~~~~~~~~

To preserve simplicity:

- Multi-threading/concurrency
- Floating point (built-in)
- Complex memory models
- Operating system features
- Network I/O

Comparison with Alternatives
-----------------------------

vs. Real Assembly
~~~~~~~~~~~~~~~~~

**Real assembly (x86, ARM):**

- Pros: Real-world relevant, fast, powerful
- Cons: Complex, platform-specific, hard to learn

**dt31:**

- Pros: Simple, portable, educational
- Cons: Toy, slow, limited

**Use case:** dt31 for learning, real assembly for production.

vs. Other Educational CPUs
~~~~~~~~~~~~~~~~~~~~~~~~~~

**MIPS, RISC-V educational tools:**

- Pros: Closer to real hardware, standardized
- Cons: Still complex, C-based, harder to modify

**dt31:**

- Pros: Simpler, Python-based, very hackable
- Cons: Less realistic, not standardized

**Use case:** dt31 for absolute beginners, others for CS courses.

vs. Emulators (QEMU, etc.)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Full system emulators:**

- Pros: Run real OS, complete hardware
- Cons: Very complex, slow, hard to understand

**dt31:**

- Pros: Minimal, fast to learn, transparent
- Cons: Not usable for real software

**Use case:** dt31 for concepts, emulators for compatibility.

Philosophy Summary
------------------

dt31 prioritizes:

1. **Educational value** over performance
2. **Simplicity** over features
3. **Clarity** over optimization
4. **Accessibility** over realism
5. **Hackability** over robustness

The goal is a **teaching tool**, not a production system.

Next Steps
----------

- See :doc:`architecture` for implementation details
- Check :doc:`/tutorials/custom-instructions` to extend dt31
- Browse the `source code <https://github.com/daturkel/dt31>`_ to see these principles in action
