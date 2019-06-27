===============
Application
===============

Simple application cog with a ‘Staff Applicant’ role.

``[p]`` is your prefix, ``<>`` is a required argument, ``[]`` is an optional argument.

------------
Setting up
------------

Run 

.. code-block:: none

    [p]applysetup

The bot checks if required channels and roles are already present, if not,
it will create them. It will also ask you if you want your `applications` channel
to be visible to everyone. Once it is done, it will ask you to move the new channel
into desired category.

------------
Usage
------------

User writes ``[p]apply`` and the bot DMs them (unless they have closed DMs,
in that case, bot sends a notice about it into the current channel) ask asks
them questions. Once the questionnaire has been finished, the bot gives them a 
`Staff Applicant` role and sends an embed message with answers into appropriate channel.

.. important:: Currently it does not support custom questions.

Current questions are:

What position are you applying for?
What is your name?
How old are you?
What timezone are you in? (Google is your friend.)
How many days per week can you be active?
How many hours per day can you be active?
Do you have any previous experience? If so, please describe.
Why do you want to be a member of our staff?

~~~~~~~~~~~~~~
Accept/Deny
~~~~~~~~~~~~~~

To accept someone’s application, use

.. code-block:: none

    [p]accept <target>

where target can be a user ID, user mention or user name.
The bot then checks if the user applied (and has the `Staff Applicant` role),
if so, it then asks you what role you want to accept the user as. 

.. warning:: It only allows one role.

Once it’s done, the bot DMs the user about being accepted.

To deny someone's application, use 

.. code-block:: none

    [p]deny <target>

where target can be a user ID, user mention or user name.
The bot then checks if the user applied (and has the `Staff Applicant` role),
if so, it asks you if you’d like to specify a reason, if so, it asks for the
reason. Once it’s done, the bot DMs the user about being rejected (with a reason,
if it has been specified).

------------
List of commands
------------

``[p]apply`` – Apply to be a staff member.

``[p]applysetup`` – Go through the initial setup process.

``[p]accept <target>`` – Accept a staff applicant. can be a mention or an ID

``[p]deny <target>`` – Deny a staff applicant. can be a mention or an ID