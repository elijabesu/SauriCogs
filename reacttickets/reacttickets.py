import discord
import datetime
import typing
import asyncio

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate

from redbot.core.bot import Red


class ReactTickets(commands.Cog):
    """
    Reaction based assignable support tickets with custom cases (reasons).
    """

    __version__ = "1.0.4"

    def __init__(self, bot: Red):
        self.bot = bot
        self.enabled_cache = {}

        self.config = Config.get_conf(
            self, identifier=5465324654986213156, force_registration=False
        )

        self.config.register_guild(
            enabled=None,
            request_channel=None,
            channel=None,
            open_category=None,
            closed_category=None,
            role=None,
            active_channels=[],
            active_users=[],
            active_msgs=[],
            closed=[],  # [channel_id, channel_id]
            cases={},  # {'emoji': {'title': 'title here', 'desc': 'description here'}}
        )

    async def red_delete_data_for_user(self, *, requester, user_id):
        for guild in self.bot.guilds:
            active_channels = await self.config.guild(guild).active_channels()
            active_users = await self.config.guild(guild).active_users()
            active_msgs = await self.config.guild(guild).active_msgs()
            active_indexes = []
            closed_channels = await self.config.guild(guild).closed()
            closed_indexes = []
            for i in range(0, len(active_channels)):
                channel = guild.get_channel(active_channels[i])
                if not channel:
                    continue
                if user_id in channel.name:
                    await channel.delete()
                    active_indexes.append(i)
            if len(active_indexes) > 0:
                active_indexes.reverse()
                for i in active_indexes:
                    active_channels.pop(i)
                    active_users.pop(i)
                    active_msgs.pop(i)
                await self.config.guild(guild).active_channels.set(active_channels)
                await self.config.guild(guild).active_users.set(active_users)
                await self.config.guild(guild).active_msgs.set(active_msgs)

            for i in range(0, len(closed_channels)):
                channel = guild.get_channel(closed_channels[i])
                if not channel:
                    continue
                if user_id in channel.name:
                    await channel.delete()
                    closed_indexes.append(i)
            if len(closed_indexes) > 0:
                closed_indexes.reverse()
                for i in closed_indexes:
                    closed_channels.pop(i)
                await self.config.guild(guild).closed.set(closed_channels)

    async def initialize(self):
        for guild in self.bot.guilds:
            enabled_message = await self.config.guild(guild).enabled()
            if enabled_message:
                self.enabled_cache[guild.id] = True

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @commands.group()
    @commands.guild_only()
    @checks.admin()
    @checks.bot_has_permissions(
        add_reactions=True,
        manage_channels=True,
        manage_messages=True,
        manage_permissions=True,
    )
    async def ticketset(self, ctx: commands.Context):
        """Various ReactTickets settings."""

    @ticketset.command(name="channel")
    async def ticketset_channel(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Set the support-request channel."""
        await self.config.guild(ctx.guild).request_channel.set(channel.id)
        await ctx.send(f"Channel has been set to {channel.mention}.")

    @ticketset.command(name="management")
    async def ticketset_management(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Set the support-management channel."""
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(f"Channel has been set to {channel.mention}.")

    @ticketset.command(name="role")
    async def ticketset_role(self, ctx: commands.Context, role: discord.Role):
        """Set the role for supports."""
        await self.config.guild(ctx.guild).role.set(role.id)
        await ctx.send(f"Support role has been set to {role.name}.")

    @ticketset.group(name="category")
    async def ticketset_category(self, ctx: commands.Context):
        """Set the ticket categories."""

    @ticketset_category.command(name="open")
    async def ticketset_category_open(
        self, ctx: commands.Context, *, category: discord.CategoryChannel
    ):
        """Set the category for open tickets."""
        await self.config.guild(ctx.guild).open_category.set(category.id)
        await ctx.send(f"Category for open tickets has been set to {category.mention}")

    @ticketset_category.command(name="closed")
    async def ticketset_category_closed(
        self, ctx: commands.Context, *, category: discord.CategoryChannel
    ):
        """Set the category for closed tickets."""
        await self.config.guild(ctx.guild).closed_category.set(category.id)
        await ctx.send(
            f"Category for closed tickets has been set to {category.mention}"
        )

    @ticketset.group(name="case")
    async def ticketset_case(self, ctx: commands.Context):
        """Set the ticket cases."""

    @ticketset_case.command(name="add")
    async def ticketset_case_add(
        self, ctx: commands.Context, emoji: typing.Union[discord.Emoji, str]
    ):
        """Add a support case type."""
        if await self.config.guild(ctx.guild).enabled():
            return await ctx.send(
                "Uh oh, you cannot add nor remove cases while support is enabled."
            )
        cases = await self.config.guild(ctx.guild).cases.get_raw()
        try:
            if cases[emoji]:
                return await ctx.send("Uh oh, that emoji is already registered.")
        except KeyError:
            pass
        try:
            await ctx.message.add_reaction(emoji)
        except discord.HTTPException:
            return await ctx.send("Uh oh, I cannot use that emoji.")
        await ctx.send("What is the title of this case? (e.g. Role change requested)")
        try:
            title = await self.bot.wait_for(
                "message", timeout=60, check=MessagePredicate.same_context(ctx)
            )
        except asyncio.TimeoutError:
            return await ctx.send("You took too long.")
        await ctx.send(
            "What's the message in the reaction message? (e.g. to request a role change)"
        )
        try:
            desc = await self.bot.wait_for(
                "message", timeout=60, check=MessagePredicate.same_context(ctx)
            )
        except asyncio.TimeoutError:
            return await ctx.send("You took too long.")
        await self.config.guild(ctx.guild).cases.set_raw(
            emoji, value={"title": title.content, "desc": desc.content}
        )
        await ctx.send(f"{title.content} was assigned to {emoji}.")

    @ticketset_case.command(name="del")
    async def ticketset_case_del(
        self, ctx: commands.Context, emoji: typing.Union[discord.Emoji, str]
    ):
        """Remove a support case type."""
        if await self.config.guild(ctx.guild).enabled():
            return await ctx.send(
                "Uh oh, you cannot add nor remove cases while support is enabled."
            )
        try:
            if not await self.config.guild(ctx.guild).cases.get_raw(emoji):
                return await ctx.send("Uh oh, that emoji is not registered.")
        except KeyError:
            return await ctx.send("Uh oh, that emoji is not registered.")
        await self.config.guild(ctx.guild).cases.clear_raw(emoji)
        await ctx.send(f"{emoji} has been deleted.")

    @ticketset_case.command(name="all")
    async def ticketset_case_all(self, ctx: commands.Context):
        """Display all registered cases."""
        cases = await self.config.guild(ctx.guild).cases.get_raw()
        string = self._get_cases_string(cases, "**Registered cases:**")
        await ctx.send(string)

    @ticketset.command(name="start")
    async def ticketset_start(self, ctx: commands.Context):
        """Start the support system."""
        data = await self.config.guild(ctx.guild).all()

        channel = ctx.guild.get_channel(data["request_channel"])
        if not channel:
            return await ctx.send("Uh oh, support is not set up properly.")
        try:
            message = await channel.fetch_message(data["enabled"])
            if message:
                return await ctx.send("Uh oh, support has already been started.")
        except discord.HTTPException:
            pass

        cases = await self.config.guild(ctx.guild).cases.get_raw()
        description = self._get_cases_string(
            cases, "React below with the reaction based on what you want.\n"
        )

        embed = discord.Embed(
            colour=await ctx.embed_colour(),
            title=f"{ctx.guild.name} support tickets",
            description=description,
        )
        msg = await channel.send(embed=embed)
        await self._add_reactions(msg, self._get_emoji_list(cases))
        await self.config.guild(ctx.guild).enabled.set(msg.id)
        self.enabled_cache[ctx.guild.id] = True
        await ctx.tick()

    @ticketset.command(name="stop")
    async def ticketset_stop(self, ctx: commands.Context):
        """Stop the support system."""
        data = await self.config.guild(ctx.guild).all()

        channel = ctx.guild.get_channel(data["request_channel"])
        if not channel:
            return await ctx.send("Uh oh, support is not set up properly.")
        message = await channel.fetch_message(data["enabled"])
        if not message:
            return await ctx.send("Uh oh, support has not been started.")

        await self.config.guild(ctx.guild).enabled.set(None)
        del self.enabled_cache[ctx.guild.id]
        await message.delete()
        await ctx.tick()

    @ticketset.command(name="settings")
    async def ticketset_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.guild(ctx.guild).all()

        manager_channel = ctx.guild.get_channel(data["channel"])
        manager_channel = manager_channel.mention if manager_channel else "None"

        request_channel = ctx.guild.get_channel(data["request_channel"])
        if request_channel:
            if not data["enabled"]:
                request_message = "False"
            else:
                request_message = await request_channel.fetch_message(data["enabled"])
                request_message = "True" if request_message else "False"
            request_channel = request_channel.mention
        else:
            request_channel = "None"

        open_category = ctx.guild.get_channel(data["open_category"])
        open_category = open_category.name if open_category else "None"

        closed_category = ctx.guild.get_channel(data["closed_category"])
        closed_category = closed_category.name if closed_category else "None"

        support_role = ctx.guild.get_role(data["role"])
        support_role = support_role.name if support_role else "None"

        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Reaction Tickets settings:__**"
        embed.set_footer(text="*required to function properly")

        embed.add_field(name="Enabled*:", value=request_message)
        embed.add_field(name="Request channel*:", value=request_channel)
        embed.add_field(name="Management channel*:", value=manager_channel)
        embed.add_field(name="Support role*:", value=support_role)
        embed.add_field(name="Open ticket category*:", value=open_category)
        embed.add_field(name="Closed ticket category*:", value=closed_category)
        embed.add_field(
            name="Registered cases:",
            value=f"Use `{ctx.clean_prefix}ticketset case all`",
        )

        await ctx.send(embed=embed)

    @ticketset.command(name="reset")
    async def ticketset_reset(
        self, ctx: commands.Context, confirmation: typing.Optional[bool]
    ):
        """Erase all data and settings."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** current data and settings. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}ticketset reset yes`."
            )
        await self.config.clear_all_guilds()
        await ctx.tick()

    @ticketset.command(name="purge")
    async def ticketset_purge(
        self, ctx: commands.Context, confirmation: typing.Optional[bool]
    ):
        """Deletes all closed ticket channels."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** closed tickets. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}ticketset purge yes`."
            )
        async with self.config.guild(ctx.guild).closed() as closed:
            for index, channel in enumerate(closed):
                try:
                    channel_obj = ctx.guild.get_channel(channel)
                    if channel_obj:
                        await channel_obj.delete(reason="Ticket purge")
                    closed.remove(channel)
                except discord.NotFound:
                    closed.remove(channel)
                except discord.HTTPException:
                    return await ctx.send("Something went wrong. Aborting.")

    @commands.command()
    @commands.guild_only()
    @checks.mod()
    @checks.bot_has_permissions(manage_messages=True)
    async def ticket(self, ctx: commands.Context, msg_id: int, *, note: str):
        """Add a staff-only note to a ticket.

        <msg_id> is in the support-management message's footer."""
        settings = await self.config.guild(ctx.guild).all()
        channel = ctx.guild.get_channel(settings["channel"])
        try:
            manager_msg = await channel.fetch_message(msg_id)
        except discord.NotFound:
            return await ctx.send("Ticket not found.")
        await self._edit_manager_msg(
            manager_msg, f"Note", False, note + f"\nby {ctx.author.mention}"
        )
        await ctx.tick()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if (
            payload.user_id == self.bot.user.id
            or not payload.guild_id
            or payload.guild_id not in self.enabled_cache
        ):
            return

        guild = self.bot.get_guild(payload.guild_id)
        settings = await self.config.guild(guild).all()

        if not settings["enabled"]:
            return

        channel = guild.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = guild.get_member(payload.user_id)

        if channel.id == settings["request_channel"]:
            await message.remove_reaction(payload.emoji, user)
            await self._open_ticket(channel, guild, str(payload.emoji), user, settings)
        if channel.id in settings["active_channels"]:
            await message.remove_reaction(payload.emoji, user)
            await self._in_active_support(
                message, channel, guild, str(payload.emoji), user, settings
            )

    async def _add_reactions(self, message: discord.Message, emoji_list: list):
        for e in emoji_list:
            await message.add_reaction(e)

    async def _open_ticket(
        self,
        channel: discord.TextChannel,
        guild: discord.Guild,
        emoji: str,
        user: discord.Member,
        settings: dict,
    ):
        name = f"open-{user.id}"
        category = guild.get_channel(settings["open_category"])

        cases = await self.config.guild(guild).cases.get_raw()
        if emoji not in self._get_emoji_list(cases):
            return await channel.send("Invalid reaction.", delete_after=5)
        reason = cases[emoji]["title"]

        found = any(
            channel.name in [f"open-{user.id}", f"assigned-{user.id}"]
            for channel in category.channels
        )

        if not found:
            overwrite = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                user: discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                ),
                guild.get_role(settings["role"]): discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    embed_links=True,
                    attach_files=True,
                    manage_messages=True,
                ),
            }
            user_channel = await guild.create_text_channel(
                name,
                overwrites=overwrite,
                category=category,
                topic=reason,
            )

            embed = discord.Embed(
                title=reason,
                description="To close this ticket, react with 🔒 below.",
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_thumbnail(url=user.avatar_url)
            embed.set_footer(text=f"{user.name}#{user.discriminator} ({user.id})")
            embed_user_message = await user_channel.send(
                content=f"{user.mention}, a staff member will be with you shortly.",
                embed=embed,
            )
            await self._add_reactions(embed_user_message, ["🔒", "✋"])

            embed = discord.Embed(
                title=f"{user.name}#{user.discriminator} ({user.id})",
                description=reason,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_thumbnail(url=user.avatar_url)
            manager_msg = await guild.get_channel(settings["channel"]).send(
                content=f"User: {user.mention}\nChannel: {user_channel.mention}",
                embed=embed,
            )
            embed.set_footer(text=f"Message ID: {manager_msg.id}")
            await manager_msg.edit(embed=embed)
            async with self.config.guild(guild).active_channels() as active_channels:
                active_channels.append(user_channel.id)
            async with self.config.guild(guild).active_users() as active_users:
                active_users.append(user.id)
            async with self.config.guild(guild).active_msgs() as active_msgs:
                active_msgs.append(manager_msg.id)
        else:
            await channel.send("You already have an open ticket.", delete_after=5)

    async def _in_active_support(
        self,
        message: discord.Message,
        channel: discord.TextChannel,
        guild: discord.Guild,
        emoji: str,
        user: discord.Member,
        settings: dict,
    ):
        index = settings["active_channels"].index(channel.id)
        target_id = settings["active_users"][index]
        try:
            target = await guild.fetch_member(target_id)
        except discord.NotFound:
            target = None
        manager_msg = await guild.get_channel(settings["channel"]).fetch_message(
            settings["active_msgs"][index]
        )

        if not target:
            await channel.send("User has left the guild. Close this ticket, please.")

        if emoji == "🔒":
            if not target:
                await self._edit_manager_msg(
                    manager_msg, "Closed", True, f"(user has left) by {user.mention}"
                )
            else:
                await self._edit_manager_msg(
                    manager_msg, "Closed", True, f"by {user.mention}"
                )

            async with self.config.guild(guild).closed() as closed:
                closed.append(channel.id)
            async with self.config.guild(guild).active_channels() as active_channels:
                active_channels.remove(channel.id)
            async with self.config.guild(guild).active_users() as active_users:
                active_users.remove(target_id)
            async with self.config.guild(guild).active_msgs() as active_msgs:
                active_msgs.remove(manager_msg.id)

            await message.clear_reactions()
            await channel.edit(
                category=guild.get_channel(settings["closed_category"]),
                name=f"closed-{target.id}",
                overwrites={
                    guild.default_role: discord.PermissionOverwrite(
                        read_messages=False
                    ),
                    guild.get_role(settings["role"]): discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        embed_links=True,
                        attach_files=True,
                        manage_messages=True,
                    ),
                },
                reason="Closed support ticket",
            )
        elif emoji == "✋" and user.id not in settings["active_users"]:
            if channel.name != f"open-{target.id}":
                return
            await channel.edit(name=f"assigned-{target.id}", reason="Ticket assigned")
            await self._edit_manager_msg(
                manager_msg, "Assigned", True, f"to {user.mention}"
            )
            await channel.send(f"This ticket has been assigned to {user.mention}.")
        else:
            await channel.send("Invalid reaction.", delete_after=5)

    async def _edit_manager_msg(
        self, message: discord.Message, state: str, inline: bool, text: str
    ):
        embed = message.embeds[0]
        value = f"{text} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        embed.add_field(name=state, value=value, inline=inline)
        await message.edit(embed=embed)

    def _get_cases_string(self, cases: dict, string: str):
        for emoji in cases:
            string += f"\n{emoji} {cases[emoji]['desc']}"
        return string

    def _get_emoji_list(self, cases):
        return [emoji for emoji in cases]
