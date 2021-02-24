import asyncio
import discord

from typing import Optional
from discord.utils import get
from datetime import timedelta

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.antispam import AntiSpam

from redbot.core.bot import Red


class Suggestion(commands.Cog):
    """
    Simple suggestion box, basically.

    **Use `[p]setsuggest setup` first.**
    Only admins can approve or reject suggestions.
    """

    __author__ = "saurichable"
    __version__ = "1.4.8"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=2115656421364, force_registration=True
        )
        self.antispam = {}
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
        self.config.init_custom("SUGGESTION", 2) # server_id, suggestion_id
        self.config.register_custom(
            "SUGGESTION",
            author=[],
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
            if await self.config.toggle():
                if ctx.guild.id in await self.config.ignore():
                    return await ctx.send("Uh oh, suggestions aren't enabled.")
                global_guild = self.bot.get_guild(await self.config.server_id())
                channel = get(
                    global_guild.text_channels, id=await self.config.channel_id()
                )
            else:
                return await ctx.send("Uh oh, suggestions aren't enabled.")
        else:
            channel = get(ctx.guild.text_channels, id=suggest_id)
        if not channel:
            return await ctx.send(
                "Uh oh, looks like your Admins haven't added the required channel."
            )
        if ctx.guild not in self.antispam:
            self.antispam[ctx.guild] = {}
        if ctx.author not in self.antispam[ctx.guild]:
            self.antispam[ctx.guild][ctx.author] = AntiSpam([(timedelta(days=1), 6)])
        if self.antispam[ctx.guild][ctx.author].spammy:
            return await ctx.send("Uh oh, you're doing this way too frequently.")
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

        self.antispam[ctx.guild][ctx.author].stamp()
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

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_messages=True)
    async def approve(
        self,
        ctx: commands.Context,
        suggestion_id: int,
        is_global: Optional[bool] = False,
    ):
        """Approve a suggestion."""
        if is_global:
            if await self.config.toggle():
                if ctx.author.id not in self.bot.owner_ids:
                    return await ctx.send("Uh oh, you're not my owner.")
                server = 1
                global_guild = self.bot.get_guild(await self.config.server_id())
                oldchannel = get(
                    global_guild.text_channels, id=await self.config.channel_id()
                )
            else:
                return await ctx.send("Global suggestions aren't enabled.")
        else:
            server = ctx.guild.id
            oldchannel = get(
                ctx.guild.text_channels,
                id=await self.config.guild(ctx.guild).suggest_id(),
            )
            channel = get(
                ctx.guild.text_channels,
                id=await self.config.guild(ctx.guild).approve_id(),
            )
        msg_id = await self.config.custom("SUGGESTION", server, suggestion_id).msg_id()
        if msg_id != 0:
            if await self.config.custom("SUGGESTION", server, suggestion_id).finished():
                return await ctx.send("This suggestion has been finished already.")
        try:
            oldmsg = await oldchannel.fetch_message(id=msg_id)
        except discord.NotFound:
            return await ctx.send("Uh oh, message with this ID doesn't exist.")
        if not oldmsg:
            return await ctx.send("Uh oh, message with this ID doesn't exist.")
        embed = oldmsg.embeds[0]
        content = oldmsg.content

        op_info = await self.config.custom("SUGGESTION", server, suggestion_id).author()
        op_id = int(op_info[0])
        op = await self.bot.fetch_user(op_id)
        op_name = op.name
        op_avatar = op.avatar_url
        if not op:
            op_name = str(op_info[1])
            op_avatar = ctx.guild.icon_url
        embed.set_author(name=f"Approved suggestion by {op_name}", icon_url=op_avatar)

        embed.add_field(name="Results:", value=await self._get_results(ctx, oldmsg), inline=False)

        if is_global:
            await oldmsg.edit(content=content, embed=embed)
        else:
            if channel:
                if await self.config.guild(ctx.guild).delete_suggestion():
                    await oldmsg.delete()
                nmsg = await channel.send(content=content, embed=embed)
                await self.config.custom(
                    "SUGGESTION", server, suggestion_id
                ).msg_id.set(nmsg.id)
            else:
                if not await self.config.guild(ctx.guild).same():
                    if await self.config.guild(ctx.guild).delete_suggestion():
                        await oldmsg.delete()
                    await self.config.custom(
                        "SUGGESTION", server, suggestion_id
                    ).msg_id.set(1)
                else:
                    await oldmsg.edit(content=content, embed=embed)
        await self.config.custom("SUGGESTION", server, suggestion_id).finished.set(True)
        await self.config.custom("SUGGESTION", server, suggestion_id).approved.set(True)
        await ctx.tick()

        try:
            await op.send(content="Your suggestion has been approved!", embed=embed)
        except discord.Forbidden:
            pass

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_messages=True)
    async def reject(
        self,
        ctx: commands.Context,
        suggestion_id: int,
        is_global: Optional[bool] = False,
        *,
        reason="",
    ):
        """Reject a suggestion. Reason is optional."""
        if is_global:
            if await self.config.toggle():
                if ctx.author.id not in self.bot.owner_ids:
                    return await ctx.send("Uh oh, you're not my owner.")
                server = 1
                global_guild = self.bot.get_guild(await self.config.server_id())
                oldchannel = get(
                    global_guild.text_channels, id=await self.config.channel_id()
                )
            else:
                return await ctx.send("Global suggestions aren't enabled.")
        else:
            server = ctx.guild.id
            oldchannel = get(
                ctx.guild.text_channels,
                id=await self.config.guild(ctx.guild).suggest_id(),
            )
            channel = get(
                ctx.guild.text_channels,
                id=await self.config.guild(ctx.guild).reject_id(),
            )
        msg_id = await self.config.custom("SUGGESTION", server, suggestion_id).msg_id()
        if msg_id != 0:
            if await self.config.custom("SUGGESTION", server, suggestion_id).finished():
                return await ctx.send("This suggestion has been finished already.")
        try:
            oldmsg = await oldchannel.fetch_message(id=msg_id)
        except discord.NotFound:
            return await ctx.send("Uh oh, message with this ID doesn't exist.")
        if not oldmsg:
            return await ctx.send("Uh oh, message with this ID doesn't exist.")
        embed = oldmsg.embeds[0]
        content = oldmsg.content

        op_info = await self.config.custom("SUGGESTION", server, suggestion_id).author()
        op_id = int(op_info[0])
        op = await self.bot.fetch_user(op_id)
        op_name = op.name
        op_avatar = op.avatar_url
        if not op:
            op_name = str(op_info[1])
            op_avatar = ctx.guild.icon_url
        embed.set_author(name=f"Rejected suggestion by {op_name}", icon_url=op_avatar)

        embed.add_field(name="Results:", value=await self._get_results(ctx, oldmsg), inline=False)

        if reason:
            embed.add_field(name="Reason:", value=reason, inline=False)
            await self.config.custom("SUGGESTION", server, suggestion_id).reason.set(
                True
            )
            await self.config.custom("SUGGESTION", server, suggestion_id).rtext.set(
                reason
            )
        if is_global:
            await oldmsg.edit(content=content, embed=embed)
        else:
            if channel:
                if await self.config.guild(ctx.guild).delete_suggestion():
                    await oldmsg.delete()
                nmsg = await channel.send(content=content, embed=embed)
                await self.config.custom(
                    "SUGGESTION", server, suggestion_id
                ).msg_id.set(nmsg.id)
            else:
                if not await self.config.guild(ctx.guild).same():
                    if await self.config.guild(ctx.guild).delete_suggestion():
                        await oldmsg.delete()
                    await self.config.custom(
                        "SUGGESTION", server, suggestion_id
                    ).msg_id.set(1)
                else:
                    await oldmsg.edit(content=content, embed=embed)
        await self.config.custom("SUGGESTION", server, suggestion_id).finished.set(True)
        await self.config.custom("SUGGESTION", server, suggestion_id).rejected.set(True)
        await ctx.tick()

        try:
            await op.send(content="Your suggestion has been rejected!", embed=embed)
        except discord.Forbidden:
            pass

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_messages=True)
    async def addreason(
        self,
        ctx: commands.Context,
        suggestion_id: int,
        is_global: Optional[bool] = False,
        *,
        reason: str,
    ):
        """Add a reason to a rejected suggestion.
        
        Only works for non global suggestions."""
        if is_global:
            if await self.config.toggle():
                if ctx.author.id not in self.bot.owner_ids:
                    return await ctx.send("Uh oh, you're not my owner.")
                server = 1
                global_guild = self.bot.get_guild(await self.config.server_id())
                channel = get(
                    global_guild.text_channels, id=await self.config.channel_id()
                )
            else:
                return await ctx.send("Global suggestions aren't enabled.")
        else:
            server = ctx.guild.id
            if not await self.config.guild(ctx.guild).same():
                channel = get(
                    ctx.guild.text_channels,
                    id=await self.config.guild(ctx.guild).reject_id(),
                )
            else:
                channel = get(
                    ctx.guild.text_channels,
                    id=await self.config.guild(ctx.guild).suggest_id(),
                )
        msg_id = await self.config.custom("SUGGESTION", server, suggestion_id).msg_id()
        if msg_id != 0:
            if not await self.config.custom("SUGGESTION", server, suggestion_id).rejected():
                return await ctx.send("This suggestion hasn't been rejected.")
            if await self.config.custom("SUGGESTION", server, suggestion_id).reason():
                return await ctx.send("This suggestion already has a reason.")
            content, embed = await self._build_suggestion(
                ctx, ctx.author.id, ctx.guild.id, suggestion_id, is_global
            )
            embed.add_field(name="Reason:", value=reason, inline=False)
            msg = await channel.fetch_message(id=msg_id)
            if msg:
                await msg.edit(content=content, embed=embed)
        await self.config.custom("SUGGESTION", server, suggestion_id).reason.set(True)
        await self.config.custom("SUGGESTION", server, suggestion_id).rtext.set(reason)
        await ctx.tick()

    @checks.admin_or_permissions(administrator=True)
    @commands.command()
    @commands.guild_only()
    async def showsuggestion(
        self,
        ctx: commands.Context,
        suggestion_id: int,
        is_global: Optional[bool] = False,
    ):
        """Show a suggestion."""
        content, embed = await self._build_suggestion(
            ctx, ctx.author.id, ctx.guild.id, suggestion_id, is_global
        )
        await ctx.send(content=content, embed=embed)

    @checks.admin_or_permissions(administrator=True)
    @commands.group(autohelp=True)
    @commands.guild_only()
    async def setsuggest(self, ctx: commands.Context):
        """Suggestion settings"""
        pass

    @checks.bot_has_permissions(manage_channels=True)
    @setsuggest.command(name="setup")
    async def setsuggest_setup(self, ctx: commands.Context):
        """ Go through the initial setup process. """
        await self.config.guild(ctx.guild).same.set(False)
        await self.config.guild(ctx.guild).suggest_id.set(None)
        await self.config.guild(ctx.guild).approve_id.set(None)
        await self.config.guild(ctx.guild).reject_id.set(None)
        await self.config.guild(ctx.guild).delete_suggestion.set(True)

        predchan = MessagePredicate.valid_text_channel(ctx)
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(send_messages=False),
            ctx.guild.me: discord.PermissionOverwrite(send_messages=True),
        }

        msg = await ctx.send("Do you already have your channel(s) done?")
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        try:
            await self.bot.wait_for("reaction_add", timeout=30, check=pred)
        except asyncio.TimeoutError:
            await msg.delete()
            return await ctx.send("You took too long. Try again, please.")
        if not pred.result:
            await msg.delete()
            suggestions = get(ctx.guild.text_channels, name="suggestions")
            if not suggestions:
                suggestions = await ctx.guild.create_text_channel(
                    "suggestions", overwrites=overwrites, reason="Suggestion cog setup"
                )
            await self.config.guild(ctx.guild).suggest_id.set(suggestions.id)

            msg = await ctx.send(
                "Do you want to use the same channel for approved and rejected suggestions? (If yes, they won't be reposted anywhere, only their title will change accordingly.)"
            )
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            try:
                await self.bot.wait_for("reaction_add", timeout=30, check=pred)
            except asyncio.TimeoutError:
                await msg.delete()
                return await ctx.send("You took too long. Try again, please.")
            if pred.result:
                await msg.delete()
                await self.config.guild(ctx.guild).same.set(True)
            else:
                await msg.delete()
                approved = get(ctx.guild.text_channels, name="approved-suggestions")
                if not approved:
                    msg = await ctx.send(
                        "Do you want to have an approved suggestions channel?"
                    )
                    start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                    pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                    try:
                        await self.bot.wait_for("reaction_add", timeout=30, check=pred)
                    except asyncio.TimeoutError:
                        await msg.delete()
                        return await ctx.send("You took too long. Try again, please.")
                    if pred.result:
                        approved = await ctx.guild.create_text_channel(
                            "approved-suggestions",
                            overwrites=overwrites,
                            reason="Suggestion cog setup",
                        )
                        await self.config.guild(ctx.guild).approve_id.set(approved.id)
                    await msg.delete()
                else:
                    await self.config.guild(ctx.guild).approve_id.set(approved.id)
                rejected = get(ctx.guild.text_channels, name="rejected-suggestions")
                if not rejected:
                    msg = await ctx.send(
                        "Do you want to have a rejected suggestions channel?"
                    )
                    start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                    pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                    try:
                        await self.bot.wait_for("reaction_add", timeout=30, check=pred)
                    except asyncio.TimeoutError:
                        await msg.delete()
                        return await ctx.send("You took too long. Try again, please.")
                    if pred.result:
                        rejected = await ctx.guild.create_text_channel(
                            "rejected-suggestions",
                            overwrites=overwrites,
                            reason="Suggestion cog setup",
                        )
                        await self.config.guild(ctx.guild).reject_id.set(rejected.id)
                    await msg.delete()
                else:
                    await self.config.guild(ctx.guild).reject_id.set(rejected.id)

                msg = await ctx.send(
                    "Do you want to keep suggestions in the original suggestion channel after being approved/rejected?"
                )
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await self.bot.wait_for("reaction_add", timeout=30, check=pred)
                except asyncio.TimeoutError:
                    await msg.delete()
                    return await ctx.send("You took too long. Try again, please.")
                if pred.result:
                    await self.config.guild(ctx.guild).delete_suggestion.set(False)
                await msg.delete()
        else:
            await msg.delete()
            msg = await ctx.send(
                "Mention the channel where you want me to post new suggestions."
            )
            try:
                await self.bot.wait_for("message", timeout=30, check=predchan)
            except asyncio.TimeoutError:
                await msg.delete()
                return await ctx.send("You took too long. Try again, please.")
            suggestion = predchan.result
            await self.config.guild(ctx.guild).suggest_id.set(suggestion.id)
            await msg.delete()

            msg = await ctx.send(
                "Do you want to use the same channel for approved and rejected suggestions? (If yes, they won't be reposted anywhere, only their title will change accordingly.)"
            )
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            try:
                await self.bot.wait_for("reaction_add", timeout=30, check=pred)
            except asyncio.TimeoutError:
                await msg.delete()
                return await ctx.send("You took too long. Try again, please.")
            if pred.result:
                await msg.delete()
                await self.config.guild(ctx.guild).same.set(True)
            else:
                await msg.delete()
                msg = await ctx.send(
                    "Do you want to have an approved suggestions channel?"
                )
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await self.bot.wait_for("reaction_add", timeout=30, check=pred)
                except asyncio.TimeoutError:
                    await msg.delete()
                    return await ctx.send("You took too long. Try again, please.")
                if pred.result:
                    await msg.delete()
                    msg = await ctx.send(
                        "Mention the channel where you want me to post approved suggestions."
                    )
                    try:
                        await self.bot.wait_for("message", timeout=30, check=predchan)
                    except asyncio.TimeoutError:
                        await msg.delete()
                        return await ctx.send("You took too long. Try again, please.")
                    approved = predchan.result
                    await self.config.guild(ctx.guild).approve_id.set(approved.id)
                await msg.delete()

                msg = await ctx.send(
                    "Do you want to have a rejected suggestions channel?"
                )
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await self.bot.wait_for("reaction_add", timeout=30, check=pred)
                except asyncio.TimeoutError:
                    await msg.delete()
                    return await ctx.send("You took too long. Try again, please.")
                if pred.result:
                    await msg.delete()
                    msg = await ctx.send(
                        "Mention the channel where you want me to post rejected suggestions."
                    )
                    try:
                        await self.bot.wait_for("message", timeout=30, check=predchan)
                    except asyncio.TimeoutError:
                        await msg.delete()
                        return await ctx.send("You took too long. Try again, please.")
                    rejected = predchan.result
                    await self.config.guild(ctx.guild).reject_id.set(rejected.id)
                await msg.delete()

                msg = await ctx.send(
                    "Do you want to keep suggestions in the original suggestion channel after being approved/rejected?"
                )
                start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(msg, ctx.author)
                try:
                    await self.bot.wait_for("reaction_add", timeout=30, check=pred)
                except asyncio.TimeoutError:
                    await msg.delete()
                    return await ctx.send("You took too long. Try again, please.")
                if pred.result:
                    await self.config.guild(ctx.guild).delete_suggestion.set(False)
                await msg.delete()
        await ctx.send(
            "You have finished the setup! Please, move your channels to the category you want them in."
        )

    @checks.bot_has_permissions(add_reactions=True)
    @setsuggest.command(name="upemoji")
    async def setsuggest_upemoji(self, ctx: commands.Context, up_emoji: discord.Emoji = None):
        """ Set custom reactions emoji instead of ✅. """
        if not up_emoji:
            await self.config.guild(ctx.guild).up_emoji.set(None)
        else:
            try:
                await ctx.message.add_reaction(up_emoji)
            except discord.HTTPException:
                return await ctx.send("Uh oh, I cannot use that emoji.")
            await self.config.guild(ctx.guild).up_emoji.set(up_emoji.id)
        await ctx.tick()

    @checks.bot_has_permissions(add_reactions=True)
    @setsuggest.command(name="downemoji")
    async def setsuggest_downemoji(self, ctx: commands.Context, down_emoji: discord.Emoji = None):
        """ Set custom reactions emoji instead of ❎. """
        if not down_emoji:
            await self.config.guild(ctx.guild).up_emoji.set(None)
        else:
            try:
                await ctx.message.add_reaction(down_emoji)
            except discord.HTTPException:
                return await ctx.send("Uh oh, I cannot use that emoji.")
            await self.config.guild(ctx.guild).down_emoji.set(down_emoji.id)
        await ctx.tick()

    @checks.bot_has_permissions(manage_messages=True)
    @setsuggest.command(name="autodelete")
    async def setsuggest_autodelete(self, ctx: commands.Context, on_off: bool = None):
        """ Toggle whether after `[p]suggest`, the bot deletes the message. """
        target_state = (
            on_off if on_off else not (await self.config.guild(ctx.guild).delete_suggest())
        )
        await self.config.guild(ctx.guild).delete_suggest.set(target_state)
        if target_state:
            await ctx.send("Auto deletion is now enabled.")
        else:
            await ctx.send("Auto deletion is now disabled.")

    @setsuggest.group(autohelp=True)
    @checks.is_owner()
    @commands.guild_only()
    async def setglobal(self, ctx: commands.Context):
        """Global suggestions settings.

        There is nothing like approved or rejected channels because global suggestions are meant to be for the bot only and will only work if it is sent in a server where normal suggestions are disabled."""
        pass

    @setglobal.command(name="toggle")
    async def setsuggest_setglobal_toggle(
        self, ctx: commands.Context, on_off: bool = None
    ):
        """Toggle global suggestions. 
        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off if on_off else not (await self.config.toggle())
        )
        await self.config.toggle.set(target_state)
        if target_state:
            await ctx.send("Global suggestions are now enabled.")
        else:
            await ctx.send("Global suggestions are now disabled.")

    @setglobal.command(name="channel")
    async def setsuggest_setglobal_channel(
        self,
        ctx: commands.Context,
        server: discord.Guild = None,
        channel: discord.TextChannel = None,
    ):
        """Add channel where global suggestions should be sent."""
        if not server:
            server = ctx.guild
        if not channel:
            channel = ctx.channel
        await self.config.server_id.set(server.id)
        await self.config.channel_id.set(channel.id)
        await ctx.send(f"{channel.mention} has been saved for global suggestions.")

    @setglobal.command(name="ignore")
    async def setsuggest_setglobal_ignore(
        self, ctx: commands.Context, server: discord.Guild = None
    ):
        """ Ignore suggestions from the server. """
        if not server:
            server = ctx.guild
        if server.id not in await self.config.ignore():
            async with self.config.ignore() as ignore:
                ignore.append(server.id)
            await ctx.send(f"{server.name} has been added into the ignored list.")
        else:
            await ctx.send(f"{server.name} is already in the ignored list.")

    @setglobal.command(name="unignore")
    async def setsuggest_setglobal_unignore(
        self, ctx: commands.Context, server: discord.Guild = None
    ):
        """ Remove server from the ignored list. """
        if not server:
            server = ctx.guild
        if server.id in await self.config.ignore():
            async with self.config.ignore() as ignore:
                ignore.remove(server.id)
            await ctx.send(f"{server.name} has been removed from the ignored list.")
        else:
            await ctx.send(f"{server.name} already isn't in the ignored list.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        message = reaction.message
        if user.id == self.bot.user.id:
            return
        # server suggestions
        if message.channel.id == await self.config.guild(message.guild).suggest_id():
            for message_reaction in message.reactions:
                if message_reaction.emoji != reaction.emoji:
                    if user in await message_reaction.users().flatten():
                        await message_reaction.remove(user)

        # global suggestions
        if message.channel.id == await self.config.channel_id():
            for message_reaction in message.reactions:
                if message_reaction.emoji != reaction.emoji:
                    if user in await message_reaction.users().flatten():
                        await message_reaction.remove(user)

    async def _build_suggestion(
        self, ctx, author_id, server_id, suggestion_id, is_global
    ):
        if is_global:
            if await self.config.toggle():
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
            else:
                return await ctx.send("Global suggestions aren't enabled.")
        if not is_global:
            server = server_id
            if (
                await self.config.custom("SUGGESTION", server, suggestion_id).msg_id()
                != 0
            ):
                content = f"Suggestion #{suggestion_id}"
            else:
                return await ctx.send("Uh oh, that suggestion doesn't seem to exist.")
        op_info = await self.config.custom("SUGGESTION", server, suggestion_id).author()
        op_id = int(op_info[0])
        op = await self.bot.fetch_user(op_id)
        if op:
            op_name = op.name
            op_discriminator = op.discriminator
            op_avatar = op.avatar_url
        else:
            op_name = str(op_info[1])
            op_discriminator = int(op_info[2])
            op_avatar = ctx.guild.icon_url
        if not await self.config.custom("SUGGESTION", server, suggestion_id).finished():
            atext = f"Suggestion by {op_name}"
        else:
            if await self.config.custom("SUGGESTION", server, suggestion_id).approved():
                atext = f"Approved suggestion by {op_name}"
            else:
                if (
                    await self.config.custom(
                        "SUGGESTION", server, suggestion_id
                    ).rejected()
                ):
                    atext = f"Rejected suggestion by {op_name}"
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
                up_count = reaction.count - 1 # minus the bot
            if reaction.emoji == down_emoji:
                down_count = reaction.count - 1 # minus the bot

        results = str(up_count) + "x " + up_emoji + "\n" + str(down_count) + "x " + down_emoji
        return results

    async def _get_emojis(self, ctx):
        up_emoji = self.bot.get_emoji(await self.config.guild(ctx.guild).up_emoji())
        if not up_emoji:
            up_emoji = "✅"
        down_emoji = self.bot.get_emoji(await self.config.guild(ctx.guild).down_emoji())
        if not down_emoji:
            down_emoji = "❎"
        return up_emoji, down_emoji