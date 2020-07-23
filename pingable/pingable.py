import asyncio
import discord

from datetime import timedelta

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.antispam import AntiSpam

from redbot.core.bot import Red


class Pingable(commands.Cog):
    """
    Make unpingable roles pingable by regular users with commands.
    """

    __author__ = "saurichable"
    __version__ = "1.0.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=145645641644623, force_registration=True
        )

        self.config.register_role(pingable=False, channel=None)
        self.antispam = {}

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(aliases=["addpingable"])
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def setpingable(self, ctx: commands.Context, *, role: discord.Role):
        """Make a role pingable"""
        pred_yn = MessagePredicate.yes_or_no(ctx)
        pred_c = MessagePredicate.valid_text_channel(ctx)

        await self.config.role(role).pingable.set(True)
        await ctx.send("Do you want it to work only in one channel?")
        try:
            await self.bot.wait_for("message", timeout=120, check=pred_yn)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        if pred_yn.result:
            await ctx.send("What channel?")
            try:
                await self.bot.wait_for("message", timeout=120, check=pred_c)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            channel = pred_c.result
            await self.config.role(role).channel.set(channel.id)
        await ctx.send(
            f"{role.name} set as pingable. You can now set an alias for "
            f'`{ctx.clean_prefix}pingable "{role.name}"` for users to use.'
        )

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command(aliases=["delpingable"])
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def rmpingable(self, ctx: commands.Context, *, role: discord.Role):
        """Make a role unpingable"""
        bot = self.bot

        await self.config.role(role).pingable.set(False)
        await self.config.role(role).channel.set(None)
        await ctx.send(
            f"{role.name} removed from the pingable roles. Don't forget to delete the alias for "
            f'`{ctx.clean_prefix}pingable "{role.name}"`.'
        )

    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def pingable(
        self, ctx: commands.Context, role: discord.Role, *, message: str
    ):
        """Ping a role."""
        if not await self.config.role(role).pingable():
            return
        if await self.config.role(role).channel():
            if await self.config.role(role).channel() != ctx.channel.id:
                return
        if ctx.guild not in self.antispam:
            self.antispam[ctx.guild] = {}
        if ctx.author not in self.antispam[ctx.guild]:
            self.antispam[ctx.guild][ctx.author] = AntiSpam([(timedelta(hours=1), 1)])
        if self.antispam[ctx.guild][ctx.author].spammy:
            return await ctx.send("Uh oh, you're doing this way too frequently.")
        await ctx.message.delete()
        await role.edit(mentionable=True)
        await ctx.send(f"{role.mention}\n{ctx.author.mention}: {message}")
        await role.edit(mentionable=False)
        self.antispam[ctx.guild][ctx.author].stamp()
