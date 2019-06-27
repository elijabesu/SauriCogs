===============
Pingable
===============

Make unpingable roles pingable by regular users with commands.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Set a pingable role with 

.. code-block:: none

    [p]setpingable <role>

and then create an alias for it (this is optional). 

------------
usage
------------

Members can just use the alias along with their message to ping the roles.

------------
List of commands
------------

``[p]setpingable <role>`` – Make a role pingable. <role> can be a name or an ID.

``[p]delpingable <role>`` – Make a role unpingable. <role> can be a name or an ID.

``[p]pingable <role> <message>`` – Ping a role.