===============
AdvancedLock
===============

An advanced version of Lock.

.. important:: You're required to read this page as I do not take
    any responsibility in it breaking your server.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Run ``[p]setlock`` which will give you a menu of subcommands.
You may not have to use them all (and some will not even let you),
that's why you should start with running 

.. code-block:: none

    [p]setlock setup

The bot will then ask you a few basic questions (depending on your
answers, it could be two, it could be more). 

Once you are done and content with your settings, use 

.. code-block:: none

    [p]setlock toggle
    
to enable/disable the cog.

~~~~~~~~~~~~~~
Initial setup
~~~~~~~~~~~~~~

Now, all the next settings depend on your answers as there's multiple scenarios.
So let me go through the questions and let's number our scenarios.

**Q1:** Do you use roles to access channels? (yes/no)

**Q2:** Do you have different channels that different roles can access? (yes/no)

**Q3:** You answered no but you answered yes to `Do you use roles to access channels?` What roles can access your channels?

**Q4:** Would you like to add default value for when a channel isn't specified? (yes/no)

**Q5:** What are the default roles that can access your channels? (Must be <strong>comma separated</strong>)

**Q6:** What is your Moderator role?

.. list-table:: 
    :widths: 5 10 10 10 10 10 10
    :header-rows: 1
    :stub-columns: 1

    * - ID
      - Q1
      - Q2
      - Q3
      - Q4
      - Q5
      - Q6
    * - 1
      - no
      - doesn't ask
      - doesn't ask
      - doesn't ask
      - doesn't ask
      - Mod role
    * - 2
      - yes
      - no
      - Role1, Role2, ...
      - doesn't ask
      - doesn't ask
      - Mod role
    * - 3
      - yes
      - yes
      - doesn't ask
      - no
      - doesn't ask
      - Mod role
    * - 4
      - yes
      - yes
      - doesn't ask
      - yes
      - Role1, Role2, ...
      - Mod role

These answers will result in the following settings:

.. list-table:: 
    :widths: 5 10 10 10 10 10 10
    :header-rows: 1
    :stub-columns: 1

    * - ID
      - everyone
      - special
      - roles
      - default
      - default roles
      - moderator
    * - 1
      - TRUE
      - FALSE
      - NULL
      - FALSE
      - NULL
      - Mod role
    * - 2
      - FALSE
      - FALSE
      - Role1, Role2, ...
      - FALSE
      - NULL
      - Mod role
    * - 3
      - FALSE
      - TRUE
      - NULL
      - FALSE
      - NULL
      - Mod role
    * - 4
      - FALSE
      - TRUE
      - NULL
      - TRUE
      - Role1, Role2, ...
      - Mod role

~~~~~~~~~~~~~~
Ignored channels
~~~~~~~~~~~~~~

Same as with Lock, you may add channels into an ignored list by running

.. code-block:: none

    [p]setlock ignore <channel>
    
and remove them by running 

.. code-block:: none

    [p]setlock unignore <channel>
    
This will ensure that during server (un)lockdown, these channels will be
kept the same without any change. Use this for channels like announcements.

~~~~~~~~~~~~~~
Special channels
~~~~~~~~~~~~~~

.. important:: If scenario with ID 3 or 4 is your scenario, you are **required** to add
    channels into the list and give them their permissions.

Run 

.. code-block:: none

    [p]setlock add <channel>
    
to add the specified channel into the list. The bot then asks you what role can 
access the channel and saves those permissions.

You can remove the channels' permissions with 

.. code-block:: none

    [p]setlock remove channel

~~~~~~~~~~~~~~
Settings display
~~~~~~~~~~~~~~

You can display your settings by running 

.. code-block:: none

    [p]setlock settings
    
This will fetch all settings for the current server.  

.. tip:: You can also check if all channels have been set/ignored by running

    .. code-block:: none

        [p]setlock all

~~~~~~~~~~~~~~
Settings reset
~~~~~~~~~~~~~~

You may reset all settings to their default value by running 

.. code-block:: none

    [p]setlock reset
    
.. warning:: This action cannot be undone and you will have to go through the
    entire setup all over again!

------------
Usage
------------

Mods may lock the channel, so that only they can type, by running

.. code-block:: none

    [p]lock
    
And letting everyone be able to type in the channel again, by running

.. code-block:: none

    [p]unlock

.. tip:: Mods can also set how many seconds the bot should wait before automatically unlocking the channel by running

    .. code-block:: none

        [p]lock [seconds]

If they wish to lock the entire server, they may use

.. code-block:: none

    [p]lockserver
    
.. warning:: This will overwrite ALL server's channels' permissions.

To unlock the server, type 

.. code-block:: none

    [p]unlockserver

------------
Warning
------------

.. important:: This cog can be extremely dangerous if setup/used incorrectly.

Use at your own risk because I wrote out everything and if it still manages to break
your server, I take no responsibility in it.

I fully support this cog as it's a masterpiece that I am very proud of.
However, it gives your Mods a LOT of power, so use it very wisely.

I tried to put in as many checks as I could, so it should not allow you something
that would break it (if setup correctly) - it has a LOT of 'Uh oh's. However,
I'm still a human and this is my biggest project so far, so it can have some flaws.
It's pretty hard to properly test all possible scenarios, so yeah. Definitely
`open an issue <https://github.com/elijabesu/SauriCogs/issues>`__ if you find
something that could be handled better.

------------
List of commands
------------

``[p]setlock toggle [on_off]`` - Toggle Lock for current server. If on_off is not provided, the state will be flipped.

``[p]setlock setup`` - Go through the initial setup process.

``[p]setlock add <channel>`` - Add channels with special permissions.

``[p]setlock remove <channel>`` - Remove channels with special permissions.

``[p]setlock ignore <channel>`` - Ignore a channel during server lock.

``[p]setlock unignore <channel>`` - Remove channels from the ignored list.

``[p]setlock settings`` - List all channels' settings.

``[p]setlock channel <channel>`` - List channel's settings.

``[p]setlock refresh`` - Refresh settings (deleted channels will be removed from ignored and special channel lists).

``[p]setlock reset`` - Reset all settings to default values.

``[p]setlock all`` - Check if all channels are set.

``[p]lock [seconds]`` - Lock `@everyone` from sending messages. If seconds is provided, the bot will automatically unlock the channel.

``[p]unlock`` - Unlock the channel for `@everyone`.

``[p]lockserver`` - Lock `@everyone` from sending messages in the entire server.

``[p]unlockserver`` - Unlock the entire server for `@everyone`.