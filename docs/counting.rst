===============
Counting
===============

Counting channel!

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

All you need to do is enable counting by running

.. code-block:: none

    [p]countchannel <channel>

------------
Usage
------------

After setting it up, you can start counting by sending the following number in the channel.

.. note:: If the message isn’t just a number, it will be deleted.

    If the message is a wrong number, it will be deleted.

    If the number message is deleted, the bot replaces it.

------------
List of commands
------------

``[p]countchannel [channel]`` – Set the counting channel. If channel isn’t provided, 
it will delete the current channel.

``[p]countgoal [goal]`` – Set the counting goal. If goal isn’t provided, it will be deleted.

``[p]countreset`` – Reset the counter and start from 0 again!

``[p]countrole [role]`` - Add a whitelisted role.