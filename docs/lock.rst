===============
Lock
===============

Lock `@everyone` from sending messages.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Start by running

.. code-block:: none

    [p]setlock

~~~~~~~~~~~~~~
Ignored channels
~~~~~~~~~~~~~~

You may add channels into an ignored list by running

.. code-block:: none

    [p]lockignore <channel>
    
and remove them by running 

.. code-block:: none

    [p]lockunignore <channel>
    
This will ensure that during server (un)lockdown, these channels will be
kept the same without any change. Use this for channels like announcements.

~~~~~~~~~~~~~~
Settings
~~~~~~~~~~~~~~

If you **DON’T** use roles to access certain channels, skip to 'Usage'.

If you **DO** use roles to access certain channels, your channel permissions need to be 
set a certain way for this cog to work.

Firstly, `@everyone`'s permissions should be set like this:

.. image:: https://i.imgur.com/fOeCA9n.jpg

Secondly, the role(s)'s permissions should be set like this:

.. image:: https://i.imgur.com/pS8wPpI.jpg

------------
Usage
------------

Mods may lock the channel, so that only they can type, by running

.. code-block:: none

    [p]lock
    
And letting everyone be able to type in the channel again, by running

.. code-block:: none

    [p]unlock

If they wish to lock the entire server, they may use

.. code-block:: none

    [p]lockserver
    
.. warning:: This will overwrite ALL server's channels' permissions.

To unlock the server, type 

.. code-block:: none

    [p]unlockserver

------------
List of commands
------------

``[p]locksetup`` – Go through the initial setup process.

``[p]lockignore <channel>`` – Ignore a channel during server lock.

``[p]lockunignore <channel>`` – Remove channels from the ignored list.

``[p]lock`` – Lock `@everyone` from sending messages.

``[p]unlock`` – Unlock the channel for `@everyone`.

``[p]lockserver`` – Lock `@everyone` from sending messages in the entire server.

``[p]unlockserver`` – Unlock the entire server for `@everyone`.