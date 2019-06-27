===============
CookieStore
===============

Store add-on for SauriCogs’ Cookies cog.

.. warning:: You need `SauriCogs' Cookies cog <https://github.com/elijabesu/SauriCogs>`__ installed, loaded and working.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Simply start by 

.. code-block:: none

    [p]store toggle

and then 

.. code-block:: none

    [p]store add

That’s all you need, the rest is optional.

~~~~~~~~~~~~~~
Changing an item
~~~~~~~~~~~~~~

You can change anything about any item in the store.

Removing::

    [p]store remove <item>

Showing information::

    [p]store show <item>

Changing the price::

    [p]store price <price> <item>

Changing the quantity::

    [p]store quantity <quantity> <item>

Changing the redeemability::

    [p]store redeemable <redeemable> <item>

------------
Usage
------------

Members can use their collected cookies to buy various things, such as roles, game keys,
etc. by running 

.. code-block:: none

    [p]buy [item]

If `[item]` is not provided or non-existent, it will act as ``[p]shop``.

.. note:: Members can only have **one** of one item.

To check the inventory, simply run 

.. code-block:: none

    [p]inventory

If the bought item is redeemable, they can then redeem it by running

.. code-block:: none

    [p]redeem <item>

If the bought item is returnable while also not redeemable or not redeemed (if redeemable),
they can then return it by running

.. code-block:: none

    [p]return <item>

which will give them back half of the original price.

They can also simply remove it without getting any cookies back by running

.. code-block:: none

    [p]rminventory <item>

------------
List of commands
------------

``[p]store toggle [on_off]`` – Toggle store for current server. If on_off is not provided, the state will be flipped.

``[p]store add`` – Add a buyable item/role/game key.

``[p]store remove <item>`` – Remove a buyable item/role/game key.

``[p]store show <item>`` – Show information about a buyable item/role/game key.

``[p]store price <price> <item>`` – Change the price of an existing buyable item.

``[p]store quantity <quantity> <item>`` – Change the quantity of an existing buyable item.

``[p]store redeemable <redeemable> <item>`` – Change the redeemable of an existing buyable item.

``[p]store reset`` – Delete all items from the store.

``[p]store ping [who]`` – Set the role/member that should be pinged when a member wants to redeem their item. If who isn’t provided, it will show the current ping set.

``[p]store resetinventories`` – Delete all items from all members’ inventories.

``[p]shop`` – Display the cookie store.

``[p]buy [item]`` – Buy an item from the cookie store. If item isn’t provided, it will show the store.

``[p]return <item>`` – Return an item, you will only get 50% of the price.

``[p]inventory`` – See all items you own.

``[p]rminventory <item>`` – Remove an item from your inventory.

``[p]redeem <item>`` – Redeem an item from your inventory.