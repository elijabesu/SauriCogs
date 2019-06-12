import asyncio
import discord

from typing import Any
from discord.utils import get, find
from datetime import datetime, timedelta

from redbot.core import Config, checks, commands
from redbot.core.utils.antispam import AntiSpam

from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class Counting(Cog):
    """
    Counting channel!
    """

    __author__ = "saurichable"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=1564646215646, force_registration=True
        )

        self.config.register_guild(channel=0, previous=0, goal=0)
        self.antispam = {}

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_channels=True)
    @checks.bot_has_permissions(manage_channels=True, manage_messages=True)
    async def countchannel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set the counting channel.

        If channel isn't provided, it will delete the current channel."""
        if not channel:
            await self.config.guild(ctx.guild).channel.set(0)
            return await ctx.send("Channel removed.")
        await self.config.guild(ctx.guild).channel.set(channel.id)
        goal = await self.config.guild(ctx.guild).goal()
        await self._set_topic(0, goal, 1, channel)
        await ctx.send(f"{channel.name} has been set for counting.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_channels=True)
    @checks.bot_has_permissions(manage_channels=True, manage_messages=True)
    async def countgoal(self, ctx: commands.Context, goal: int = 0):
        """Set the counting goal.

        If goal isn't provided, it will be deleted."""
        if not goal:
            await self.config.guild(ctx.guild).goal.set(0)
            return await ctx.send("Goal removed.")
        await self.config.guild(ctx.guild).goal.set(goal)
        await ctx.send(f"Goal set to {goal}.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_channels=True)
    @checks.bot_has_permissions(manage_channels=True, manage_messages=True)
    async def countreset(self, ctx: commands.Context, confirmation: bool = False):
        """Reset the counter and start from 0 again!"""
        if confirmation is False:
            return await ctx.send(
                "This will reset the ongoing counting. This action **cannot** be undone.\n"
                "If you're sure, type `{0}countreset yes`.".format(ctx.clean_prefix)
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
        if c is None:
            return await ctx.send(
                f"Set the channel with `{ctx.clean_prefix}countchannel <channel>`, please."
            )
        await self.config.guild(ctx.guild).previous.set(0)
        await c.send("Counting has been reset.")
        goal = await self.config.guild(ctx.guild).goal()
        await self._set_topic(0, goal, 1, c)
        await ctx.send("Counting has been reset.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        counting = await self.config.guild(message.guild).channel()
        if counting == 0:
            return
        if message.channel.id != counting:
            return
        if message.guild not in self.antispam:
            self.antispam[message.guild] = {}
        if message.author not in self.antispam[message.guild]:
            self.antispam[message.guild][message.author] = AntiSpam(
                [(timedelta(hours=1), 1)]
            )
        if self.antispam[message.guild][message.author].spammy:
            return await message.delete()
        try:
            now = int(message.content)
            previous = await self.config.guild(message.guild).previous()
            goal = await self.config.guild(message.guild).goal()
            if now - 1 == previous:
                await self.config.guild(message.guild).previous.set(now)
                n = now + 1
                await self._set_topic(now, goal, n, message.channel)
                self.antispam[message.guild][message.author].stamp()
            else:
                if message.author.id == self.bot.user.id:
                    return
                else:
                    await message.delete()
        except:
            if message.author.id == self.bot.user.id:
                return
            else:
                await message.delete()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild is None:
            return
        counting = await self.config.guild(message.guild).channel()
        if counting == 0:
            return
        if message.channel.id != counting:
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
                if msg is None:
                    p = deleted - 1
                    await self.config.guild(message.guild).previous.set(p)
                    await message.channel.send(deleted)
                else:
                    return
            else:
                return
        except:
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
