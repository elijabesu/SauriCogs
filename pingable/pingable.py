import asyncio
import discord

from redbot.core import Config, checks, commands

from redbot.core.bot import Red


class Pingable(commands.Cog):
    """
    Make unpingable roles pingable by regular users with commands.
    """

    __author__ = "saurichable"
    __version__ = "1.1.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=145645641644623, force_registration=True
        )

        self.config.register_role(pingable=False, channel=None)

    @commands.max_concurrency(1, commands.BucketType.guild, True)
    @commands.group(autohelp=True)
    @checks.admin_or_permissions(manage_roles=True)
    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    async def pingableset(self, ctx: commands.Context):
        """Various Pingable settings."""
        pass

    @pingableset.command(name="ping")
    async def pingableset_ping(self, ctx: commands.Context, *, role: discord.Role):
        """Make a role pingable."""
        await self.config.role(role).pingable.set(True)
        await self.config.role(role).channel.set(None)
        await ctx.send(f"{role.name} set as pingable.")

    @pingableset.command(name="unping")
    async def pingableset_unping(self, ctx: commands.Context, *, role: discord.Role):
        """Make a role unpingable."""
        await self.config.role(role).pingable.set(False)
        await self.config.role(role).channel.set(None)
        await ctx.send(f"{role.name} removed from the pingable roles.")

    @pingableset.command(name="pingin")
    async def pingableset_pingin(self, ctx: commands.Context, role: discord.Role, channel: discord.TextChannel):
        """Make a role pinable in a specified channel only."""
        await self.config.role(role).pingable.set(True)
        await self.config.role(role).channel.set(channel.id)
        await ctx.send(f"{role.name} set as pingable only in {channel.mention}.")

    @pingableset.command(name="settings")
    async def pingableset_settings(self, ctx: commands.Context):
        roles_nochannel = ""
        roles_channel = ""

        for role in ctx.guild.roles:
            if await self.config.role(role).pingable():
                channel = ctx.guild.get_channel(await self.config.role(role).channel())
                if not channel:
                    roles_nochannel += role.name + "\n"
                else:
                    roles_channel += role.name + "(" + channel.mention + ")\n"

        embed = discord.Embed(colour=await ctx.embed_colour(), timestamp=datetime.now())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Pingable settings:__**"
        embed.set_footer(text="*required to function properly")

        embed.add_field(name="Pingable roles everywhere:", value=roles_nochannel.strip())
        embed.add_field(name="Pingable roles with specified channel:", value=roles_channel.strip())

        await ctx.send(embed)

    @commands.cooldown(1, 1800, commands.BucketType.member)
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
        await ctx.message.delete()
        await role.edit(mentionable=True)
        await ctx.send(f"{role.mention}\n{ctx.author.mention}: {message}")
        await role.edit(mentionable=False)
