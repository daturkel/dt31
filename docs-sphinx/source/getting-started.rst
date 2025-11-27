Getting Started
===============

Installation
------------

Install dt31 using pip:

.. code-block:: bash

   pip install dt31

"Hello world!" two ways
------------------------

Rather than putting a bunch of syntax and technicalities up front, let's jump straight into writing some programs.

To build up our understanding, we'll write a `"Hello world!" <https://en.wikipedia.org/wiki/%22Hello,_World!%22_program>`_ program,
which simply prints ``Hello world!``, in a couple of different ways.

One character at a time
~~~~~~~~~~~~~~~~~~~~~~~

For our first attempt, we'll only use just one instruction, but we're going to use it many times.
The :class:`OOUT <dt31.instructions.OOUT>` instruction lets us print a single character. It's syntax is ``OOUT a, b`` where
``a`` is the character to be printed, and if ``b`` is nonzero, we append a newline. If we don't need a newline,
we can omit ``b`` completely.

.. code-block:: nasm

   OOUT 'H'
   OOUT 'e'
   OOUT 'l'
   OOUT 'l'
   OOUT 'o'
   OOUT ' '
   OOUT 'w'
   OOUT 'o'
   OOUT 'r'
   OOUT 'l'
   OOUT 'd'
   OOUT '!', 1 ; add a newline after the "!"

.. NOTE::
   Notice how the last line of our program has a comment. Any text following a ``;`` character is ignored
   by the assembler.

We can now run this program with ``dt31 run``. Save it to a file called ``hello_world_1.dt`` and run::

   dt31 run hello_world_1.dt

and you will see the output::

   Hello world!

Great, we've just written our first dt31 program!

Hello *you*!
------------

Next up we're going to customize our program. It's going to prompt the user to enter their name. If they
provide a name, we'll print ``Hello <name>!`` If the user just hits enter without entering anything, we'll
print ``Hello world!`` as before.

Let's take a look at the full program first, then we'll break down what's going on:

.. code-block:: nasm

      STRIN [0]      ; write name starting at index 0
      OOUT 'H'       ; print "Hello "
      OOUT 'e'
      OOUT 'l'
      OOUT 'l'
      OOUT 'o'
      OOUT ' '
      JIF name, [0]  ; jump to `name` if index 0 is nonzero

   world:             ; print "world"
      OOUT 'w'
      OOUT 'o'
      OOUT 'r'
      OOUT 'l'
      OOUT 'd'
      JMP end        ; jump to `end`

   name:
      STROUT [0]     ; print string starting at [0]

   end:
      OOUT '!', 1    ; print "!" with a newline


There's a lot going on here, so let's take it piece by piece.

First off, you'll notice that most of the program is indented. The dt31 assembler doesn't care
about whitespace, so indentation and newlines can be used purely to make it more human-readable.
In this case, we indent the code to make the labels stand out, which is fairly common in *real* assembly languages.

The aforementioned labels are the lines ending in a colon: ``world:``, ``name:``, ``end:`` These
allow us to set positions in the code that we can jump to with special jump instructions. Labels are
detected and reference to labels (e.g. ``JMP end``) are replaced with with
numeric references to the instruction number to jump to. In this case, ``JMP end`` becomes ``JMP 16`` because
the next instruction after the label (``OOUT '!', 1``) is instruction 16.

At the start of the program, we see a new instruction: :class:`STRIN <dt31.instructions.STRIN>`. This instruction
takes a single argument that must be a reference to a point in memory. The dt31 virtual computer has a fixed
amount of memory, where each index can hold an integer or character (encoded as their Unicode codepoint). References
to memory are written with square brackets, so ``[123]`` refers to index 123 in memory. Putting this together,
``STRIN [0]`` prompts the user for a string and writes it to memory, one character at a time, starting at index 0.
At the end of the string, we write a 0 to indicate the end of the string. If the user provided ``Bob``, then we'll
write 66 (the Unicode codepoint for "B") at index 0, 111 to index 1 ("o"), 98 to index 2 ("b"), and 0 to index 3.

Since we're going to print "Hello " no matter what, we then proceed directly into that with a series of ``OOUT`` instructions.

Next we have to make a decision: do we print "world!" or the user's name? If it's not told otherwise, dt31 programs will
just run straight from top to bottom, so we need some way to decide which section of code to run. Blah blah :class:`JIF <dt31.instructions.JIF>`
