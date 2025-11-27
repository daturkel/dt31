Getting Started
===============

Installation
------------

Install dt31 using pip:

.. code-block:: bash

   pip install dt31

"Hello world!" two ways
------------------------

Let's jump straight into writing programs. We'll write a `"Hello world!" <https://en.wikipedia.org/wiki/%22Hello,_World!%22_program>`_ program in a couple of different ways.

One character at a time
~~~~~~~~~~~~~~~~~~~~~~~

For our first attempt, we'll use the :class:`OOUT <dt31.instructions.OOUT>` instruction to print a single character.
Its syntax is ``OOUT a, b`` where ``a`` is the character, and ``b`` (optional) adds a newline if nonzero.

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
   Text following a ``;`` character is treated as a comment and ignored by the assembler.

Save this to ``hello_world_1.dt`` and run::

   $ dt31 run hello_world_1.dt
   Hello world!

Congrats, you've just written your first dt31 program!

Hello *you*!
~~~~~~~~~~~~

Now let's add a feature: we'll prompt for a name and print ``Hello <name>!`` if provided,
or ``Hello world!`` if the user just hits enter.

Here's the full program:

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

If you save this to ``hello_world_2.dt``, you can test it out::

   $ dt31 run hello_world_2.dt
   > Joe
   Hello Joe!

   $ dt31 run hello_world_2.dt
   >
   Hello world!

Let's break this down. First, note that indentation is purely for readability—the assembler ignores whitespace.

The unindented lines, ending with ``:``, are labels, which mark positions we can jump to: ``world:``, ``name:``, and ``end:``.

The program starts with :class:`STRIN <dt31.instructions.STRIN>`, which prompts for a string and stores it in memory.
dt31 has fixed-size memory where each index holds an integer or character (as its Unicode codepoint). Memory references
use square brackets: ``[123]`` refers to index 123.

``STRIN [0]`` writes the string to memory starting at index 0, one character at a time, ending with a 0 terminator.
For ``Bob``, we write: 66 (the Unicode codepoint for "B") at ``[0]``, 111 ("o") at ``[1]``, 98 ("b") at ``[2]``, and 0 at ``[3]``.

Next we print "Hello " with a series of ``OOUT`` instructions like before.

Now we need to decide: do we print "world" or the user's name? Programs run top-to-bottom unless we jump, so
we use :class:`JIF <dt31.instructions.JIF>`—"jump if," written ``JIF dest, a``—to jump to ``dest`` if ``a`` is nonzero.

``JIF name, [0]`` checks ``[0]``: if it contains a character (the first letter of the name), we jump to the ``name`` label.
Otherwise, ``[0]`` is 0, so we fall through to the next instruction and print "world" with ``OOUT`` instructions.
At the end of the ``world`` section, :class:`JMP <dt31.instructions.JMP>` (unconditional jump) skips to ``end``.

In the scenario where there *is* a name, we pick up from the ``name`` label, which uses :class:`STROUT <dt31.instructions.STROUT>` to print the string from memory.
``STROUT [0]`` reads characters starting at ``[0]`` until it hits the 0 terminator (which you'll recall ``STRIN`` adds after every string).

In both scenarios, we end up at the ``end:`` label, which prints ``!`` with a newline.

Next steps
----------

Now that you've seen the basics of writing dt31 programs, we'll take a tour of some common instructions you'll need. Click
the "Next" button below to continue.
