import asyncio
import discord

from discord.utils import get
from datetime import datetime

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.chat_formatting import humanize_list

from redbot.core.bot import Red


class AdvancedLock(commands.Cog):
    """
    Lock `@everyone` from sending messages.
    Use `[p]setlock setup` first.
    """

    __author__ = "saurichable"
    __version__ = "1.1.2"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=56546565165465, force_registration=True
        )

        default_guild = {
            "moderator": None,
            "everyone": True,
            "special": False,
            "roles": None,
            "defa": False,
            "def_roles": None,
            "channels": {},
            "ignore": [],
            "toggle": False,
            "has_been_set": False,
        }

        self.config.register_guild(**default_guild)

    @commands.group(autohelp=True)
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def setlock(self, ctx):
        """Various Lock settings."""
        pass

    @commands.guild_only()
    @setlock.command(name="toggle")
    async def setlock_toggle(self, ctx: commands.Context, on_off: bool = None):
        """Toggle Lock for current server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = on_off or not (await self.config.guild(ctx.guild).toggle())
        await self.config.guild(ctx.guild).toggle.set(target_state)
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if target_state:
            if not has_been_set:
                return await ctx.send(
                    f"Lock is now enabled but remember to do `{ctx.clean_prefix}setlock setup`"
                )
            return await ctx.send("Lock is now enabled.")
        await ctx.send("Lock is now disabled.")

    @commands.guild_only()
    @setlock.command(name="setup")
    async def setlock_setup(self, ctx: commands.Context):
        """ Go through the initial setup process. """
        await ctx.send("Do you use roles to access channels? (yes/no)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        if not pred.result:  # if no, everyone can see channels
            await self.config.guild(ctx.guild).everyone.set(True)
            await self.config.guild(ctx.guild).special.clear()
            await self.config.guild(ctx.guild).roles.clear()
            await self.config.guild(ctx.guild).defa.clear()
            await self.config.guild(ctx.guild).def_roles.clear()
            await self.config.guild(ctx.guild).channels.clear_raw()
        else:  # if yes, only some roles can see channels
            await self.config.guild(ctx.guild).everyone.set(False)
            await ctx.send(
                "Do you have different channels that different roles can access? (yes/no)"
            )
            try:
                await self.bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            if not pred.result:  # if not, all special roles can see same channels
                await self.config.guild(ctx.guild).special.set(False)
                arole_list = []
                await ctx.send(
                    "You answered no but you answered yes to `Do you use roles to access channels?`\nWhat roles can access your channels? (Must be **comma separated**)"
                )

                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel

                try:
                    answer = await self.bot.wait_for(
                        "message", timeout=120, check=check
                    )
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                arole_list = await self._get_roles_from_content(ctx, answer.content)
                if not arole_list:
                    return await ctx.send("Invalid answer, canceling.")
                await self.config.guild(ctx.guild).roles.set(arole_list)
            else:  # if yes, some roles can see some channels, some other roles can see some other channels
                await self.config.guild(ctx.guild).special.set(True)
                await self.config.guild(ctx.guild).roles.clear()
                await ctx.send(
                    f"**Use `{ctx.clean_prefix}setlock add` to add a channel.**"
                )
                await ctx.send(
                    "Would you like to add default value for when a channel isn't specified? (yes/no)"
                )
                try:
                    await self.bot.wait_for("message", timeout=30, check=pred)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                if not pred.result:  # if no, it will give an error
                    await ctx.send(
                        f"Okay, `{ctx.clean_prefix}lock` will give an error and will not lock a channel if the channel hasn't been added."
                    )
                    await self.config.guild(ctx.guild).defa.set(False)
                    await self.config.guild(ctx.guild).def_roles.clear()
                else:  # if yes, lock will do default perms
                    await self.config.guild(ctx.guild).defa.set(True)
                    drole_list = []
                    await ctx.send(
                        "What are the default roles that can access your channels? (Must be **comma separated**)"
                    )

                    def check(m):
                        return m.author == ctx.author and m.channel == ctx.channel

                    try:
                        answer = await self.bot.wait_for(
                            "message", timeout=120, check=check
                        )
                    except asyncio.TimeoutError:
                        return await ctx.send("You took too long. Try again, please.")
                    drole_list = await self._get_roles_from_content(ctx, answer.content)
                    if not drole_list:
                        return await ctx.send("Invalid answer, canceling.")
                    await self.config.guild(ctx.guild).def_roles.set(drole_list)
        await ctx.send("What is your Moderator role?")
        role = MessagePredicate.valid_role(ctx)
        try:
            await self.bot.wait_for("message", timeout=30, check=role)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        mod_role = role.result
        await self.config.guild(ctx.guild).moderator.set(mod_role.id)
        await self.config.guild(ctx.guild).has_been_set.set(True)

        await ctx.send("You have finished the setup!")

    @commands.guild_only()
    @setlock.command(name="add")
    async def setlock_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Add channels with special permissions. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        special = await self.config.guild(ctx.guild).special()
        if not special:
            return await ctx.send("Your initial setup is incorrect.")
        arole_list = []
        await ctx.send(
            "What roles can access this channel? (Must be **comma separated**)"
        )

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            answer = await self.bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        arole_list = await self._get_roles_from_content(ctx, answer.content)
        if not arole_list:
            return await ctx.send("Invalid answer, canceling.")
        await self.config.guild(ctx.guild).channels.set_raw(
            channel.id, value={"roles": arole_list}
        )
        await ctx.send(f"{channel.mention}'s permissions set.")

    @commands.guild_only()
    @setlock.command(name="remove")
    async def setlock_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Remove channels with special permissions. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        special = await self.config.guild(ctx.guild).special()
        if not special:
            return await ctx.send("Your initial setup is incorrect.")
        is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
            channel.id
        )
        if not is_already_channel:
            return await ctx.send("That channel has no extra permissions already.")
        if is_already_channel:
            await self.config.guild(ctx.guild).channels.clear_raw(channel.id)
            await ctx.send(f"{channel.mention}'s permissions removed.")

    @commands.guild_only()
    @setlock.command(name="ignore")
    async def setlock_ignore(
        self, ctx: commands.Context, new_channel: discord.TextChannel
    ):
        """ Ignore a channel during server lock. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
            new_channel.id
        )
        if not is_already_channel:
            if new_channel.id not in await self.config.guild(ctx.guild).ignore():
                async with self.config.guild(ctx.guild).ignore() as ignore:
                    ignore.append(new_channel.id)
                return await ctx.send(
                    f"{new_channel.mention} has been added into the ignored channels list."
                )
            return await ctx.send(
                f"{new_channel.mention} is already in the ignored channels list."
            )
        if is_already_channel:
            await ctx.send(
                f"{new_channel.mention} has been previously added into the active list, remove it first with `{ctx.clean_prefix}setlock remove {new_channel.mention}`."
            )

    @commands.guild_only()
    @setlock.command(name="unignore")
    async def setlock_unignore(
        self, ctx: commands.Context, new_channel: discord.TextChannel
    ):
        """ Remove channels from the ignored list. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
            new_channel.id
        )
        if not is_already_channel:
            is_ignored = await self.config.guild(ctx.guild).ignore(new_channel.id)
            if not is_ignored:
                return await ctx.send(
                    f"{new_channel.mention} already isn't in the ignored channels list."
                )
            if is_ignored:
                async with self.config.guild(ctx.guild).ignore() as ignore:
                    ignore.remove(new_channel.id)
                return await ctx.send(
                    f"{new_channel.mention} has been removed from the ignored channels list."
                )
        if is_already_channel:
            await ctx.send(
                f"{new_channel.mention} has been previously added into the active list, remove it first with `{ctx.clean_prefix}setlock remove {new_channel.mention}`."
            )

    @commands.guild_only()
    @setlock.command(name="settings")
    async def setlock_settings(self, ctx: commands.Context):
        """ List all channels' settings. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        data = await self.config.guild(ctx.guild).all()

        toggle = data["toggle"]
        if not toggle:
            toggle = False
        if not toggle:
            return await ctx.send("Lock is disabled.")
        mod = get(ctx.guild.roles, id=data["moderator"]).name
        if not mod:
            mod = None
        everyone = data["everyone"]

        special = data["special"]
        spec = "True" if not special else "False"
        ro_list = []
        try:
            for role_id in data["roles"]:
                ro = get(ctx.guild.roles, id=role_id).name
                ro_list.append(ro)
            ro_desc = humanize_list(ro_list)
        except TypeError:
            ro_desc = "Not specified"
        except AttributeError:
            ro_desc = "Something went wrong."
        if ro_list == []:
            ro_desc = "Not specified"
        def_list = []
        try:
            for def_role_id in data["def_roles"]:
                def_ro = get(ctx.guild.roles, id=def_role_id).name
                def_list.append(def_ro)
            def_desc = humanize_list(def_list)
        except TypeError:
            def_desc = "Not specified"
        except AttributeError:
            def_desc = "Something went wrong."
        if def_list == []:
            def_desc = "Not specified"
        ig_list = []
        try:
            for ignore_id in data["ignore"]:
                ig = get(ctx.guild.text_channels, id=ignore_id).name
                ig_list.append(ig)
            ig_desc = humanize_list(ig_list)
        except TypeError:
            ig_desc = "Not specified"
        except AttributeError:
            ig_desc = f"Something went wrong. `{ctx.clean_prefix}setlock refresh` might fix it"
        if ig_list == []:
            ig_desc = "Not specified"
        c_list = []
        try:
            config_channels = await self.config.guild(ctx.guild).channels.get_raw()
            for c_id in config_channels:
                c = get(ctx.guild.text_channels, id=int(c_id)).name
                c_list.append(c)
            c_desc = humanize_list(c_list)
        except TypeError:
            c_desc = "Not specified"
        except AttributeError:
            c_desc = f"Something went wrong. `{ctx.clean_prefix}setlock refresh` might fix it"
        if c_list == []:
            c_desc = "Not specified"
        embed = discord.Embed(colour=await ctx.embed_colour(), timestamp=datetime.now())
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Advanced Lock settings:__**"
        embed.add_field(name="Enabled:", value=toggle)
        embed.add_field(name="Moderator role:", value=mod)
        embed.add_field(
            name="Can everyone see all channels?", value=everyone, inline=False
        )
        embed.add_field(name="Ignored channels:", value=ig_desc, inline=False)
        if not everyone:
            embed.add_field(
                name="Can all roles see the same channels?", value=spec, inline=False
            )
            if not special:
                embed.add_field(
                    name="What roles can see all channels?", value=ro_desc, inline=False
                )
            else:
                embed.add_field(
                    name="Default permissions:", value=def_desc, inline=False
                )
            embed.add_field(
                name=(
                    f"Channels with special settings (to see the settings, type `{ctx.clean_prefix}setlock channel <channel>`):"
                ),
                value=c_desc,
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.guild_only()
    @setlock.command(name="channel")
    async def setlock_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """ List channel's settings. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
            channel.id
        )
        if not is_already_channel:
            return await ctx.send("That channel has no extra permissions.")
        if is_already_channel:
            c = await self.config.guild(ctx.guild).channels.get_raw(channel.id)
            ro_list = []
            try:
                for role_id in c["roles"]:
                    ro = get(ctx.guild.roles, id=role_id).name
                    ro_list.append(ro)
                ro_desc = (
                    f"The following roles may access {channel.mention}: "
                    + humanize_list(ro_list)
                )
            except Exception:
                ro_desc = "Not specified"
            await ctx.send(ro_desc)

    @commands.guild_only()
    @setlock.command(name="refresh")
    async def setlock_refresh(self, ctx: commands.Context):
        """ Refresh settings (deleted channels will be removed from ignored and special channel lists). """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        async with ctx.typing():
            for ignore_id in await self.config.guild(ctx.guild).ignore():
                ig = get(ctx.guild.text_channels, id=ignore_id)
                if not ig:
                    async with self.config.guild(ctx.guild).ignore() as ignore:
                        ignore.remove(ignore_id)
            for c_id in await self.config.guild(ctx.guild).channels.get_raw():
                c = get(ctx.guild.text_channels, id=int(c_id))
                if not c:
                    await self.config.guild(ctx.guild).channels.clear_raw(c_id)
        await ctx.send("Done.")

    @commands.guild_only()
    @setlock.command(name="reset")
    async def setlock_reset(self, ctx: commands.Context, confirmation: bool = False):
        """ Reset all settings to default values. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        if not confirmation:
            return await ctx.send(
                "This will delete **all** settings. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}setlock reset yes`."
            )
        await self.config.guild(ctx.guild).moderator.set(None)
        await self.config.guild(ctx.guild).everyone.set(True)
        await self.config.guild(ctx.guild).special.set(False)
        await self.config.guild(ctx.guild).roles.set(None)
        await self.config.guild(ctx.guild).defa.set(False)
        await self.config.guild(ctx.guild).def_roles.set(None)
        await self.config.guild(ctx.guild).ignore.set([])
        await self.config.guild(ctx.guild).toggle.set(False)
        await self.config.guild(ctx.guild).has_been_set.set(False)

        for channel in await self.config.guild(ctx.guild).channels.get_raw():
            await self.config.guild(ctx.guild).channels.clear_raw(channel)
        await ctx.send(
            f"All settings have been set to default values. Run `{ctx.clean_prefix}setlock setup` to set them again!"
        )

    @commands.guild_only()
    @setlock.command(name="all")
    async def setlock_all(self, ctx: commands.Context):
        """Check if all channels are set."""
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        defa = await self.config.guild(ctx.guild).defa()
        if defa:
            return await ctx.send("You don't need to know this though.")
        ignore = await self.config.guild(ctx.guild).ignore()
        config_channels = await self.config.guild(ctx.guild).channels.get_raw()
        check_channels = [int(c_id) for c_id in config_channels]
        for ig_id in ignore:
            check_channels.append(ig_id)
        if any(
            channel.id not in check_channels for channel in ctx.guild.text_channels
        ):
            missing_list = [
                channel.mention
                for channel in ctx.guild.text_channels
                if channel.id not in check_channels
            ]

            missing = humanize_list(missing_list)
            await ctx.send(f"These channels are not set nor ignored:\n{missing}")
        else:
            await ctx.send("All channels are set or ignored!")

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context, seconds=0):
        """Lock `@everyone` from sending messages.

        Optionally, you can set how many seconds the channel should stay locked for."""
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if not toggle:
                return await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if not mods:
                return await ctx.send(
                    "Uh oh. Looks like your Admins haven't setup this yet."
                )
            if ctx.channel.id in ignore:
                return await ctx.send("Uh oh. This channel is in the ignored list.")
            if which:  # if everyone can see the channels
                await ctx.channel.set_permissions(
                    everyone, read_messages=True, send_messages=False
                )
            else:
                await ctx.channel.set_permissions(
                    everyone, read_messages=False, send_messages=False
                )
                if special:  # if True, some roles can see some channels
                    c_ctx = ctx.channel.id
                    c = await self.config.guild(ctx.guild).channels.get_raw(c_ctx)
                    if c:
                        for role_id in c["roles"]:
                            ro = get(ctx.guild.roles, id=role_id)
                            await ctx.channel.set_permissions(
                                ro, read_messages=True, send_messages=False
                            )
                    else:
                        if not defa:
                            return await ctx.send(
                                "Uh oh. This channel has no settings. Ask your Admins to add it."
                            )
                        def_roles = await self.config.guild(ctx.guild).def_roles()
                        for def_role_id in def_roles:
                            def_ro = get(ctx.guild.roles, id=def_role_id)
                            await ctx.channel.set_permissions(
                                def_ro, read_messages=True, send_messages=False
                            )
                else:  # if False, all special roles can see same channels
                    roles = await self.config.guild(ctx.guild).roles()
                    for role_id in roles:
                        ro = get(ctx.guild.roles, id=role_id)
                        await ctx.channel.set_permissiouuuns(
                            ro, read_messages=True, send_messages=False
                        )
            await ctx.channel.set_permissions(
                mods, read_messages=True, send_messages=True
            )
        if seconds == 0:
            return await ctx.send(":lock: Channel locked. Only Moderators can type.")
        await ctx.send(
            f":lock: Channel locked for {seconds} seconds. Only Moderators can type."
        )
        await asyncio.sleep(seconds)
        await ctx.invoke(self.bot.get_command("unlock"))

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        """ Unlock the channel for `@everyone`. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if not toggle:
                return await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if not mods:
                return await ctx.send(
                    "Uh oh. Looks like your Admins haven't setup this yet."
                )
            if ctx.channel.id in ignore:
                return await ctx.send("Uh oh. This channel is in the ignored list.")
            if which:  # if everyone can see the channels
                await ctx.channel.set_permissions(
                    everyone, read_messages=True, send_messages=True
                )
            else:
                if not special:  # if False, all special roles can see same channels
                    roles = await self.config.guild(ctx.guild).roles()
                    for role_id in roles:
                        ro = get(ctx.guild.roles, id=role_id)
                        await ctx.channel.set_permissions(
                            ro, read_messages=True, send_messages=True
                        )
                else:  # if True, some roles can see some channels
                    c_ctx = ctx.channel.id
                    c = await self.config.guild(ctx.guild).channels.get_raw(c_ctx)
                    if not c:
                        if not defa:
                            return await ctx.send(
                                "Uh oh. This channel has no settings. Ask your Admins to add it."
                            )
                        def_roles = await self.config.guild(ctx.guild).def_roles()
                        for def_role_id in def_roles:
                            def_ro = get(ctx.guild.roles, id=def_role_id)
                            await ctx.channel.set_permissions(
                                def_ro, read_messages=True, send_messages=True
                            )
                    else:
                        for role_id in c["roles"]:
                            ro = get(ctx.guild.roles, id=role_id)
                            await ctx.channel.set_permissions(
                                ro, read_messages=True, send_messages=True
                            )
            await ctx.channel.set_permissions(
                mods, read_messages=True, send_messages=True
            )
        await ctx.send(":unlock: Channel unlocked.")

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def lockserver(self, ctx: commands.Context, confirmation: bool = False):
        """ Lock `@everyone` from sending messages in the entire server."""
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        if not confirmation:
            return await ctx.send(
                "This will overwrite every channel's permissions.\n"
                f"If you're sure, type `{ctx.clean_prefix}lockserver yes` (you can set an alias for this so I don't ask you every time)."
            )
        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if not toggle:
                return await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if not mods:
                return await ctx.send(
                    "Uh oh. Looks like your Admins haven't setup this yet."
                )
            for channel in ctx.guild.text_channels:
                if channel.id in ignore:
                    continue
                if which:  # if everyone can see the channels
                    await channel.set_permissions(
                        everyone, read_messages=True, send_messages=False
                    )
                else:
                    await channel.set_permissions(
                        everyone, read_messages=False, send_messages=False
                    )
                    if special:  # if True, some roles can see some channels
                        if not defa:
                            config_channels = await self.config.guild(
                                ctx.guild
                            ).channels.get_raw()
                            check_channels = [int(c_id) for c_id in config_channels]
                            for ig_id in ignore:
                                check_channels.append(ig_id)
                            if any(
                                channel.id not in check_channels
                                for channel in ctx.guild.text_channels
                            ):
                                return await ctx.send(
                                    "Uh oh. I cannot let you do this. Ask your Admins to add remaining channels."
                                )
                        c = await self.config.guild(ctx.guild).channels.get_raw(
                            channel.id
                        )
                        if c:
                            for role_id in c["roles"]:
                                ro = get(ctx.guild.roles, id=role_id)
                                await channel.set_permissions(
                                    ro, read_messages=True, send_messages=False
                                )
                        else:
                            def_roles = await self.config.guild(ctx.guild).def_roles()
                            for def_role_id in def_roles:
                                def_ro = get(ctx.guild.roles, id=def_role_id)
                                await channel.set_permissions(
                                    def_ro, read_messages=True, send_messages=False
                                )
                    else:  # if False, all special roles can see same channels
                        roles = await self.config.guild(ctx.guild).roles()
                        for role_id in roles:
                            ro = get(ctx.guild.roles, id=role_id)
                            await channel.set_permissions(
                                ro, read_messages=True, send_messages=False
                            )
                await channel.set_permissions(
                    mods, read_messages=True, send_messages=True
                )
        await ctx.send(":lock: Server locked. Only Moderators can type.")

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def unlockserver(self, ctx: commands.Context):
        """ Unlock the entire server for `@everyone` """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if not has_been_set:
            return await ctx.send(
                f"You have to do `{ctx.clean_prefix}setlock setup` first!"
            )
        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if not toggle:
                return await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if not mods:
                return await ctx.send(
                    "Uh oh. Looks like your Admins haven't setup this yet."
                )
            for channel in ctx.guild.text_channels:
                if channel.id in ignore:
                    continue
                if which:  # if everyone can see the channels
                    await channel.set_permissions(
                        everyone, read_messages=True, send_messages=True
                    )
                else:
                    if special:  # if True, some roles can see some channels
                        if not defa:
                            config_channels = await self.config.guild(
                                ctx.guild
                            ).channels.get_raw()
                            check_channels = [int(c_id) for c_id in config_channels]
                            for ig_id in ignore:
                                check_channels.append(ig_id)
                            if any(
                                channel.id not in check_channels
                                for channel in ctx.guild.text_channels
                            ):
                                return await ctx.send(
                                    "Uh oh. I cannot let you do this. Ask your Admins to add remaining channels."
                                )
                        c = await self.config.guild(ctx.guild).channels.get_raw(
                            channel.id
                        )
                        if c:
                            for role_id in c["roles"]:
                                ro = get(ctx.guild.roles, id=role_id)
                                await channel.set_permissions(
                                    ro, read_messages=True, send_messages=True
                                )
                        else:
                            def_roles = await self.config.guild(ctx.guild).def_roles()
                            for def_role_id in def_roles:
                                def_ro = get(ctx.guild.roles, id=def_role_id)
                                await channel.set_permissions(
                                    def_ro, read_messages=True, send_messages=True
                                )
                    else:  # if False, all special roles can see same channels
                        roles = await self.config.guild(ctx.guild).roles()
                        for role_id in roles:
                            ro = get(ctx.guild.roles, id=role_id)
                            await channel.set_permissions(
                                ro, read_messages=True, send_messages=True
                            )
                await channel.set_permissions(
                    mods, read_messages=True, send_messages=True
                )
        await ctx.send(":unlock: Server unlocked.")

    async def _get_roles_from_content(self, ctx, content):
        content_list = content.split(",")
        try:
            role_list = [
                discord.utils.get(ctx.guild.roles, name=role.strip(" ")).id
                for role in content_list
            ]
        except Exception:
            return None
        else:
            return role_list
