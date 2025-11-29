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

For our first attempt, we'll use the :class:`COUT <dt31.instructions.COUT>` **instruction** to print a single character.
Its syntax is ``COUT a, b`` where ``a`` is the character, and ``b`` (optional) adds a newline if nonzero.

.. code-block:: nasm

   COUT 'H'
   COUT 'e'
   COUT 'l'
   COUT 'l'
   COUT 'o'
   COUT ' '
   COUT 'w'
   COUT 'o'
   COUT 'r'
   COUT 'l'
   COUT 'd'
   COUT '!', 1  ; add a newline after the "!"

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
      COUT 'H'       ; print "Hello "
      COUT 'e'
      COUT 'l'
      COUT 'l'
      COUT 'o'
      COUT ' '
      JIF name, [0]  ; jump to `name` if index 0 is nonzero

   world:            ; print "world"
      COUT 'w'
      COUT 'o'
      COUT 'r'
      COUT 'l'
      COUT 'd'
      JMP end        ; jump to `end`

   name:
      STROUT [0]     ; print string starting at [0]

   end:
      COUT '!', 1    ; print "!" with a newline

.. NOTE::
   Indentation is just for readability. dt31 ignores most whitespace within a line.

If you save this to ``hello_world_2.dt``, you can test it out::

   $ dt31 run hello_world_2.dt
   > Joe
   Hello Joe!

   $ dt31 run hello_world_2.dt
   >
   Hello world!

Let's break this down in parts.

Strings
^^^^^^^

.. code-block:: nasm

   STRIN [0]      ; write name starting at index 0
   COUT 'H'       ; print "Hello "
   COUT 'e'
   COUT 'l'
   COUT 'l'
   COUT 'o'
   COUT ' '

The program starts with :class:`STRIN <dt31.instructions.STRIN>`, which prompts for a string and stores it in **memory**.
dt31 has fixed-size memory where each index holds an integer or character (stored as its Unicode codepoint). Memory references
use square brackets: ``[123]`` refers to the data stored at index 123.

``STRIN [0]`` writes the string to memory starting at index 0, one character at a time, ending with a 0 terminator.
For ``Bob``, the resulting memory looks like this:

+---------------+----+-----+----+--------+
| Index:        | 0  | 1   | 2  | 3      |
+===============+====+=====+====+========+
| Value stored: | 66 | 111 | 98 | 0      |
+---------------+----+-----+----+--------+
| Character:    | B  | o   | b  | (null) |
+---------------+----+-----+----+--------+

Then we print "Hello " with a series of ``COUT`` instructions like before.

Jumping around
^^^^^^^^^^^^^^

Programs run top-to-bottom unless we **jump**, so we use :class:`JIF <dt31.instructions.JIF>`—"jump if," written ``JIF dest, a``—to jump to ``dest`` if ``a`` is nonzero.
The lines ending with ``:`` are **labels** marking positions we can jump to: ``world:``, ``name:``, and ``end:``.

.. code-block:: nasm

       JIF name, [0]  ; jump to `name` if index 0 is nonzero

   world:            ; print "world"
       COUT 'w'
       COUT 'o'
       COUT 'r'
       COUT 'l'
       COUT 'd'
       JMP end        ; jump to `end`

   name:
      STROUT [0]     ; print string starting at [0]

``JIF name, [0]`` checks ``[0]``: if it contains a character (the first letter of the name), we jump to the ``name`` label.
Otherwise, ``[0]`` is 0, so we fall through to the next instruction and print "world" with ``COUT`` instructions.
At the end of the ``world`` section, :class:`JMP <dt31.instructions.JMP>` (unconditional jump) skips to ``end``.

In the scenario where there *is* a name, we pick up from the ``name`` label, which uses :class:`STROUT <dt31.instructions.STROUT>` to print the string from memory.
``STROUT [0]`` reads characters starting at ``[0]`` until it hits the 0 terminator (which you'll recall ``STRIN`` adds after every string).

.. code-block:: nasm

   end:
      COUT '!', 1    ; print "!" with a newline

In both scenarios, we end up at the ``end:`` label, which prints ``!`` with a newline.

Next steps
----------

Now that you've seen the basics of writing dt31 programs, we'll take a tour of some common instructions you'll need. Click
the "Next" button below to continue.
