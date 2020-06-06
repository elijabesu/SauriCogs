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
    __version__ = "1.0.1"

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
        currency = await bank.get_currency_name(ctx.guild)
        pred = MessagePredicate.yes_or_no(ctx)
        await ctx.send("Do you want the winner to have a specific role? (yes/no)")
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        if pred.result:
            await ctx.send("What role should it be?")
            role = MessagePredicate.valid_role(ctx)
            try:
                await self.bot.wait_for("message", timeout=30, check=role)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            required = role.result
            await self.config.guild(ctx.guild).required.set(str(required))
        await ctx.send(
            f"What amount of {currency} do you want me to give away? (whole number)"
        )
        predi = MessagePredicate.valid_int(ctx)
        try:
            await self.bot.wait_for("message", timeout=30, check=predi)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        amount = predi.result
        await self.config.guild(ctx.guild).amount.set(amount)

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
            await self.bot.wait_for("message", timeout=30, check=predic)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        msg = msg_list[predic.result]
        await self.config.guild(ctx.guild).msg.set(int(msg))
        if int(msg) == 4:
            await ctx.send(
                "What's your message? Available parametres are: `{winner}`, `{amount}`, `{currency}`, `{server}`"
            )

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                answer = await self.bot.wait_for("message", timeout=120, check=check)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            custom = answer.content
            await self.config.guild(ctx.guild).custom.set(custom)
        await ctx.send(
            f"You have finished the setup! Command `{ctx.clean_prefix}economyraffle` is ready to be used. *Please note that scheduler isn't part of this cog.*"
        )

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    async def economyraffle(self, ctx: commands.Context):
        """ Give a a pre-set amount of economy to a random user in the guild/role."""
        currency = await bank.get_currency_name(ctx.guild)
        name_required = await self.config.guild(ctx.guild).required()
        required = get(ctx.guild.roles, name=name_required)
        amount = await self.config.guild(ctx.guild).amount()
        which = await self.config.guild(ctx.guild).msg()

        if not required:
            winner = random.choice(ctx.guild.members)
        else:
            winner = random.choice(required.members)
        if which == 1:
            msg = f"It's time for our {currency} giveaway!\n\nCongratulations {winner.mention}! :tada: You just won extra {amount} {currency}!"
        elif which == 2:
            msg = f"Congratulations {winner.mention}! :tada: You just won extra {amount} {currency}!"
        elif which == 3:
            msg = f"{winner.mention}! :tada: You just won extra {amount} {currency}!"
        elif which == 4:
            custom = await self.config.guild(ctx.guild).custom()
            msg = custom.format(
                server=ctx.guild.name,
                winner=winner.mention,
                amount=amount,
                currency=currency,
            )
        else:
            return await ctx.send(
                "Uh oh. Looks like your Admins haven't setup this yet."
            )
        await bank.deposit_credits(winner, amount)
        await ctx.send(msg)
