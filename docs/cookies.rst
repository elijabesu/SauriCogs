===============
Cookies
===============

Collect cookies.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------
By default, members receive one cookie, cooldown is 24 hours, stealing is disabled
and stealing cooldown is 12 hours.

You can set how many cookies members get by running

.. code-block:: none

    [p]setcookies amount <amount>

If you put amount as ``0``, the bot will ask you to put the minimum and maximum amount
for a random amount.

~~~~~~~~~~~~~~
Stealing
~~~~~~~~~~~~~~

To enable stealing, run 

.. code-block:: none

    [p]setcookies steal

You can change the cooldowns with 

.. code-block:: none

    [p]setcookies cooldown <seconds>

and 

.. code-block:: none

    [p]setcookies stealcooldown <seconds>

~~~~~~~~~~~~~~
Cookie rewards
~~~~~~~~~~~~~~

You can also set cookie rewards for gaining a certain role by running

.. code-block:: none

    [p]setcookies role add <role> <amount>

and remove it by

.. code-block:: none

    [p]setcookies role del <role>

------------
Usage
------------

Members collect cookies by simply running

.. code-block:: none

    [p]cookie

To see how many they have, they can run

.. code-block:: none

    [p]cookies

Cookie leaderboard can be seen by running

.. code-block:: none

    [p]cookielb

To give someone some of their cookies, they can run

.. code-block:: none

    [p]gift <target> <amount>

Stealing is done by running

.. code-block:: none

    [p]steal [target]

where target is optional, if not provided, it's a randomly chosen member of the server.
They can steal up to 50% of the target's cookies.

.. warning:: Penalty for failing stealing can be up to 25% of the author's (your) cookies.

------------
List of commands
------------

``[p]cookie`` – Get your daily dose of cookies.

``[p]steal [target]`` – Steal cookies from members. If [target] isn’t specified, target will be randomly chosen.

``[p]gift <target> <amount>`` – Gift someone some yummy cookies.

``[p]cookies [target]`` – Check how many cookies you have.

``[p]cookielb`` – Display the server’s cookie leaderboard.

``[p]setcookies amount <amount>`` – Set the amount of cookies members can obtain. If 0, members will get a random amount.

``[p]setcookies cooldown <seconds>`` – Set the cooldown for [p]cookie. This is in seconds! Default is 86400 seconds (24 hours).

``[p]setcookies stealcooldown <seconds>`` – Set the cooldown for [p]steal. This is in seconds! Default is 43200 seconds (12 hours).

``[p]setcookies steal [on_off]`` – Toggle cookie stealing for current server. If on_off is not provided, the state will be flipped.

``[p]setcookies set <target> <amount>`` – Set someone’s amount of cookies.

``[p]setcookies add <target> <amount>`` – Add cookies to someone.

``[p]setcookies take <target> <amount>`` – Take cookies away from someone.

``[p]setcookies reset`` – Delete all cookies from all members.

``[p]setcookies role add <role> <amount>`` – Set cookie reward for a role.

``[p]setcookies role del <role>`` – Delete cookie rewards for a role.

``[p]setcookies role show <role>`` – Show how many cookies a role gives.

``[p]nostore`` – Cookie store.