import datetime
import discord

from typing import Any

from redbot.core import checks, commands, Config

from redbot.core.bot import Red

__author__ = "saurichable"

Cog: Any = getattr(commands, "Cog", object)


class UserLog(Cog):
    """Log when users join/leave into your specified channel."""

    __author__ = "saurichable"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=56546565165465456, force_registration=True
        )

        default_guild = {"channel": None, "join": True, "leave": True}

        self.config.register_guild(**default_guild)

    @commands.group(autohelp=True)
    @checks.admin_or_permissions(manage_guild=True)
    async def userlog(self, ctx):
        """Manage user log settings."""
        pass

    @userlog.command(name="channel")
    async def user_channel_log(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for logs.

        If the channel is not provided, logging will be disabled."""
        if channel:
            await self.config.guild(ctx.guild).channel.set(channel.id)
        else:
            await self.config.guild(ctx.guild).channel.set(None)
        await ctx.tick()

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @userlog.command(name="join")
    async def user_join_log(self, ctx: commands.Context, on_off: bool = None):
        """Toggle logging when users join the current server. 

        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off
            if on_off is not None
            else not (await self.config.guild(ctx.guild).join())
        )
        await self.config.guild(ctx.guild).join.set(target_state)
        if target_state:
            await ctx.send("Logging users joining is now enabled.")
        else:
            await ctx.send("Logging users joining is now disabled.")

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @userlog.command(name="leave")
    async def user_leave_log(self, ctx: commands.Context, on_off: bool = None):
        """Toggle logging when users leave the current server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off
            if on_off is not None
            else not (await self.config.guild(ctx.guild).leave())
        )
        await self.config.guild(ctx.guild).leave.set(target_state)
        if target_state:
            await ctx.send("Logging users leaving is now enabled.")
        else:
            await ctx.send("Logging users leaving is now disabled.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        join = await self.config.guild(guild).join()
        if join is False:
            return
        try:
            channel = guild.get_channel(await self.config.guild(guild).channel())
        except RuntimeError:
            return
        if channel is None:
            return
        time = datetime.datetime.utcnow()
        users = len(guild.members)
        since_created = (time - member.created_at).days
        user_created = member.created_at.strftime("%Y-%m-%d, %H:%M")

        created_on = "{0} ({1} days ago)".format(user_created, since_created)

        embed = discord.Embed(
            description="{0} ({1}#{2})".format(
                member.mention, member.name, member.discriminator
            ),
            colour=discord.Colour.green(),
            timestamp=member.joined_at,
        )
        embed.add_field(name="Total Users:", value=str(users))
        embed.add_field(name="Account created on:", value=created_on)
        embed.set_footer(text="User ID: {0}".format(member.id))
        embed.set_author(
            name="{0} has joined the guild".format(member.name),
            url=member.avatar_url,
            icon_url=member.avatar_url,
        )
        embed.set_thumbnail(url=member.avatar_url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild

        leave = await self.config.guild(guild).leave()
        if leave is False:
            return
        try:
            channel = guild.get_channel(await self.config.guild(guild).channel())
        except RuntimeError:
            return
        if channel is None:
            return

        time = datetime.datetime.utcnow()
        users = len(guild.members)
        embed = discord.Embed(
            description="{0} ({1}#{2})".format(
                member.mention, member.name, member.discriminator
            ),
            colour=discord.Colour.red(),
            timestamp=time,
        )
        embed.add_field(name="Total Users:", value=str(users))
        embed.set_footer(text="User ID: {0}".format(member.id))
        embed.set_author(
            name="{0} has left the guild".format(member.name),
            url=member.avatar_url,
            icon_url=member.avatar_url,
        )
        embed.set_thumbnail(url=member.avatar_url)
        await channel.send(embed=embed)
