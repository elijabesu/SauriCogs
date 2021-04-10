import discord
import datetime
import typing

from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import humanize_list


class UniqueName(commands.Cog):
    """
    Deny members' names to be the same as your Moderators'.
    """

    __version__ = "1.4.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=58462132145646132, force_registration=True
        )

        self.config.register_guild(
            toggle=False, roles=[], name="username", channel=None
        )
        self.config.register_global(guilds=[])

    async def red_delete_data_for_user(self, *, requester, user_id):
        # nothing to delete
        return

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @commands.group(autohelp=True, aliases=["unset", "uniquename"])
    @checks.admin()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_nicknames=True)
    async def uniquenameset(self, ctx: commands.Context):
        """Various Unique Name settings."""

    @uniquenameset.command(name="role")
    async def unset_role(self, ctx: commands.Context, role: discord.Role):
        """Add a role to the protected list."""
        async with self.config.guild(ctx.guild).roles() as roles:
            roles.append(role.id)
        await ctx.tick()

    @uniquenameset.command(name="delrole")
    async def unset_delrole(self, ctx: commands.Context, role: discord.Role):
        """Remove a role from the protected list."""
        if not (await self.config.guild(ctx.guild).roles(role.id)):
            return await ctx.send(f"{role.name} isn't in the list.")
        async with self.config.guild(ctx.guild).roles() as roles:
            roles.remove(role.id)
        await ctx.tick()

    @uniquenameset.command(name="roles")
    async def unset_roles(self, ctx: commands.Context):
        """View the protected roles."""
        roles = []
        for rid in await self.config.guild(guild).roles():
            role = guild.get_role(rid)
            if role:
                roles.append(role)
        pretty_roles = humanize_list(roles)
        await ctx.send(f"List of roles that are protected:\n{pretty_roles}")

    @uniquenameset.command(name="channel")
    async def unset_channel(
        self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel]
    ):
        """Set the channel for warnings.

        If the channel is not provided, logging will be disabled."""
        if channel:
            await self.config.guild(ctx.guild).channel.set(channel.id)
        else:
            await self.config.guild(ctx.guild).channel.clear()
        await ctx.tick()

    @uniquenameset.command(name="name")
    async def unset_name(self, ctx: commands.Context, name: str):
        """Set a default name that will be set."""
        await self.config.guild(ctx.guild).name.set(name)
        await ctx.tick()

    @uniquenameset.command(name="toggle")
    async def unset_toggle(self, ctx: commands.Context, on_off: typing.Optional[bool]):
        """Toggle UniqueName for this server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = on_off or not (await self.config.guild(ctx.guild).toggle())
        await self.config.guild(ctx.guild).toggle.set(target_state)
        async with self.config.guilds() as guilds:
            guilds.append(ctx.guild.id)
        if target_state:
            await ctx.send("UniqueName is now enabled.")
        else:
            await ctx.send("UniqueName is now disabled.")

    @uniquenameset.command(name="settings")
    async def unset_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).channel())
        channel = "None" if not channel else channel.mention
        config_roles = await self.config.guild(ctx.guild).roles()
        if len(config_roles) == 0:
            roles = "None"
        else:
            roles = []
            for rid in config_roles:
                role = ctx.guild.get_role(rid)
                if role:
                    roles.append(role.name)
            roles = humanize_list(roles)

        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Unique Name settings:__**"
        embed.set_footer(text="*required to function properly")

        embed.add_field(name="Enabled*:", value=str(data["toggle"]))
        embed.add_field(name="Default name:", value=data["name"])
        embed.add_field(name="Logging channel:", value=channel)
        embed.add_field(name="Protected roles*:", value=roles, inline=False)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if not await self.config.guild(before.guild).toggle():
            return
        config_roles = await self.config.guild(before.guild).roles()
        if len(config_roles) == 0:
            return
        if len(before.roles) != 0:
            for role in before.roles:
                if role.id in config_roles:
                    return
        names = await self._build_name_list(before.guild)
        name = await self.config.guild(before.guild).name()
        channel = before.guild.get_channel(
            await self.config.guild(before.guild).channel()
        )
        if not after.nick:
            return
        if after.nick not in names:
            return
        if channel:
            warning_text = f"""**UniqueName warning:**
        
            Discovered a forbidden name: '{after.display_name}'. 
            User: {after.mention} - `{after.name}#{after.discriminator} ({after.id})`"""
            await channel.send(warning_text)
        await after.edit(nick=name, reason="UniqueName cog")

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        guilds = await self.config.guilds()
        if len(guilds) == 0:
            return
        for gid in guilds:
            guild = self.bot.get_guild(gid)
            if guild:
                member = guild.get_member(before.id)
                if not member:
                    return
                if not await self.config.guild(guild).toggle():
                    return
                config_roles = await self.config.guild(guild).roles()
                if len(config_roles) == 0:
                    return
                if len(member.roles) != 0:
                    for role in member.roles:
                        if role.id in config_roles:
                            return
                names = await self._build_name_list(guild)
                name = await self.config.guild(guild).name()
                channel = guild.get_channel(await self.config.guild(guild).channel())
                if not after.name:
                    return
                if after.name not in names:
                    return
                if channel:
                    warning_text = f"""**UniqueName warning:**
                
                    Discovered a forbidden name: '{after.name}'. 
                    User: {after.mention} - `{after.name}#{after.discriminator} ({after.id})`"""
                    await channel.send(warning_text)
                await member.edit(nick=name, reason="UniqueName cog")

    async def _build_name_list(self, guild):
        names = []
        for rid in await self.config.guild(guild).roles():
            role = guild.get_role(rid)
            if role:
                for member in role.members:
                    names.append(member.nick)
                    names.append(member.name)
        return names
