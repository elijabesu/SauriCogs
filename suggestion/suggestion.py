import discord
import datetime
import typing

from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import humanize_list

from redbot.core.bot import Red


class Suggestion(commands.Cog):
    """
    Simple suggestion box, basically.

    Only admins can approve or reject suggestions.
    """

    __author__ = "saurichable"
    __version__ = "1.5.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=2115656421364, force_registration=True
        )
        self.config.register_guild(
            same=False,
            suggest_id=None,
            approve_id=None,
            reject_id=None,
            next_id=1,
            up_emoji=None,
            down_emoji=None,
            delete_suggest=False,
            delete_suggestion=True,
        )
        self.config.register_global(
            toggle=False, server_id=None, channel_id=None, next_id=1, ignore=[]
        )
        self.config.init_custom("SUGGESTION", 2)  # server_id, suggestion_id
        self.config.register_custom(
            "SUGGESTION",
            author=[],  # id, name, discriminator
            msg_id=0,
            finished=False,
            approved=False,
            rejected=False,
            reason=False,
            stext=None,
            rtext=None,
        )

    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(add_reactions=True)
    async def suggest(self, ctx: commands.Context, *, suggestion: str):
        """Suggest something. Message is required."""
        suggest_id = await self.config.guild(ctx.guild).suggest_id()
        if not suggest_id:
            if not await self.config.toggle():
                return await ctx.send("Uh oh, suggestions aren't enabled.")
            if ctx.guild.id in await self.config.ignore():
                return await ctx.send("Uh oh, suggestions aren't enabled.")
            global_guild = self.bot.get_guild(await self.config.server_id())
            channel = global_guild.get_channel(await self.config.channel_id())
        else:
            channel = ctx.guild.get_channel(suggest_id)
        if not channel:
            return await ctx.send(
                "Uh oh, looks like your Admins haven't added the required channel."
            )
        embed = discord.Embed(color=await ctx.embed_colour(), description=suggestion)
        embed.set_author(
            name=f"Suggestion by {ctx.author.display_name}",
            icon_url=ctx.author.avatar_url,
        )
        embed.set_footer(
            text=f"Suggested by {ctx.author.name}#{ctx.author.discriminator} ({ctx.author.id})"
        )

        if not suggest_id:
            if await self.config.toggle():
                s_id = await self.config.next_id()
                await self.config.next_id.set(s_id + 1)
                server = 1
                content = f"Global suggestion #{s_id}"
        else:
            s_id = await self.config.guild(ctx.guild).next_id()
            await self.config.guild(ctx.guild).next_id.set(s_id + 1)
            server = ctx.guild.id
            content = f"Suggestion #{s_id}"
        msg = await channel.send(content=content, embed=embed)

        up_emoji, down_emoji = await self._get_emojis(ctx)
        await msg.add_reaction(up_emoji)
        await msg.add_reaction(down_emoji)

        async with self.config.custom("SUGGESTION", server, s_id).author() as author:
            author.append(ctx.author.id)
            author.append(ctx.author.name)
            author.append(ctx.author.discriminator)
        await self.config.custom("SUGGESTION", server, s_id).stext.set(suggestion)
        await self.config.custom("SUGGESTION", server, s_id).msg_id.set(msg.id)

        if await self.config.guild(ctx.guild).delete_suggest():
            await ctx.message.delete()
        else:
            await ctx.tick()
        try:
            await ctx.author.send(
                content="Your suggestion has been sent for approval!", embed=embed
            )
        except discord.Forbidden:
            pass

    @checks.admin()
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_messages=True)
    async def approve(
            self,
            ctx: commands.Context,
            suggestion_id: int,
            is_global: typing.Optional[bool],
    ):
        """Approve a suggestion."""
        await self._finish_suggestion(ctx, suggestion_id, is_global, True, None)

    @checks.admin()
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_messages=True)
    async def reject(
            self,
            ctx: commands.Context,
            suggestion_id: int,
            is_global: typing.Optional[bool],
            *,
            reason: typing.Optional[str],
    ):
        """Reject a suggestion. Reason is optional."""
        await self._finish_suggestion(ctx, suggestion_id, is_global, False, reason)

    @checks.admin()
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_messages=True)
    async def addreason(
            self,
            ctx: commands.Context,
            suggestion_id: int,
            is_global: typing.Optional[bool],
            *,
            reason: str,
    ):
        """Add a reason to a rejected suggestion.

        Only works for non global suggestions."""
        if is_global:
            try:
                server, old_channel = await self._check_global(ctx)
            except TypeError:
                return
        else:
            server = ctx.guild.id
            if not await self.config.guild(ctx.guild).same():
                channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).reject_id())
            else:
                channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).suggest_id())
        msg_id = await self.config.custom("SUGGESTION", server, suggestion_id).msg_id()
        if msg_id != 0:
            if not await self.config.custom(
                    "SUGGESTION", server, suggestion_id
            ).rejected():
                return await ctx.send("This suggestion hasn't been rejected.")
            if await self.config.custom("SUGGESTION", server, suggestion_id).reason():
                return await ctx.send("This suggestion already has a reason.")
            content, embed = await self._build_suggestion(
                ctx, ctx.author.id, ctx.guild.id, suggestion_id, is_global
            )
            embed.add_field(name="Reason:", value=reason, inline=False)
            msg = await channel.fetch_message(msg_id)
            if msg:
                await msg.edit(content=content, embed=embed)
        await self.config.custom("SUGGESTION", server, suggestion_id).reason.set(True)
        await self.config.custom("SUGGESTION", server, suggestion_id).rtext.set(reason)
        await ctx.tick()

    @checks.admin()
    @commands.command()
    @commands.guild_only()
    async def showsuggestion(
            self,
            ctx: commands.Context,
            suggestion_id: int,
            is_global: typing.Optional[bool],
    ):
        """Show a suggestion."""
        content, embed = await self._build_suggestion(
            ctx, ctx.author.id, ctx.guild.id, suggestion_id, is_global
        )
        await ctx.send(content=content, embed=embed)

    @checks.admin()
    @checks.bot_has_permissions(
        manage_channels=True, add_reactions=True, manage_messages=True
    )
    @commands.group(autohelp=True, aliases=["suggestion"])
    @commands.guild_only()
    async def suggestset(self, ctx: commands.Context):
        f"""Various Suggestion settings.
        
        Version: {self.__version__}
        Author: {self.__author__}"""

    @suggestset.command(name="channel")
    async def suggestset_channel(
            self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel]
    ):
        """Set the channel for suggestions.

        If the channel is not provided, suggestions will be disabled."""
        if channel:
            await self.config.guild(ctx.guild).suggest_id.set(channel.id)
        else:
            await self.config.guild(ctx.guild).suggest_id.clear()
        await ctx.tick()

    @suggestset.command(name="approved")
    async def suggestset_approved(
            self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel]
    ):
        """Set the channel for suggestions.

        If the channel is not provided, approved suggestions will not be reposted."""
        if channel:
            await self.config.guild(ctx.guild).approve_id.set(channel.id)
        else:
            await self.config.guild(ctx.guild).approve_id.clear()
        await ctx.tick()

    @suggestset.command(name="rejected")
    async def suggestset_rejected(
            self, ctx: commands.Context, channel: typing.Optional[discord.TextChannel]
    ):
        """Set the channel for suggestions.

        If the channel is not provided, rejected suggestions will not be reposted."""
        if channel:
            await self.config.guild(ctx.guild).reject_id.set(channel.id)
        else:
            await self.config.guild(ctx.guild).reject_id.clear()
        await ctx.tick()

    @suggestset.command(name="same")
    async def suggestset_same(self, ctx: commands.Context, same: bool):
        """Set whether to use the same channel for new and finished suggestions."""
        await ctx.send(
            "Suggestions won't be reposted anywhere, only their title will change accordingly."
            if same
            else "Suggestions will go to their appropriate channels upon approving/rejecting."
        )
        await self.config.guild(ctx.guild).same.set(same)

    @suggestset.command(name="upemoji")
    async def suggestset_upemoji(
            self, ctx: commands.Context, up_emoji: typing.Optional[discord.Emoji]
    ):
        """Set custom reactions emoji instead of ✅. """
        if not up_emoji:
            await self.config.guild(ctx.guild).up_emoji.clear()
        else:
            try:
                await ctx.message.add_reaction(up_emoji)
            except discord.HTTPException:
                return await ctx.send("Uh oh, I cannot use that emoji.")
            await self.config.guild(ctx.guild).up_emoji.set(up_emoji.id)
        await ctx.tick()

    @suggestset.command(name="downemoji")
    async def suggestset_downemoji(
            self, ctx: commands.Context, down_emoji: typing.Optional[discord.Emoji]
    ):
        """Set custom reactions emoji instead of ❎. """
        if not down_emoji:
            await self.config.guild(ctx.guild).down_emoji.clear()
        else:
            try:
                await ctx.message.add_reaction(down_emoji)
            except discord.HTTPException:
                return await ctx.send("Uh oh, I cannot use that emoji.")
            await self.config.guild(ctx.guild).down_emoji.set(down_emoji.id)
        await ctx.tick()

    @suggestset.command(name="autodelete")
    async def suggestset_autodelete(self, ctx: commands.Context, on_off: typing.Optional[bool]):
        """Toggle whether after `[p]suggest`, the bot deletes the command message. """
        target_state = on_off or not (
            await self.config.guild(ctx.guild).delete_suggest()
        )

        await self.config.guild(ctx.guild).delete_suggest.set(target_state)
        await ctx.send("Auto deletion is now enabled." if target_state else "Auto deletion is now disabled.")

    @suggestset.command(name="delete")
    async def suggestset_delete(self, ctx: commands.Context, on_off: typing.Optional[bool]):
        """Toggle whether suggestions in the original suggestion channel get deleted after being approved/rejected."""
        target_state = on_off or not (
            await self.config.guild(ctx.guild).delete_suggestion()
        )

        await self.config.guild(ctx.guild).delete_suggestion.set(target_state)
        await ctx.send(
            "Suggestions will be deleted upon approving/rejecting from the original suggestion channel."
            if target_state
            else "Suggestions will stay in the original channel after approving/rejecting."
        )

    @suggestset.command(name="settings")
    async def suggestset_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.guild(ctx.guild).all()
        suggest_channel = ctx.guild.get_channel(
            await self.config.guild(ctx.guild).suggest_id()
        )
        suggest_channel = "None" if not suggest_channel else suggest_channel.mention
        approve_channel = ctx.guild.get_channel(
            await self.config.guild(ctx.guild).approve_id()
        )
        approve_channel = "None" if not approve_channel else approve_channel.mention
        reject_channel = ctx.guild.get_channel(
            await self.config.guild(ctx.guild).reject_id()
        )
        reject_channel = "None" if not reject_channel else reject_channel.mention
        up_emoji, down_emoji = await self._get_emojis(ctx)

        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Suggestion settings (guild):__**"

        embed.set_footer(text="*required to function properly")
        embed.add_field(name="Same channel*:", value=str(data["same"]), inline=False)
        embed.add_field(name="Suggest channel*:", value=suggest_channel)
        embed.add_field(name="Approved channel:", value=approve_channel)
        embed.add_field(name="Rejected channel:", value=reject_channel)
        embed.add_field(name="Up emoji:", value=up_emoji)
        embed.add_field(name="Down emoji:", value=down_emoji)
        embed.add_field(
            name=f"Delete `{ctx.clean_prefix}suggest` upon use:",
            value=data["delete_suggest"],
            inline=False,
        )
        embed.add_field(
            name="Delete suggestion upon approving/rejecting:",
            value=data["delete_suggestion"],
            inline=False,
        )

        await ctx.send(embed=embed)

    @suggestset.group(autohelp=True)
    @checks.is_owner()
    @commands.guild_only()
    async def globalset(self, ctx: commands.Context):
        ("""Global suggestions settings.

        There is nothing like approved or rejected channels because global suggestions are meant to be for the bot"""
         """only and will only work if it is sent in a server where normal suggestions are disabled.""")

    @globalset.command(name="toggle")
    async def suggestset_globalset_toggle(
            self, ctx: commands.Context, on_off: typing.Optional[bool]
    ):
        """Toggle global suggestions.
        If `on_off` is not provided, the state will be flipped."""
        target_state = on_off or not (await self.config.toggle())
        await self.config.toggle.set(target_state)
        if target_state:
            await ctx.send("Global suggestions are now enabled.")
        else:
            await ctx.send("Global suggestions are now disabled.")

    @globalset.command(name="channel")
    async def suggestset_globalset_channel(
            self,
            ctx: commands.Context,
            server: typing.Optional[discord.Guild],
            channel: typing.Optional[discord.TextChannel],
    ):
        """Add channel where global suggestions should be sent."""
        if not server:
            server = ctx.guild
        if not channel:
            channel = ctx.channel
        await self.config.server_id.set(server.id)
        await self.config.channel_id.set(channel.id)
        await ctx.send(f"{channel.mention} has been saved for global suggestions.")

    @globalset.command(name="ignore")
    async def suggestset_globalset_ignore(
            self, ctx: commands.Context, server: typing.Optional[discord.Guild]
    ):
        """Ignore suggestions from the server. """
        if not server:
            server = ctx.guild
        if server.id not in await self.config.ignore():
            async with self.config.ignore() as ignore:
                ignore.append(server.id)
            await ctx.send(f"{server.name} has been added into the ignored list.")
        else:
            await ctx.send(f"{server.name} is already in the ignored list.")

    @globalset.command(name="unignore")
    async def suggestset_globalset_unignore(
            self, ctx: commands.Context, server: typing.Optional[discord.Guild]
    ):
        """Remove server from the ignored list. """
        if not server:
            server = ctx.guild
        if server.id in await self.config.ignore():
            async with self.config.ignore() as ignore:
                ignore.remove(server.id)
            await ctx.send(f"{server.name} has been removed from the ignored list.")
        else:
            await ctx.send(f"{server.name} already isn't in the ignored list.")

    @globalset.command(name="settings")
    async def suggestset_globalset_settings(self, ctx: commands.Context):
        """See current settings."""
        data = await self.config.all()
        global_guild = self.bot.get_guild(data["server_id"])
        if global_guild:
            channel = global_guild.get_channel(data["channel_id"])
            channel = "None" if not channel else f"{channel.name} ({global_guild.name})"
        else:
            channel = "None"
        servers = []
        for sid in data["ignore"]:
            server = self.bot.get_guild(sid)
            if server:
                servers.append(server.name)
        servers_text = "None" if servers == [] else humanize_list(servers)

        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Suggestion settings (global):__**"

        embed.set_footer(text="*required to function properly")
        embed.add_field(name="Enabled*:", value=data["toggle"])
        embed.add_field(name="Channel*:", value=channel)
        embed.add_field(name="Ignored servers:", value=servers_text, inline=False)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        if user.id == self.bot.user.id:
            return
        # server suggestions
        if message.channel.id == await self.config.guild(message.guild).suggest_id():
            for message_reaction in message.reactions:
                if (
                    message_reaction.emoji != reaction.emoji
                    and user in await message_reaction.users().flatten()
                ):
                    await message_reaction.remove(user)

        # global suggestions
        if message.channel.id == await self.config.channel_id():
            for message_reaction in message.reactions:
                if (
                    message_reaction.emoji != reaction.emoji
                    and user in await message_reaction.users().flatten()
                ):
                    await message_reaction.remove(user)

    async def _build_suggestion(
            self, ctx, author_id, server_id, suggestion_id, is_global
    ):
        if is_global:
            if not await self.config.toggle():
                return await ctx.send("Global suggestions aren't enabled.")
            if author_id not in self.bot.owner_ids:
                return await ctx.send("Uh oh, you're not my owner.")
            server = 1
            if (
                    await self.config.custom(
                        "SUGGESTION", server, suggestion_id
                    ).msg_id()
                    != 0
            ):
                content = f"Global suggestion #{suggestion_id}"
            else:
                return await ctx.send(
                    "Uh oh, that suggestion doesn't seem to exist."
                )
        if not is_global:
            server = server_id
            if (
                await self.config.custom(
                    "SUGGESTION", server, suggestion_id
                ).msg_id()
                == 0
            ):
                return await ctx.send("Uh oh, that suggestion doesn't seem to exist.")
            else:
                content = f"Suggestion #{suggestion_id}"
        op_info = await self.config.custom("SUGGESTION", server, suggestion_id).author()
        op, op_name, op_discriminator, op_id, op_avatar = await self._get_op_info(ctx, op_info)
        if await self.config.custom("SUGGESTION", server, suggestion_id).finished():
            if await self.config.custom("SUGGESTION", server, suggestion_id).approved():
                atext = f"Approved suggestion by {op_name}"
            else:
                if await self.config.custom(
                        "SUGGESTION", server, suggestion_id
                ).rejected():
                    atext = f"Rejected suggestion by {op_name}"
        else:
            atext = f"Suggestion by {op_name}"
        embed = discord.Embed(
            color=await ctx.embed_colour(),
            description=await self.config.custom(
                "SUGGESTION", server, suggestion_id
            ).stext(),
        )
        embed.set_author(name=atext, icon_url=op_avatar)
        embed.set_footer(text=f"Suggested by {op_name}#{op_discriminator} ({op_id})")

        if await self.config.custom("SUGGESTION", server, suggestion_id).reason():
            embed.add_field(
                name="Reason:",
                value=await self.config.custom(
                    "SUGGESTION", server, suggestion_id
                ).rtext(),
                inline=False,
            )
        return content, embed

    async def _get_results(self, ctx, message):
        up_emoji, down_emoji = await self._get_emojis(ctx)
        up_count = 0
        down_count = 0

        for reaction in message.reactions:
            if reaction.emoji == up_emoji:
                up_count = reaction.count - 1  # minus the bot
            if reaction.emoji == down_emoji:
                down_count = reaction.count - 1 # minus the bot

        return f"{up_count}x {up_emoji}\n{down_count}x {down_emoji}"

    async def _get_emojis(self, ctx):
        up_emoji = self.bot.get_emoji(await self.config.guild(ctx.guild).up_emoji())
        if not up_emoji:
            up_emoji = "✅"
        down_emoji = self.bot.get_emoji(await self.config.guild(ctx.guild).down_emoji())
        if not down_emoji:
            down_emoji = "❎"
        return up_emoji, down_emoji

    async def _get_op_info(self, ctx, op_info):
        op_id = op_info[0]
        op = await self.bot.fetch_user(op_id)
        if op:
            op_name = op.name
            op_discriminator = op.discriminator
            op_avatar = op.avatar_url
        else:
            op_name = op_info[1]
            op_discriminator = op_info[2]
            op_avatar = ctx.guild.icon_url

        return op, op_name, op_discriminator, op_id, op_avatar

    async def _check_global(self, ctx):
        if not await self.config.toggle():
            return await ctx.send("Global suggestions aren't enabled.")
        if ctx.author.id not in self.bot.owner_ids:
            return await ctx.send("Uh oh, you're not my owner.")
        server = 1
        global_guild = self.bot.get_guild(await self.config.server_id())
        old_channel = global_guild.get_channel(await self.config.channel_id())
        return server, old_channel

    async def _contact_op(self, op, content, embed):
        try:
            await op.send(content=content, embed=embed)
        except discord.Forbidden:
            pass

    async def _finish_suggestion(self, ctx, suggestion_id, is_global, approve, reason):
        if is_global:
            try:
                server, old_channel = await self._check_global(ctx)
            except TypeError:
                return
        else:
            server = ctx.guild.id
            old_channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).suggest_id())
            if approve:
                channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).approve_id())
            else:
                channel = ctx.guild.get_channel(await self.config.guild(ctx.guild).reject_id())
        msg_id = await self.config.custom("SUGGESTION", server, suggestion_id).msg_id()
        if (
            msg_id != 0
            and await self.config.custom(
                "SUGGESTION", server, suggestion_id
            ).finished()
        ):
            return await ctx.send("This suggestion has been finished already.")
        try:
            old_msg = await old_channel.fetch_message(msg_id)
        except discord.NotFound:
            return await ctx.send("Uh oh, message with this ID doesn't exist.")
        if not old_msg:
            return await ctx.send("Uh oh, message with this ID doesn't exist.")
        embed = old_msg.embeds[0]
        content = old_msg.content

        op_info = await self.config.custom("SUGGESTION", server, suggestion_id).author()
        op, op_name, op_discriminator, op_id, op_avatar = await self._get_op_info(ctx, op_info)

        approved = "Approved" if approve else "Rejected"

        embed.set_author(name=f"{approved} suggestion by {op_name}", icon_url=op_avatar)
        embed.add_field(
            name="Results:", value=await self._get_results(ctx, old_msg), inline=False
        )
        if reason:
            embed.add_field(name="Reason:", value=reason, inline=False)
            await self.config.custom("SUGGESTION", server, suggestion_id).reason.set(
                True
            )
            await self.config.custom("SUGGESTION", server, suggestion_id).rtext.set(
                reason
            )

        if is_global:
            await old_msg.edit(content=content, embed=embed)
        else:
            if channel:
                if not await self.config.guild(ctx.guild).same():
                    if await self.config.guild(ctx.guild).delete_suggestion():
                        await old_msg.delete()
                    nmsg = await channel.send(content=content, embed=embed)
                    await self.config.custom(
                        "SUGGESTION", server, suggestion_id
                    ).msg_id.set(nmsg.id)
                else:
                    await old_msg.edit(content=content, embed=embed)
            else:
                if not await self.config.guild(ctx.guild).same():
                    if await self.config.guild(ctx.guild).delete_suggestion():
                        await old_msg.delete()
                    await self.config.custom(
                        "SUGGESTION", server, suggestion_id
                    ).msg_id.set(1)
                else:
                    await old_msg.edit(content=content, embed=embed)
        await self.config.custom("SUGGESTION", server, suggestion_id).finished.set(True)
        await self.config.custom("SUGGESTION", server, suggestion_id).approved.set(True)
        await ctx.tick()

        await self._contact_op(op, f"Your suggestion has been {approved.lower()}!", embed)
