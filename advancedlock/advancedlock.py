import asyncio
import discord

from typing import Any
from discord.utils import get
from datetime import datetime

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.chat_formatting import humanize_list

from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class AdvancedLock(Cog):
    """
    Lock `@everyone` from sending messages.
    Use `[p]setlock setup` first.
    """

    __author__ = "saurichable"
    __version__ = "1.0.3"

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

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="toggle")
    async def setlock_toggle(self, ctx: commands.Context, on_off: bool = None):
        """ Toggle Lock for current server. 
        
        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off
            if on_off is not None
            else not (await self.config.guild(ctx.guild).toggle())
        )
        await self.config.guild(ctx.guild).toggle.set(target_state)
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if target_state:
            if has_been_set is False:
                await ctx.send(
                    f"Lock is now enabled but remember to do `{ctx.clean_prefix}setlock setup`"
                )
            else:
                await ctx.send("Lock is now enabled.")
        else:
            await ctx.send("Lock is now disabled.")

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="setup")
    async def setlock_setup(self, ctx: commands.Context):
        """ Go through the initial setup process. """
        bot = self.bot
        author = ctx.author
        channel = ctx.channel
        guild = ctx.guild
        await ctx.send("Do you use roles to access channels? (yes/no)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Try again, please.")
            return
        if pred.result is False:  # if no, everyone can see channels
            await self.config.guild(guild).everyone.set(True)
            await self.config.guild(guild).special.clear()
            await self.config.guild(guild).roles.clear()
            await self.config.guild(guild).defa.clear()
            await self.config.guild(guild).def_roles.clear()
            await self.config.guild(guild).channels.clear_raw()
        else:  # if yes, only some roles can see channels
            await self.config.guild(guild).everyone.set(False)
            await ctx.send(
                "Do you have different channels that different roles can access? (yes/no)"
            )
            try:
                await bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                await ctx.send("You took too long. Try again, please.")
                return
            if pred.result is False:  # if not, all special roles can see same channels
                await self.config.guild(guild).special.set(False)
                arole_list = []
                await ctx.send(
                    "You answered no but you answered yes to `Do you use roles to access channels?`\nWhat roles can access your channels? (Must be **comma separated**)"
                )

                def check(m):
                    return m.author == author and m.channel == channel

                try:
                    answer = await bot.wait_for("message", timeout=120, check=check)
                except asyncio.TimeoutError:
                    await ctx.send("You took too long. Try again, please.")
                    return
                arole_list = await self._get_roles_from_content(ctx, answer.content)
                if arole_list is None:
                    await ctx.send("Invalid answer, canceling.")
                    return
                await self.config.guild(guild).roles.set(arole_list)
            else:  # if yes, some roles can see some channels, some other roles can see some other channels
                await self.config.guild(ctx.guild).special.set(True)
                await self.config.guild(guild).roles.clear()
                await ctx.send(
                    "**Use `{0}setlock add` to add a channel.**".format(
                        ctx.clean_prefix
                    )
                )
                await ctx.send(
                    "Would you like to add default value for when a channel isn't specified? (yes/no)"
                )
                try:
                    await bot.wait_for("message", timeout=30, check=pred)
                except asyncio.TimeoutError:
                    await ctx.send("You took too long. Try again, please.")
                    return
                if pred.result is False:  # if no, it will give an error
                    await ctx.send(
                        "Okay, `{0}lock` will give an error and will not lock a channel if the channel hasn't been added.".format(
                            ctx.clean_prefix
                        )
                    )
                    await self.config.guild(guild).defa.set(False)
                    await self.config.guild(guild).def_roles.clear()
                else:  # if yes, lock will do default perms
                    await self.config.guild(guild).defa.set(True)
                    drole_list = []
                    await ctx.send(
                        "What are the default roles that can access your channels? (Must be **comma separated**)"
                    )

                    def check(m):
                        return m.author == author and m.channel == channel

                    try:
                        answer = await bot.wait_for("message", timeout=120, check=check)
                    except asyncio.TimeoutError:
                        await ctx.send("You took too long. Try again, please.")
                        return
                    drole_list = await self._get_roles_from_content(ctx, answer.content)
                    if drole_list is None:
                        await ctx.send("Invalid answer, canceling.")
                        return
                    await self.config.guild(guild).def_roles.set(drole_list)

        await ctx.send("What is your Moderator role?")
        role = MessagePredicate.valid_role(ctx)
        try:
            await bot.wait_for("message", timeout=30, check=role)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Try again, please.")
            return
        mod_role = role.result
        await self.config.guild(ctx.guild).moderator.set(mod_role.id)
        await self.config.guild(ctx.guild).has_been_set.set(True)

        await ctx.send("You have finished the setup!")

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="add")
    async def setlock_add(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Add channels with special permissions. """
        bot = self.bot
        author = ctx.author
        chan = ctx.channel
        guild = ctx.guild
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        special = await self.config.guild(ctx.guild).special()
        if special is False:
            await ctx.send("Your initial setup is incorrect.")
            return

        arole_list = []
        await ctx.send(
            "What roles can access this channel? (Must be **comma separated**)"
        )

        def check(m):
            return m.author == author and m.channel == chan

        try:
            answer = await bot.wait_for("message", timeout=120, check=check)
        except asyncio.TimeoutError:
            await ctx.send("You took too long. Try again, please.")
            return
        arole_list = await self._get_roles_from_content(ctx, answer.content)
        if arole_list is None:
            await ctx.send("Invalid answer, canceling.")
            return
        await self.config.guild(ctx.guild).channels.set_raw(
            channel.id, value={"roles": arole_list}
        )
        await ctx.send("{0}'s permissions set.".format(channel.mention))

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="remove")
    async def setlock_remove(self, ctx: commands.Context, channel: discord.TextChannel):
        """ Remove channels with special permissions. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        special = await self.config.guild(ctx.guild).special()
        if special is False:
            await ctx.send("Your initial setup is incorrect.")
            return

        try:
            is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
                channel.id
            )
            if is_already_channel:
                await self.config.guild(ctx.guild).channels.clear_raw(channel.id)
                await ctx.send("{0}'s permissions removed.".format(channel.mention))
                return
        except:
            await ctx.send("That channel has no extra permissions already.")

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="ignore")
    async def setlock_ignore(
        self, ctx: commands.Context, new_channel: discord.TextChannel
    ):
        """ Ignore a channel during server lock. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        try:
            is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
                new_channel.id
            )
            if is_already_channel:
                await ctx.send(
                    "{0} has been previously added into the active list, remove it first with `{1}setlock remove {0}`.".format(
                        new_channel.mention, ctx.clean_prefix
                    )
                )
                return
        except:
            if new_channel.id not in await self.config.guild(ctx.guild).ignore():
                async with self.config.guild(ctx.guild).ignore() as ignore:
                    ignore.append(new_channel.id)
                await ctx.send(
                    "{0} has been added into the ignored channels list.".format(
                        new_channel.mention
                    )
                )
            else:
                await ctx.send(
                    "{0} is already in the ignored channels list.".format(
                        new_channel.mention
                    )
                )
                return

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="unignore")
    async def setlock_unignore(
        self, ctx: commands.Context, new_channel: discord.TextChannel
    ):
        """ Remove channels from the ignored list. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        try:
            is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
                new_channel.id
            )
            if is_already_channel:
                await ctx.send(
                    "{0} has been previously added into the active list, remove it first with `{1}setlock remove {0}`.".format(
                        new_channel.mention, ctx.clean_prefix
                    )
                )
                return
        except:
            try:
                is_ignored = await self.config.guild(ctx.guild).ignore(new_channel.id)
                if is_ignored:
                    async with self.config.guild(ctx.guild).ignore() as ignore:
                        ignore.remove(new_channel.id)
                    await ctx.send(
                        "{0} has been removed from the ignored channels list.".format(
                            new_channel.mention
                        )
                    )
                    return
            except:
                await ctx.send(
                    "{0} already isn't in the ignored channels list.".format(
                        new_channel.mention
                    )
                )
                return

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="settings")
    async def setlock_settings(self, ctx: commands.Context):
        """ List all channels' settings. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        data = await self.config.guild(ctx.guild).all()

        try:
            toggle = data["toggle"]
        except:
            toggle = False
        if toggle is False:
            await ctx.send("Lock is disabled.")
            return

        try:
            mod = get(ctx.guild.roles, id=data["moderator"]).name
        except:
            mod = None

        everyone = data["everyone"]

        special = data["special"]
        if special is False:
            spec = "True"
        else:
            spec = "False"

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
            ig_desc = "Something went wrong. `{0}setlock refresh` might fix it".format(
                ctx.clean_prefix
            )
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
            c_desc = "Something went wrong. `{0}setlock refresh` might fix it".format(
                ctx.clean_prefix
            )
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
        if everyone is False:
            embed.add_field(
                name="Can all roles see the same channels?", value=spec, inline=False
            )
            if special is False:
                embed.add_field(
                    name="What roles can see all channels?", value=ro_desc, inline=False
                )
            else:
                embed.add_field(
                    name="Default permissions:", value=def_desc, inline=False
                )
            embed.add_field(
                name=(
                    "Channels with special settings (to see the settings, type `{0}setlock channel <channel>`):".format(
                        ctx.clean_prefix
                    )
                ),
                value=c_desc,
                inline=False,
            )
        await ctx.send(embed=embed)

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="channel")
    async def setlock_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """ List channel's settings. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        try:
            is_already_channel = await self.config.guild(ctx.guild).channels.get_raw(
                channel.id
            )
            if is_already_channel:
                c = await self.config.guild(ctx.guild).channels.get_raw(channel.id)
                ro_list = []
                try:
                    for role_id in c["roles"]:
                        ro = get(ctx.guild.roles, id=role_id).name
                        ro_list.append(ro)
                    ro_desc = f"The following roles may access {channel.mention}: " + humanize_list(ro_list)
                except:
                    ro_desc = "Not specified"
                await ctx.send(ro_desc)
                return
        except:
            await ctx.send("That channel has no extra permissions.")
            return

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="refresh")
    async def setlock_refresh(self, ctx: commands.Context):
        """ Refresh settings (deleted channels will be removed from ignored and special channel lists). """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        async with ctx.typing():
            for ignore_id in await self.config.guild(ctx.guild).ignore():
                ig = get(ctx.guild.text_channels, id=ignore_id)
                if ig is None:
                    async with self.config.guild(ctx.guild).ignore() as ignore:
                        ignore.remove(ignore_id)
            for c_id in await self.config.guild(ctx.guild).channels.get_raw():
                c = get(ctx.guild.text_channels, id=int(c_id))
                if c is None:
                    await self.config.guild(ctx.guild).channels.clear_raw(c_id)
        await ctx.send("Done.")

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="reset")
    async def setlock_reset(self, ctx: commands.Context, confirmation: bool = False):
        """ Reset all settings to default values. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        if confirmation is False:
            await ctx.send(
                "This will delete **all** settings. This action **cannot** be undone.\n"
                "If you're sure, type `{0}setlock reset yes`.".format(ctx.clean_prefix)
            )
            return
        else:
            pass

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
            "All settings have been set to default values. Run `{0}setlock setup` to set them again!".format(
                ctx.clean_prefix
            )
        )

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @setlock.command(name="all")
    async def setlock_all(self, ctx: commands.Context):
        """Check if all channels are set."""
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        defa = await self.config.guild(ctx.guild).defa()
        if defa is True:
            await ctx.send("You don't need to know this though.")
            return
        ignore = await self.config.guild(ctx.guild).ignore()
        config_channels = await self.config.guild(ctx.guild).channels.get_raw()
        check_channels = []
        for c_id in config_channels:
            check_channels.append(int(c_id))
        for ig_id in ignore:
            check_channels.append(ig_id)
        if not all(channel.id in check_channels for channel in ctx.guild.text_channels):
            missing_list = []
            for channel in ctx.guild.text_channels:
                if channel.id not in check_channels:
                    missing_list.append(channel.mention)
            missing = humanize_list(missing_list)
            await ctx.send(f"These channels are not set nor ignored:\n{missing}")
        else:
            await ctx.send("All channels are set or ignored!")

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        """ Lock `@everyone` from sending messages."""
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if toggle is False:
                await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
                return

            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if mods is None:
                await ctx.send("Uh oh. Looks like your Admins haven't setup this yet.")
                return

            if ctx.channel.id in ignore:
                await ctx.send("Uh oh. This channel is in the ignored list.")
                return

            if which is True:  # if everyone can see the channels
                await ctx.channel.set_permissions(
                    everyone, read_messages=True, send_messages=False
                )
            else:
                await ctx.channel.set_permissions(
                    everyone, read_messages=False, send_messages=False
                )
                if (
                    special is False
                ):  # if False, all special roles can see same channels
                    roles = await self.config.guild(ctx.guild).roles()
                    for role_id in roles:
                        ro = get(ctx.guild.roles, id=role_id)
                        await ctx.channel.set_permissiouuuns(
                            ro, read_messages=True, send_messages=False
                        )
                else:  # if True, some roles can see some channels
                    c_ctx = ctx.channel.id
                    try:
                        c = await self.config.guild(ctx.guild).channels.get_raw(c_ctx)
                        if c is None:
                            if defa is False:
                                await ctx.send(
                                    "Uh oh. This channel has no settings. Ask your Admins to add it."
                                )
                                return
                            else:
                                def_roles = await self.config.guild(
                                    ctx.guild
                                ).def_roles()
                                for def_role_id in def_roles:
                                    def_ro = get(ctx.guild.roles, id=def_role_id)
                                    await ctx.channel.set_permissions(
                                        def_ro, read_messages=True, send_messages=False
                                    )
                        else:
                            for role_id in c["roles"]:
                                ro = get(ctx.guild.roles, id=role_id)
                                await ctx.channel.set_permissions(
                                    ro, read_messages=True, send_messages=False
                                )
                    except:
                        if defa is False:
                            await ctx.send(
                                "Uh oh. This channel has no settings. Ask your Admins to add it."
                            )
                            return
                        else:
                            def_roles = await self.config.guild(ctx.guild).def_roles()
                            for def_role_id in def_roles:
                                def_ro = get(ctx.guild.roles, id=def_role_id)
                                await ctx.channel.set_permissions(
                                    def_ro, read_messages=True, send_messages=False
                                )
            await ctx.channel.set_permissions(
                mods, read_messages=True, send_messages=True
            )

        await ctx.send(":lock: Channel locked. Only Moderators can type.")

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        """ Unlock the channel for `@everyone`. """
        has_been_set = await self.config.guild(ctx.guild).has_been_set()
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if toggle is False:
                await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
                return

            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if mods is None:
                await ctx.send("Uh oh. Looks like your Admins haven't setup this yet.")
                return

            if ctx.channel.id in ignore:
                await ctx.send("Uh oh. This channel is in the ignored list.")
                return

            if which is True:  # if everyone can see the channels
                await ctx.channel.set_permissions(
                    everyone, read_messages=True, send_messages=True
                )
            else:
                if (
                    special is False
                ):  # if False, all special roles can see same channels
                    roles = await self.config.guild(ctx.guild).roles()
                    for role_id in roles:
                        ro = get(ctx.guild.roles, id=role_id)
                        await ctx.channel.set_permissions(
                            ro, read_messages=True, send_messages=True
                        )
                else:  # if True, some roles can see some channels
                    c_ctx = ctx.channel.id
                    try:
                        c = await self.config.guild(ctx.guild).channels.get_raw(c_ctx)
                        if c is None:
                            if defa is False:
                                await ctx.send(
                                    "Uh oh. This channel has no settings. Ask your Admins to add it."
                                )
                                return
                            else:
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
                    except:
                        if defa is False:
                            await ctx.send(
                                "Uh oh. This channel has no settings. Ask your Admins to add it."
                            )
                            return
                        else:
                            def_roles = await self.config.guild(ctx.guild).def_roles()
                            for def_role_id in def_roles:
                                def_ro = get(ctx.guild.roles, id=def_role_id)
                                await ctx.channel.set_permissions(
                                    def_ro, read_messages=True, send_messages=True
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
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        if confirmation is False:
            await ctx.send(
                "This will overwrite every channel's permissions.\n"
                "If you're sure, type `{0}lockserver yes` (you can set an alias for this so I don't ask you every time).".format(
                    ctx.clean_prefix
                )
            )
            return
        else:
            pass

        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if toggle is False:
                await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
                return

            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if mods is None:
                await ctx.send("Uh oh. Looks like your Admins haven't setup this yet.")
                return

            for channel in ctx.guild.text_channels:
                if channel.id in ignore:
                    continue
                else:
                    pass
                if which is True:  # if everyone can see the channels
                    await channel.set_permissions(
                        everyone, read_messages=True, send_messages=False
                    )
                else:
                    await channel.set_permissions(
                        everyone, read_messages=False, send_messages=False
                    )
                    if (
                        special is False
                    ):  # if False, all special roles can see same channels
                        roles = await self.config.guild(ctx.guild).roles()
                        for role_id in roles:
                            ro = get(ctx.guild.roles, id=role_id)
                            await channel.set_permissions(
                                ro, read_messages=True, send_messages=False
                            )
                    else:  # if True, some roles can see some channels
                        if defa is False:
                            config_channels = await self.config.guild(
                                ctx.guild
                            ).channels.get_raw()
                            check_channels = []
                            for c_id in config_channels:
                                check_channels.append(int(c_id))
                            for ig_id in ignore:
                                check_channels.append(ig_id)
                            if not all(
                                channel.id in check_channels
                                for channel in ctx.guild.text_channels
                            ):
                                await ctx.send(
                                    "Uh oh. I cannot let you do this. Ask your Admins to add remaining channels."
                                )
                                return
                        try:
                            c = await self.config.guild(ctx.guild).channels.get_raw(
                                channel.id
                            )
                            if c is None:
                                def_roles = await self.config.guild(
                                    ctx.guild
                                ).def_roles()
                                for def_role_id in def_roles:
                                    def_ro = get(ctx.guild.roles, id=def_role_id)
                                    await channel.set_permissions(
                                        def_ro, read_messages=True, send_messages=False
                                    )
                            else:
                                for role_id in c["roles"]:
                                    ro = get(ctx.guild.roles, id=role_id)
                                    await channel.set_permissions(
                                        ro, read_messages=True, send_messages=False
                                    )
                        except:
                            def_roles = await self.config.guild(ctx.guild).def_roles()
                            for def_role_id in def_roles:
                                def_ro = get(ctx.guild.roles, id=def_role_id)
                                await channel.set_permissions(
                                    def_ro, read_messages=True, send_messages=False
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
        if has_been_set is False:
            await ctx.send(f"You have to do `{ctx.clean_prefix}setlock setup` first!")
            return
        async with ctx.typing():
            toggle = await self.config.guild(ctx.guild).toggle()
            if toggle is False:
                await ctx.send(
                    "Uh oh. Lock isn't enabled in this server. Ask your Admins to enable it."
                )
                return

            everyone = get(ctx.guild.roles, name="@everyone")
            mods_id = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, id=mods_id)
            which = await self.config.guild(ctx.guild).everyone()
            special = await self.config.guild(ctx.guild).special()
            defa = await self.config.guild(ctx.guild).defa()
            ignore = await self.config.guild(ctx.guild).ignore()

            if mods is None:
                await ctx.send("Uh oh. Looks like your Admins haven't setup this yet.")
                return

            for channel in ctx.guild.text_channels:
                if channel.id in ignore:
                    continue
                else:
                    pass
                if which is True:  # if everyone can see the channels
                    await channel.set_permissions(
                        everyone, read_messages=True, send_messages=True
                    )
                else:
                    if (
                        special is False
                    ):  # if False, all special roles can see same channels
                        roles = await self.config.guild(ctx.guild).roles()
                        for role_id in roles:
                            ro = get(ctx.guild.roles, id=role_id)
                            await channel.set_permissions(
                                ro, read_messages=True, send_messages=True
                            )
                    else:  # if True, some roles can see some channels
                        if defa is False:
                            config_channels = await self.config.guild(
                                ctx.guild
                            ).channels.get_raw()
                            check_channels = []
                            for c_id in config_channels:
                                check_channels.append(int(c_id))
                            for ig_id in ignore:
                                check_channels.append(ig_id)
                            if not all(
                                channel.id in check_channels
                                for channel in ctx.guild.text_channels
                            ):
                                await ctx.send(
                                    "Uh oh. I cannot let you do this. Ask your Admins to add remaining channels."
                                )
                                return
                        try:
                            c = await self.config.guild(ctx.guild).channels.get_raw(
                                channel.id
                            )
                            if c is None:
                                def_roles = await self.config.guild(
                                    ctx.guild
                                ).def_roles()
                                for def_role_id in def_roles:
                                    def_ro = get(ctx.guild.roles, id=def_role_id)
                                    await channel.set_permissions(
                                        def_ro, read_messages=True, send_messages=True
                                    )
                            else:
                                for role_id in c["roles"]:
                                    ro = get(ctx.guild.roles, id=role_id)
                                    await channel.set_permissions(
                                        ro, read_messages=True, send_messages=True
                                    )
                        except:
                            def_roles = await self.config.guild(ctx.guild).def_roles()
                            for def_role_id in def_roles:
                                def_ro = get(ctx.guild.roles, id=def_role_id)
                                await channel.set_permissions(
                                    def_ro, read_messages=True, send_messages=True
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
        except:
            return None
        else:
            return role_list