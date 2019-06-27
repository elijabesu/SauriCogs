===============
UserLog
===============

Log when an user joins or leaves. 

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Setting up is super easy. All you need to do is run 

.. code-block:: none

    [p]userlog channel <channel>
    
where `channel` is a mention of your desired text channel.

The default value is True for both logging users joining and users leaving.
You can disable/enable either by running ``[p]userlog join`` and ``[p]userlog leave``.

.. tip:: I suggest ``[p]cog unload userlog`` when you're mass pruning/banning 
    just to be sure you do not rate limit your bot.

------------
List of commands
------------

``[p]userlog channel [channel]`` - Set the channel for logs. If the channel is not provided,
logging will be disabled.

``[p]userlog join [on_off]`` - Toggle logging when users join the current server. 
If on_off is not provided, the state will be flipped.

``[p]userlog leave [on_off]`` - Toggle logging when users leave the current server. 
If on_off is not provided, the state will be flipped.
