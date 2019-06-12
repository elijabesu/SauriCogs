import asyncio
import random
import discord

from typing import Any
from discord.utils import get

from redbot.core import Config, checks, bank, commands
from redbot.core.utils.predicates import MessagePredicate

from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class EconomyRaffle(Cog):
    """
    Simple economy raffle cog.
    **Use `[p]economysetup` first.**
    **This cog is meant to be used with [scheduler](https://github.com/mikeshardmind/SinbadCogs)!**
    """

    __author__ = "saurichable"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=5865146516515491, force_registration=True
        )
        default_guild = {"required": None, "amount": 0, "msg": 0, "custom": None}

        self.config.register_guild(**default_guild)

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    async def economysetup(self, ctx: commands.Context):
        """ Go through the initial setup process. """
        bot = self.bot
        guild = ctx.guild
        author = ctx.author
        channel = ctx.channel
        currency = await bank.get_currency_name(guild)
        pred = MessagePredicate.yes_or_no(ctx)
        await ctx.send("Do you want the winner to have a specific role? (yes/no)")
        try:
            await bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Try again, please.")
            return
        if pred.result is True:
            await ctx.send("What role should it be?")
            role = MessagePredicate.valid_role(ctx)
            try:
                await bot.wait_for("message", timeout=30, check=role)
            except asyncio.TimeoutError:
                await ctx.send("You took too long. Try again, please.")
                return
            required = role.result
            await self.config.guild(guild).required.set(str(required))

        await ctx.send(
            "What amount of {0} do you want me to give away? (whole number)".format(
                currency
            )
        )
        predi = MessagePredicate.valid_int(ctx)
        try:
            await bot.wait_for("message", timeout=30, check=predi)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Try again, please.")
            return
        amount = predi.result
        await self.config.guild(guild).amount.set(amount)

        await ctx.send(
            "I will send a few options of the raffle message. Please, choose number of the one you like the most."
            "```cs\nWrite '1' for this:```It's time for our {amount} giveaway!\nCongratulations {winner}! :tada: You just won {amount} {currency_name}!"
            "```cs\nWrite '2' for this:```Congratulations {winner}! :tada: You just won {amount} {currency_name}!"
            "```cs\nWrite '3' for this:```{winner} just won {amount} {currency_name}! :tada:"
            "```cs\nWrite '4' for a custom message.```"
        )
        msg_list = ["1", "2", "3", "4"]
        predic = MessagePredicate.contained_in(msg_list, ctx)
        try:
            await bot.wait_for("message", timeout=30, check=predic)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Try again, please.")
            return
        msg = msg_list[predic.result]
        await self.config.guild(guild).msg.set(int(msg))
        if int(msg) == 4:
            await ctx.send(
                "What's your message? Available parametres are: `{winner}`, `{amount}`, `{currency}`, `{server}`"
            )

            def check(m):
                return m.author == author and m.channel == channel

            try:
                answer = await bot.wait_for("message", timeout=120, check=check)
            except asyncio.TimeoutError:
                await ctx.send("You took too long. Try again, please.")
                return
            custom = answer.content
            await self.config.guild(guild).custom.set(custom)

        await ctx.send(
            """You have finished the setup! Command `{0}economyraffle` is ready to be used. *Please note that scheduler isn't part of this cog.*""".format(
                ctx.clean_prefix
            )
        )

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    async def economyraffle(self, ctx: commands.Context):
        """ Give a a pre-set amount of economy to a random user in the guild/role."""
        guild = ctx.guild
        currency = await bank.get_currency_name(guild)
        name_required = await self.config.guild(guild).required()
        required = get(guild.roles, name=name_required)
        amount = await self.config.guild(guild).amount()
        which = await self.config.guild(guild).msg()

        if required is None:
            winner = random.choice(guild.members)
        else:
            winner = random.choice(required.members)

        if which == 1:
            msg = "It's time for our {0} giveaway!\n\nCongratulations {1}! :tada: You just won extra {2} {0}!".format(
                currency, winner.mention, amount
            )
        elif which == 2:
            msg = "Congratulations {0}! :tada: You just won extra {1} {2}!".format(
                winner.mention, amount, currency
            )
        elif which == 3:
            msg = "{0}! :tada: You just won extra {1} {2}!".format(
                winner.mention, amount, currency
            )
        elif which == 4:
            custom = await self.config.guild(guild).custom()
            msg = custom.format(
                server=ctx.guild.name,
                winner=winner.mention,
                amount=amount,
                currency=currency,
            )
        else:
            await ctx.send("Uh oh. Looks like your Admins haven't setup this yet.")
            return

        await bank.deposit_credits(winner, amount)

        await ctx.send(msg)
