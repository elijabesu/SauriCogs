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
    async def pick(self, ctx: commands.Context, embed: typing.Optional[bool]=True, *, role: typing.Optional[discord.Role]):
        """Pick a random user. *Output is a user ID.*

        I suggest using [nestedcommands by tmerc](https://github.com/tmercswims/tmerc-cogs)
        Example of usage `[p]say Congratulations <@$(pick)>! You won!`"""
        if not role or not role.members:
            role = ctx.guild.default_role
            winner = random.choice(ctx.guild.members)
        else:
            role = role
            winner = random.choice(role.members)
        if embed:
            embed: discord.Embed = discord.Embed()
            embed.title = name=f"{winner}"
            embed.description = f"Mention: {winner.mention} - Id: {winner.id}"
            embed.color = 0xffd700
            embed.set_thumbnail(url=winner.avatar_url)
            embed.add_field(
                name="Chosen among the members of the role:",
                value=f"{role.mention} ({role.id})")
            embed.set_author(name=winner, icon_url=winner.avatar_url)
            embed.set_footer(text="Chosen by the cog Pick.", icon_url="https://static.vecteezy.com/ti/vecteur-libre/p1/2477187-icone-de-decoration-etoile-doree-gratuit-vectoriel.jpg")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{winner.id}")
