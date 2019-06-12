import random
import discord

from typing import Any
from discord.utils import get

from redbot.core import Config, checks, commands

from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class Pick(Cog):
    """Pick a random user or a user with a specified role. For the latter, use `[p]pickrole <role>` first.
    **Output is a user ID.**
    I suggest using it along with [nestedcommands](https://github.com/tmercswims/tmerc-cogs) and [scheduler](https://github.com/mikeshardmind/SinbadCogs)."""

    __author__ = "saurichable"
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=50743950055646, force_registration=True
        )

        default_guild = {"role": None}

        self.config.register_guild(**default_guild)

    @commands.command()
    @commands.guild_only()
    @checks.mod_or_permissions(manage_roles=True)
    async def pick(self, ctx: commands.Context):
        """Pick a random user. **Output is a user ID.** I suggest using [nestedcommands by tmerc](https://github.com/tmercswims/tmerc-cogs) (Example of usage `[p]say Congratulations <@$(pick)>! You won!`)"""
        winner = random.choice(ctx.guild.members)
        await ctx.send("{}".format(winner.id))

    # ROLES SETUP:
    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def pickrole(self, ctx, role_name=None):
        """Set a role winners should have."""
        if not role_name:
            await self.config.guild(ctx.guild).role.set(None)
            return await ctx.send("Role removed.")
        await self.config.guild(ctx.guild).role.set(str(role_name))
        await ctx.send(f"Role has been set to {role_name}.")

    @commands.command()
    @commands.guild_only()
    @checks.mod_or_permissions(manage_roles=True)
    async def rpick(self, ctx: commands.Context):
        """Pick a random user with specified role. **Output is a user ID.** I suggest using [nestedcommands by tmerc](https://github.com/tmercswims/tmerc-cogs) (Example of usage `[p]say Congratulations <@$(rpick)>! You won!`)"""
        name_role = await self.config.guild(ctx.guild).role()
        role = get(ctx.guild.roles, name=name_role)
        winner = random.choice(role.members)
        await ctx.send("{}".format(winner.id))
