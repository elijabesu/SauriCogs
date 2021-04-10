import discord

from redbot.core import checks, commands

from redbot.core.bot import Red


class Mentionable(commands.Cog):
    """
    Very simple way to make unmentionable roles mentionable.
    """

    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot

    async def red_delete_data_for_user(self, *, requester, user_id):
        # nothing to delete
        return

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @checks.admin()
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def mention(self, ctx: commands.Context, *, role: discord.Role):
        """Makes that role mentionable"""
        if not role.mentionable:
            await role.edit(mentionable=True)
            await ctx.send(f"{role} is now mentionable.")
        else:
            await ctx.send(f"{role} is already mentionable.")

    @checks.admin()
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def unmention(self, ctx: commands.Context, *, role: discord.Role):
        """
        Makes that role unmentionable
        """
        if not role.mentionable:
            await ctx.send(f"{role} is already unmentionable.")
        else:
            await role.edit(mentionable=False)
            await ctx.send(f"{role} is now unmentionable.")
