import datetime
import discord
import typing

from redbot.core import checks, commands, Config

from redbot.core.bot import Red

__author__ = "saurichable"


class UserLog(commands.Cog):
    """Log when users join/leave into your specified channel."""

    __author__ = "saurichable"
    __version__ = "1.1.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=56546565165465456, force_registration=True
        )

        self.config.register_guild(channel=None, join=True, leave=True)

    @commands.group(autohelp=True, aliases=["userlog"])
    @commands.guild_only()
    @checks.admin()
    async def userlogset(self, ctx: commands.Context):
        f"""Various User Log settings.
        
        Version: {self.__version__}
        Author: {self.__author__}"""

    @userlogset.command(name="channel")
    async def user_channel_log(
        self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel]
    ):
        """Set the channel for logs.

        If the channel is not provided, logging will be disabled."""
        if channel:
            await self.config.guild(ctx.guild).channel.set(channel.id)
        else:
            await self.config.guild(ctx.guild).channel.clear()
        await ctx.tick()

    @userlogset.command(name="join")
    async def user_join_log(self, ctx: commands.Context, on_off: typing.Optional[bool]):
        """Toggle logging when users join the current server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = on_off or not (await self.config.guild(ctx.guild).join())
        await self.config.guild(ctx.guild).join.set(target_state)
        if target_state:
            await ctx.send("Logging users joining is now enabled.")
        else:
            await ctx.send("Logging users joining is now disabled.")

    @userlogset.command(name="leave")
    async def user_leave_log(self, ctx: commands.Context, on_off: typing.Optional[bool]):
        """Toggle logging when users leave the current server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = on_off or not (await self.config.guild(ctx.guild).leave())
        await self.config.guild(ctx.guild).leave.set(target_state)
        if target_state:
            await ctx.send("Logging users leaving is now enabled.")
        else:
            await ctx.send("Logging users leaving is now disabled.")

    @userlogset.command(name="settings")
    async def user_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).channel())
        channel = "None" if not channel else channel.mention
        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__User Log settings:__**"

        embed.set_footer(text="*required to function properly")
        embed.add_field(name="Channel*:", value=channel)
        embed.add_field(name="Join:", value=str(data["join"]))
        embed.add_field(name="Leave:", value=str(data["leave"]))

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        join = await self.config.guild(member.guild).join()
        if not join:
            return
        channel = member.guild.get_channel(
            await self.config.guild(member.guild).channel()
        )
        if not channel:
            return
        time = datetime.datetime.utcnow()
        users = len(member.guild.members)
        since_created = (time - member.created_at).days
        user_created = member.created_at.strftime("%Y-%m-%d, %H:%M")

        created_on = f"{user_created} ({since_created} days ago)"

        embed = discord.Embed(
            description=f"{member.mention} ({member.name}#{member.discriminator})",
            colour=discord.Colour.green(),
            timestamp=member.joined_at,
        )
        embed.add_field(name="Total Users:", value=str(users))
        embed.add_field(name="Account created on:", value=created_on)
        embed.set_footer(text=f"User ID: {member.id}")
        embed.set_author(
            name=f"{member.name} has joined the guild",
            url=member.avatar_url,
            icon_url=member.avatar_url,
        )
        embed.set_thumbnail(url=member.avatar_url)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        leave = await self.config.guild(member.guild).leave()
        if not leave:
            return
        channel = member.guild.get_channel(
            await self.config.guild(member.guild).channel()
        )
        if not channel:
            return
        time = datetime.datetime.utcnow()
        users = len(member.guild.members)
        embed = discord.Embed(
            description=f"{member.mention} ({member.name}#{member.discriminator})",
            colour=discord.Colour.red(),
            timestamp=time,
        )
        embed.add_field(name="Total Users:", value=str(users))
        embed.set_footer(text=f"User ID: {member.id}")
        embed.set_author(
            name=f"{member.name} has left the guild",
            url=member.avatar_url,
            icon_url=member.avatar_url,
        )
        embed.set_thumbnail(url=member.avatar_url)
        await channel.send(embed=embed)
