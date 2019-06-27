===============
Suggestion
===============

A bit more than just a simple suggestion box. Only admins can approve or reject suggestions.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Start by running

.. code-block:: none

    [p]setsuggest setup

The bot will ask you if you have your channels already present. If yes, it asks 
you to mention them so it can save them. If not, it will create them (default 
permissions are everyone can see the channels but cannot send messages). 
Since both approved and rejected channels are optional, it asks if you want them. 
If you say you don't, it will ask if you want to use the same one channel for all.


~~~~~~~~~~~~~~
Global suggestions
~~~~~~~~~~~~~~

To enable global suggestions, you need to add the channel where the bot can post them by 
running

.. code-block:: none

    [p]setsuggest setglobal channel [server] [channel]

If you don't provide [server] nor [channel], it will save the current channel. Otherwise, 
you have to provide both.

Then toggle global suggestions by running

.. code-block:: none

    [p]setsuggest setglobal toggle

------------
Usage
------------

Once the cog is properly set up (``[p]setsuggest setup`` has been finished), 
users may start using 

.. code-block:: none

    [p]suggest <suggestion>

~~~~~~~~~~~~~~
Approve/Reject
~~~~~~~~~~~~~~

To approve someone's suggestion, use 

.. code-block:: none

    [p]approve <suggestion ID> [global]

To reject someone's suggestion, use 

.. code-block:: none

    [p]reject <suggestion ID> [global] [reason]

Since `[reason]` is optional, you can add it whenever you want by using 

.. code-block:: none

    [p]addreason <suggestion ID> [global] <reason>

------------
List of commands
------------

``[p]suggest <suggestion>`` – Suggest something.

``[p]approve <suggestion ID> [global]`` – Approve a suggestion. 
If you're approving a global suggestion, add 'True' or 'yes' after the ID.

``[p]reject <suggestion ID> [global] [reason]`` – Reject a suggestion. 
If you're rejecting a global suggestion, add 'True' or 'yes' after the ID.

``[p]addreason <suggestion ID> [global] <reason>`` – Add a reason to a rejected suggestion. 
If you're adding a reason to a global suggestion, add 'True' or 'yes' after the ID.

``[p]showsuggestion <suggestion ID> [global]`` – Show a suggestion. If you want to see 
a global suggestion, add 'True' or 'yes' after the ID.

``[p]setsuggest setup`` – Go through the initial setup process.

``[p]setsuggest setglobal toggle [on_off]`` – Toggle global suggestions. 
If on_off is not provided, the state will be flipped.

``[p]setsuggest setglobal channel [server] [channel]`` – Add channel where global 
suggestions should be sent.

``[p]setsuggest setglobal ignore [server]`` - Ignore suggestions from the server.

``[p]setsuggest setglobal unignore [server]`` - Remove server from the ignored list.