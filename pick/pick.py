import random
import discord
import typing

from redbot.core import checks, commands


class Pick(commands.Cog):
    """Pick a random user, or a user with a specified role."""

    __version__ = "1.2.0"

    def __init__(self, bot):
        self.bot = bot

    async def red_delete_data_for_user(self, *, requester, user_id):
        # nothing to delete
        return

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @commands.command()
    @commands.guild_only()
    @checks.mod()
    async def pick(self, ctx: commands.Context, *, role: typing.Optional[discord.Role]):
        """Pick a random user. *Output is a user ID.*

        I suggest using [nestedcommands by tmerc](https://github.com/tmercswims/tmerc-cogs)
        Example of usage `[p]say Congratulations <@$(pick)>! You won!`"""
        if not role or not role.members:
            winner = random.choice(ctx.guild.members)
        else:
            winner = random.choice(role.members)
        await ctx.send(f"{winner.id}")
