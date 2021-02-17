import asyncio
import discord

from discord.utils import get, find

from redbot.core import Config, checks, commands

from redbot.core.bot import Red


class Counting(commands.Cog):
    """
    Counting channel!
    """

    __author__ = "saurichable"
    __version__ = "1.3.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1564646215646, force_registration=True
        )

        self.config.register_guild(
            channel=0,
            previous=0,
            goal=0,
            last=0,
            whitelist=None,
            warning=False,
            seconds=0,
            allow_text=False,
            topic=True,
        )

    @checks.admin_or_permissions(administrator=True)
    @checks.bot_has_permissions(manage_channels=True, manage_messages=True)
    @commands.group(autohelp=True)
    @commands.guild_only()
    async def setcount(self, ctx: commands.Context):
        """Counting settings"""
        pass

    @setcount.command(name="channel")
    async def setcount_channel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set the counting channel.

        If channel isn't provided, it will delete the current channel."""
        if not channel:
            await self.config.guild(ctx.guild).channel.set(0)
            return await ctx.send("Channel removed.")
        await self.config.guild(ctx.guild).channel.set(channel.id)
        goal = await self.config.guild(ctx.guild).goal()
        if await self.config.guild(ctx.guild).topic():
            await self._set_topic(0, goal, 1, channel)
        await ctx.send(f"{channel.name} has been set for counting.")

    @setcount.command(name="goal")
    async def setcount_goal(self, ctx: commands.Context, goal: int = 0):
        """Set the counting goal.

        If goal isn't provided, it will be deleted."""
        if not goal:
            await self.config.guild(ctx.guild).goal.set(0)
            return await ctx.send("Goal removed.")
        await self.config.guild(ctx.guild).goal.set(goal)
        await ctx.send(f"Goal set to {goal}.")

    @setcount.command(name="start")
    async def setcount_start(self, ctx: commands.Context, number: int):
        """Set the starting number."""
        c_id = await self.config.guild(ctx.guild).channel()
        if c_id == 0:
            return await ctx.send(
                f"Set the channel with `{ctx.clean_prefix}setcount channel <channel>`, please."
            )
        channel = get(ctx.guild.text_channels, id=c_id)
        if not channel:
            return await ctx.send(
                f"Set the channel with `{ctx.clean_prefix}setcount channel <channel>`, please."
            )
        await self.config.guild(ctx.guild).previous.set(number)
        await self.config.guild(ctx.guild).last.set(0)
        goal = await self.config.guild(ctx.guild).goal()
        next_number = number + 1
        if await self.config.guild(ctx.guild).topic():
            await self._set_topic(number, goal, next_number, channel)
        await channel.send(number)
        if c_id != ctx.channel.id:
            await ctx.send(f"Counting start set to {number}.")

    @setcount.command(name="reset")
    async def setcount_reset(self, ctx: commands.Context, confirmation: bool = False):
        """Reset the counter and start from 0 again!"""
        if not confirmation:
            return await ctx.send(
                "This will reset the ongoing counting. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}setcount reset yes`."
            )
        p = await self.config.guild(ctx.guild).previous()
        if p == 0:
            return await ctx.send("The counting hasn't even started.")
        c_id = await self.config.guild(ctx.guild).channel()
        if c_id == 0:
            return await ctx.send(
                f"Set the channel with `{ctx.clean_prefix}countchannel <channel>`, please."
            )
        c = get(ctx.guild.text_channels, id=c_id)
        if not c:
            return await ctx.send(
                f"Set the channel with `{ctx.clean_prefix}countchannel <channel>`, please."
            )
        await self.config.guild(ctx.guild).previous.set(0)
        await self.config.guild(ctx.guild).last.set(0)
        await c.send("Counting has been reset.")
        goal = await self.config.guild(ctx.guild).goal()
        if await self.config.guild(ctx.guild).topic():
            await self._set_topic(0, goal, 1, c)
        if c_id != ctx.channel.id:
            await ctx.send("Counting has been reset.")

    @setcount.command(name="role")
    async def setcount_role(self, ctx: commands.Context, role: discord.Role = None):
        """Add a whitelisted role."""
        if not role:
            await self.config.guild(ctx.guild).whitelist.set(None)
            await ctx.send(f"Whitelisted role has been deleted.")
        else:
            await self.config.guild(ctx.guild).whitelist.set(role.id)
            await ctx.send(f"{role.name} has been whitelisted.")

    @setcount.command(name="warnmsg")
    async def setcount_warnmsg(
        self, ctx: commands.Context, on_off: bool = None, seconds: int = 0
    ):
        """Toggle a warning message.

        If `on_off` is not provided, the state will be flipped.
        Optionally add how many seconds the bot should wait before deleting the message (0 for not deleting)."""
        target_state = (
            on_off
            if on_off
            else not (await self.config.guild(ctx.guild).warning())
        )
        await self.config.guild(ctx.guild).warning.set(target_state)
        if target_state:
            if seconds < 0:
                seconds = 0
            await self.config.guild(ctx.guild).seconds.set(seconds)
            if seconds == 0:
                await ctx.send("Warning messages are now enabled.")
            else:
                await ctx.send(
                    f"Warning messages are now enabled, will be deleted after {seconds} seconds."
                )
        else:
            await ctx.send("Warning messages are now disabled.")

    @setcount.command(name="topic")
    async def setcount_topic(self, ctx: commands.Context, on_off: bool = None):
        """Toggle counting channel's topic changing.

        If `on_off` is not provided, the state will be flipped.="""
        target_state = (
            on_off
            if on_off
            else not (await self.config.guild(ctx.guild).topic())
        )
        await self.config.guild(ctx.guild).topic.set(target_state)
        if target_state:
            await ctx.send("Updating the channel's topic is now enabled.")
        else:
            await ctx.send("Updating the channel's topic is now disabled.")

#    @setcount.command(name="allowtext")
#    async def setcount_allowtext(self, ctx: commands.Context, on_off: bool = None):
#        """Toggle allowing text AFTER the number.
#
#        If `on_off` is not provided, the state will be flipped."""
#        target_state = (
#            on_off
#            if on_off
#            else not (await self.config.guild(ctx.guild).allow_text())
#        )
#        await self.config.guild(ctx.guild).allow_text.set(target_state)
#        if target_state:
#            await ctx.send("Text in messages is now allowed.")
#        else:
#            await ctx.send("Text in messages is no longer allowed.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild:
            return
        if message.channel.id != await self.config.guild(message.guild).channel():
            return
        if message.author.id == self.bot.user.id:
            return
        last_id = await self.config.guild(message.guild).last()
        previous = await self.config.guild(message.guild).previous()
        next_number = previous + 1
        goal = await self.config.guild(message.guild).goal()
        warning = await self.config.guild(message.guild).warning()
        seconds = await self.config.guild(message.guild).seconds()
        if message.author.id != last_id:
            try:
                now = int(message.content)
                if now - 1 == previous:
                    await self.config.guild(message.guild).previous.set(now)
                    await self.config.guild(message.guild).last.set(message.author.id)
                    n = now + 1
                    if await self.config.guild(message.guild).topic():
                        return await self._set_topic(now, goal, n, message.channel)
                    return
            except (TypeError, ValueError):
                pass
#                if await self.config.guild(message.guild).allow_text():
#                    nums = [int(i) for i in message.content.split() if i.isdigit()]
#                    if now != []:
#                        now = nums[0]
#                        if now - 1 == previous:
#                            await self.config.guild(message.guild).previous.set(now)
#                            await self.config.guild(message.guild).last.set(
#                                message.author.id
#                            )
#                            n = now + 1
#                            return await self._set_topic(now, goal, n, message.channel)
#                        pass
#                    else:
#                        pass
        rid = await self.config.guild(message.guild).whitelist()
        if rid:
            role = message.guild.get_role(int(rid))
            if role:
                if role in message.author.roles:
                    return
        if warning:
            if message.author.id != last_id:
                warn_msg = await message.channel.send(
                    f"The next message in this channel must be {next_number}"
                )
            else:
                warn_msg = await message.channel.send(
                    f"You cannot count twice in a row."
                )
            if seconds != 0:
                await asyncio.sleep(seconds)
                await warn_msg.delete()
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.guild:
            return
        if message.channel.id != await self.config.guild(message.guild).channel():
            return
        try:
            deleted = int(message.content)
            previous = await self.config.guild(message.guild).previous()
            goal = await self.config.guild(message.guild).goal()
            if deleted == previous:
                s = str(deleted)
                if goal == 0:
                    msgs = await message.channel.history(limit=500).flatten()
                else:
                    msgs = await message.channel.history(limit=goal).flatten()
                msg = find(lambda m: m.content == s, msgs)
                if not msg:
                    p = deleted - 1
                    await self.config.guild(message.guild).previous.set(p)
                    await message.channel.send(deleted)
        except (TypeError, ValueError):
            return

    async def _set_topic(self, now, goal, n, channel):
        if goal == 0:
            await channel.edit(topic=f"Let's count! | Next message must be {n}!")
        else:
            if now < goal:
                await channel.edit(
                    topic=f"Let's count! | Next message must be {n}! | Goal is {goal}!"
                )
            elif now == goal:
                await channel.send("We did it, we reached the goal! :tada:")
                await channel.edit(topic=f"Goal reached! :tada:")
            else:
                return
