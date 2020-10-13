import random
import discord

from discord.utils import get

from redbot.core import Config, checks, commands


class Pick(commands.Cog):
    """Pick a random user or a user with a specified role. For the latter, use `[p]pickrole <role>` first.
    **Output is a user ID.**
    I suggest using it along with [nestedcommands](https://github.com/tmercswims/tmerc-cogs) and [scheduler](https://github.com/mikeshardmind/SinbadCogs)."""

    __author__ = "saurichable"
    __version__ = "1.1.1"

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
        """Pick a random user. **Output is a user ID.**
        
        I suggest using [nestedcommands by tmerc](https://github.com/tmercswims/tmerc-cogs) (Example of usage `[p]say Congratulations <@$(pick)>! You won!`)"""
        winner = random.choice(ctx.guild.members)
        await ctx.send(f"{winner.id}")

    # ROLES SETUP:
    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def pickrole(self, ctx, role: discord.Role):
        """Set a role winners should have."""
        await self.config.guild(ctx.guild).role.set(role.id)
        await ctx.send(f"Role has been set to {role.name}.")

    @commands.command()
    @commands.guild_only()
    @checks.mod_or_permissions(manage_roles=True)
    async def rpick(self, ctx: commands.Context):
        """Pick a random user with specified role. **Output is a user ID.**
        
        I suggest using [nestedcommands by tmerc](https://github.com/tmercswims/tmerc-cogs) (Example of usage `[p]say Congratulations <@$(rpick)>! You won!`)"""
        role = get(ctx.guild.roles, id=await self.config.guild(ctx.guild).role())
        if len(role.members) == 0:
            await ctx.send("No members to choose from.")
        else:
            winner = random.choice(role.members)
            await ctx.send(f"{winner.id}")
