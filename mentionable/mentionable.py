import discord

from discord.utils import get

from redbot.core import checks, commands

from redbot.core.bot import Red
from typing import Any

Cog: Any = getattr(commands, "Cog", object)


class Mentionable(Cog):
    """
    Makes unmentionable roles mentionable.
    """

    __author__ = "saurichable"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def mention(self, ctx: commands.Context, role: discord.Role):
        """Makes that role mentionable"""
        if not role.mentionable:
            await role.edit(mentionable=True)
            await ctx.send("{} is now mentionable.".format(role))
        else:
            await ctx.send("{} is already mentionable.".format(role))

    @checks.admin_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def unmention(self, ctx: commands.Context, role: discord.Role):
        """
       Makes that role unmentionable
       """
        if not role.mentionable:
            await ctx.send("{} is already unmentionable.".format(role))
        else:
            await role.edit(mentionable=False)
            await ctx.send("{} is now unmentionable.".format(role))
