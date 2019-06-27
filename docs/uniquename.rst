===============
UniqueName
===============

Deny members' names to be the same as your Moderators'.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Firstly, you need to add at least one protected role by running

.. code-block:: none

    [p]unset role <role>

Roles added through this command are considered as the originals/uniques.

Secondly (and also finally), you need to toggle the cog by running

.. code-block:: none

    [p]unset toggle

------------
List of commands
------------

``[p]unset role <role>`` - Add a role to the original list (f.e. Moderator or Admin role).

``[p]unset name <name>`` - Set a default name that will be set.

``[p]unset toggle [on_off]`` - Toggle UniqueName for this server. If `on_off` 
is not provided, the state will be flipped.