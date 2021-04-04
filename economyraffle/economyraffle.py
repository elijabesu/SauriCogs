import discord
import random
import typing
import datetime

from redbot.core import Config, checks, bank, commands

from redbot.core.bot import Red


class EconomyRaffle(commands.Cog):
    """
    Simple economy raffle cog.
    """

    __author__ = "saurichable"
    __version__ = "1.1.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=5865146516515491, force_registration=True
        )

        self.config.register_guild(
            required_role=None,
            amount=0,
            message="Congratulations {winner}! :tada: You just won {amount} {currency_name}!",
        )

    @commands.group(autohelp=True, aliases=["erset"])
    @commands.guild_only()
    @checks.admin()
    async def economyraffleset(self, ctx: commands.Context):
        f"""Various Economy Raffle settings.
        
        Version: {self.__version__}
        Author: {self.__author__}"""

    @economyraffleset.command(name="role")
    async def economyraffleset_role(self, ctx: commands.Context, *, role: typing.Optional[discord.Role]):
        """Set the required role to be in the raffle pool.

        If the role is not specified, no role is required."""
        if not role:
            await self.config.guild(ctx.guild).required_role.clear()
            return await ctx.send("No role is required.")
        await self.config.guild(ctx.guild).required_role.set(role.id)
        await ctx.send(f"{role.name} is now required to win economy.")

    @economyraffleset.command(name="amount")
    async def economyraffleset_amount(self, ctx: commands.Context, amount: int):
        """Set the amount members can win."""
        await self.config.guild(ctx.guild).amount.set(amount)
        await ctx.tick()

    @economyraffleset.command(name="settings")
    async def economyraffleset_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.guild(ctx.guild).all()
        required_role = ctx.guild.get_role(await self.config.guild(ctx.guild).required_role())
        required_role = required_role.name if required_role else "None"

        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Economy Raffle settings:__**"
        embed.set_footer(text="*required to function properly")

        embed.add_field(name="Enabled:", value=required_role)
        embed.add_field(name="Amount*:", value=str(data["amount"]))
        embed.add_field(name="Message:", value=data["message"], inline=False)

        await ctx.send(embed=embed)

    @economyraffleset.command(name="message")
    async def economyraffleset_message(self, ctx: commands.Context, *, message: str):
        """Set the raffle message.

        Available parameters are: `{winner}`, `{amount}`, `{currency_name}`, `{server}`"""
        await self.config.guild(ctx.guild).message.set(message)
        await ctx.tick()

    @checks.mod()
    @commands.command()
    @commands.guild_only()
    async def economyraffle(self, ctx: commands.Context):
        """ Give a a pre-set amount of economy to a random user in the guild/role."""
        currency_name = await bank.get_currency_name(ctx.guild)
        required_role = ctx.guild.get_role(await self.config.guild(ctx.guild).required_role())
        amount = await self.config.guild(ctx.guild).amount()
        message = await self.config.guild(ctx.guild).message()

        if not required_role:
            winner = random.choice(ctx.guild.members)
        else:
            winner = random.choice(required_role.members)
        msg = message.format(
            server=ctx.guild.name,
            winner=winner.mention,
            amount=amount,
            currency_name=currency_name,
        )
        await bank.deposit_credits(winner, amount)
        await ctx.send(msg)
