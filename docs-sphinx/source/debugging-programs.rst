Debugging Programs
==================

This guide covers techniques for finding and fixing bugs in dt31 programs.

Using Debug Mode
----------------

The easiest way to debug is with ``--debug`` mode:

.. code-block:: bash

   dt31 --debug program.dt

This shows:

- Each instruction before execution
- Register state after each instruction
- Program output inline
- Jump targets and control flow

Example output:

.. code-block:: text

   [0] CP 5, R.a
   Registers: {'a': 5, 'b': 0, 'c': 0, 'ip': 1}

   [1] NOUT R.a, 1
   5
   Registers: {'a': 5, 'b': 0, 'c': 0, 'ip': 2}

Step-by-Step Execution in Python
---------------------------------

For fine-grained control, use ``cpu.step()`` in Python:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   cpu = DT31()
   program = parse_program(open("program.dt").read())
   cpu.load(program)

   # Execute one instruction at a time
   while not cpu.halted:
       print(f"\n--- Instruction {cpu.ip} ---")
       print(f"Before: {cpu.get_register('a')=}")

       cpu.step(debug=True)

       print(f"After: {cpu.get_register('a')=}")

       # Add breakpoint conditions
       if cpu.get_register('a') > 100:
           print("BREAKPOINT: a > 100")
           break

This gives you full control to inspect state, set conditions, and pause execution.

Inspecting CPU State
--------------------

Access CPU state during execution:

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[42], R.a),
       I.ADD(R.a, L[10]),
       I.CP(L[100], M[0]),
   ]

   cpu.run(program)

   # Read registers
   print(cpu.get_register('a'))  # 52
   print(cpu.get_register('b'))  # 0

   # Read memory
   print(cpu.get_memory(0))      # 100

   # Get full state
   state = cpu.state
   print(state['registers'])     # All registers
   print(state['memory'])        # Entire memory array
   print(state['stack'])         # Stack contents
   print(state['ip'])            # Instruction pointer

Using CPU Dumps
---------------

Capture complete CPU state to JSON:

.. code-block:: bash

   # Dump on errors
   dt31 --dump error program.dt

   # Dump on success
   dt31 --dump success program.dt

   # Always dump
   dt31 --dump all program.dt

This creates files like ``program_error_20231113_143022.json``.

Analyzing Dump Files
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import json

   # Load dump file
   with open("program_error_20231113_143022.json") as f:
       dump = json.load(f)

   # Inspect state
   print("Registers:", dump['cpu_state']['registers'])
   print("Stack:", dump['cpu_state']['stack'])

   # See what caused the error
   if 'error' in dump:
       print("Error type:", dump['error']['type'])
       print("Error message:", dump['error']['message'])
       print("Failing instruction:", dump['error']['instruction']['str'])

Common Issues
-------------

Infinite Loops
~~~~~~~~~~~~~~

**Symptom:** Program never terminates.

**Debug:**

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   cpu = DT31()
   program = parse_program(open("program.dt").read())
   cpu.load(program)

   max_steps = 1000
   for i in range(max_steps):
       if cpu.halted:
           break
       cpu.step()

       # Track instruction pointer
       if i % 100 == 0:
           print(f"Step {i}, IP: {cpu.ip}")
   else:
       print(f"Terminated after {max_steps} steps - possible infinite loop")
       print(f"Last IP: {cpu.ip}")
       print(f"Registers: {cpu.state['registers']}")

**Common causes:**

- Loop condition never becomes false
- Missing exit condition
- Wrong jump target

.. code-block:: nasm

   ; Bug: never decrements counter
   CP 5, R.a
   loop:
       NOUT R.a, 1
       ; Missing: SUB R.a, 1
       JGT loop, R.a, 0  ; Always true!

Wrong Output
~~~~~~~~~~~~

**Symptom:** Program produces incorrect results.

**Debug:** Add output statements to trace values:

.. code-block:: nasm

   ; Debug version with tracing
   CP 10, R.a
   NOUT R.a, 1         ; Debug: print a
   CP 5, R.b
   NOUT R.b, 1         ; Debug: print b
   ADD R.a, R.b
   NOUT R.a, 1         ; Debug: print result

Or in Python:

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[10], R.a),
       I.CP(L[5], R.b),
       I.ADD(R.a, R.b),
   ]

   # Run with debug=True
   cpu.run(program, debug=True)

Stack Overflow
~~~~~~~~~~~~~~

**Symptom:** ``StackOverflowError`` or ``IndexError`` on stack operations.

**Causes:**

- Too many ``PUSH`` operations
- Recursive function with no base case
- Stack too small for recursion depth

**Debug:**

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   # Increase stack size
   cpu = DT31(stack_size=1024)
   program = parse_program(open("recursive.dt").read())

   try:
       cpu.run(program)
   except Exception as e:
       print(f"Stack size at crash: {len(cpu.stack)}")
       print(f"Stack contents: {cpu.stack}")
       raise

Or from CLI:

.. code-block:: bash

   dt31 --stack-size 1024 recursive.dt

Memory Access Errors
~~~~~~~~~~~~~~~~~~~~

**Symptom:** ``MemoryAccessError`` or ``IndexError`` on memory operations.

**Causes:**

- Accessing memory address beyond bounds
- Using negative memory address
- Indirect addressing with wrong register value

**Debug:**

.. code-block:: python

   from dt31 import DT31, I, L, M, R

   cpu = DT31(memory_size=256)

   program = [
       I.CP(L[300], R.a),  # Address too large
       I.CP(L[42], M[R.a]),  # Will fail
   ]

   try:
       cpu.run(program, debug=True)
   except Exception as e:
       print(f"Memory size: {len(cpu.memory)}")
       print(f"Attempted address: {cpu.get_register('a')}")
       raise

**Fix:** Either increase memory size or fix the address:

.. code-block:: bash

   dt31 --memory 512 program.dt

Or fix the program:

.. code-block:: nasm

   ; Use valid address
   CP 100, R.a          ; 100 < 256
   CP 42, [R.a]         ; OK

Division by Zero
~~~~~~~~~~~~~~~~

**Symptom:** ``ZeroDivisionError``

**Debug:**

.. code-block:: nasm

   ; Add check before division
   CP 10, R.a
   CP 0, R.b

   ; Check if b is zero
   JEQ skip_div, R.b, 0
   DIV R.a, R.b
   JMP continue

   skip_div:
       OOUT 'E', 0    ; Print error
       OOUT 'r', 0
       OOUT 'r', 1

   continue:

Jump to Invalid Address
~~~~~~~~~~~~~~~~~~~~~~~

**Symptom:** ``InvalidJumpError`` or program ends unexpectedly.

**Debug:** Check label definitions and jump targets:

.. code-block:: bash

   dt31 --debug program.dt

Look for:

- Undefined labels
- Typos in label names (labels are case-sensitive!)
- Relative jumps with wrong offset

.. code-block:: nasm

   ; Bug: typo in label name
   JMP loo      ; Should be 'loop'

   loop:
       NOUT R.a, 1

Advanced Debugging Techniques
------------------------------

Conditional Breakpoints
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   cpu = DT31()
   program = parse_program(open("program.dt").read())
   cpu.load(program)

   while not cpu.halted:
       # Breakpoint: stop when a > 50
       if cpu.get_register('a') > 50:
           print("BREAKPOINT HIT")
           print(f"IP: {cpu.ip}")
           print(f"Registers: {cpu.state['registers']}")

           # Interactive debugging
           import pdb; pdb.set_trace()

       cpu.step()

Memory Watchpoints
~~~~~~~~~~~~~~~~~~

Track when specific memory addresses change:

.. code-block:: python

   from dt31 import DT31, I, L, M, R

   cpu = DT31()

   watched_address = 100
   last_value = None

   program = [
       I.CP(L[42], M[100]),
       I.ADD(M[100], L[10]),
       I.CP(M[100], R.a),
   ]

   cpu.load(program)

   while not cpu.halted:
       cpu.step()

       current = cpu.get_memory(watched_address)
       if current != last_value:
           print(f"Memory[{watched_address}] changed: {last_value} -> {current}")
           last_value = current

Register History
~~~~~~~~~~~~~~~~

Track register changes over time:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program

   cpu = DT31()
   program = parse_program(open("program.dt").read())
   cpu.load(program)

   history = []

   while not cpu.halted:
       # Record state before each instruction
       history.append({
           'ip': cpu.ip,
           'registers': cpu.state['registers'].copy()
       })
       cpu.step()

   # Analyze history
   print("Register 'a' over time:")
   for i, state in enumerate(history):
       print(f"Step {i}: {state['registers']['a']}")

Execution Profiling
~~~~~~~~~~~~~~~~~~~

Find which instructions execute most frequently:

.. code-block:: python

   from dt31 import DT31
   from dt31.parser import parse_program
   from collections import Counter

   cpu = DT31()
   program = parse_program(open("program.dt").read())
   cpu.load(program)

   ip_counts = Counter()

   while not cpu.halted:
       ip_counts[cpu.ip] += 1
       cpu.step()

   print("Most executed instructions:")
   for ip, count in ip_counts.most_common(10):
       print(f"[{ip}]: {count} times")

Comparing Expected vs Actual
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from dt31 import DT31, I, L, R

   cpu = DT31()
   program = [
       I.CP(L[5], R.a),
       I.MUL(R.a, L[3]),  # a = 15
   ]

   cpu.run(program)

   expected = 15
   actual = cpu.get_register('a')

   assert actual == expected, f"Expected {expected}, got {actual}"
   print("✓ Test passed")

Debugging Custom Instructions
------------------------------

Add print statements in ``_calc``:

.. code-block:: python

   from dt31.instructions import UnaryOperation
   from dt31.operands import Operand, Reference

   class DEBUG_SQUARE(UnaryOperation):
       def __init__(self, a: Operand, out: Reference | None = None):
           super().__init__("DEBUG_SQUARE", a, out)

       def _calc(self, cpu) -> int:
           value = self.a.resolve(cpu)
           result = value * value

           # Debug output
           print(f"DEBUG_SQUARE: {value}^2 = {result}")

           return result

Common Patterns
---------------

Assert-Style Debugging
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Test that a equals 10
   CP 10, R.expected
   EQ R.a, R.expected, R.test
   JIF continue, R.test
   ; Failed: print error and halt
   OOUT 'F', 0
   OOUT 'A', 0
   OOUT 'I', 0
   OOUT 'L', 1
   JMP end

   continue:
   ; Test passed, continue...

Print Debugging
~~~~~~~~~~~~~~~

.. code-block:: nasm

   ; Trace execution path
   OOUT 'A', 1     ; Mark checkpoint A
   ; ... code ...
   OOUT 'B', 1     ; Mark checkpoint B
   ; ... code ...
   OOUT 'C', 1     ; Mark checkpoint C

Tips
----

1. **Start simple:** Test with minimal input first
2. **Use debug mode:** Always try ``--debug`` first
3. **Check your math:** Verify calculations manually
4. **Read error messages:** They usually point to the problem
5. **Dump on error:** Use ``--dump error`` to capture state
6. **Test incrementally:** Add code gradually and test often
7. **Check labels:** Label typos are common (case-sensitive!)
8. **Watch the stack:** Unbalanced PUSH/POP causes issues
9. **Verify jumps:** Make sure jump conditions are correct
10. **Use version control:** Git helps track when bugs were introduced
