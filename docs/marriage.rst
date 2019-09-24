===============
Marriage
===============

Marriage cog with some extra shit.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Simply start by 

.. code-block:: none

    [p]marriage toggle

That’s all you need, the rest is optional.

------------
List of commands
------------

``[p]marriage toggle [on_off]`` - Toggle Marriage for current server. If `on_off` is not provided, the state will be flipped.

``[p]marriage currency <currency>`` - Set the currency that should be used. 0 for Red's economy, 1 for SauriCogs' cookies.

``[p]marriage multiple <state>`` - Enable/disable whether members can be married to multiple people at once.

``[p]marriage marprice <price>`` - Set the price for getting married. With each past marriage, the cost of getting married is 50% more.

``[p]marriage divprice <multiplier>`` - Set the MULTIPLIER for getting divorced. This is a multiplier, not the price! Default is 2.

``[p]marriage changetemper <action> <temper>`` - Set the action's/gift's temper. Temper has to be in range 1 to 100. 
Negative actions (f.e. flirting with someone other than one's spouse) should have negative temper.
!!! Remember that starting point for everyone is 100 == happy and satisfied, 0 == leave their spouse

``[p]marriage changeprice <action> <temper>`` - Set the action's/gift's price.

``[p]addabout <about>`` - Add your about text. Maximum is 1000 characters.

``[p]about [member]`` - Display someone's about. If member is not specified, it shows yours.

``[p]exes [member]`` - Display someone's exes. If member is not specified, it shows yours.

``[p]crush [member]`` - Tell us who you have a crush on. If member is not specified, it deletes the current one.

``[p]marry <spouse>`` - Marry the love of your life! Pre-defined cost is multiplied by the amount of past marriages, comparing both participants and taking the higher amount.

``[p]divorce <spouse> [court]`` - Divorce your current spouse. Asks for their approval, if they say no, you go to the court. You can also force court. 
Without court, cost is multiplied same as [p]marry as well as by a pre-defined multiplier. By going to a court, you both lose a random percentage of your money.

``[p]perform <action> <target> [item]`` - Do something with someone. Available actions are flirt, fuck, dinner, date, and gift. 
If you choose gift, available gifts are flower, sweets, alcohol, loveletter, food, makeup, car, yacht, and house.
Note that if these are performed on someone but your spouse(s), your spouse(s) lose certain amount of temper. Once temper is 0, your spouse(s) leave you and take all your money.