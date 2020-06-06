import asyncio
import discord

from typing import Any
from discord.utils import get

from redbot.core import Config, checks, commands
from redbot.core.utils.predicates import MessagePredicate

from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class Lock(Cog):
    """
    Lock `@everyone` from sending messages.
    Use `[p]locksetup` first.
    """

    __author__ = "saurichable"
    __version__ = "1.0.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=36546565165464, force_registration=True
        )

        default_guild = {"moderator": None, "everyone": True, "ignore": []}

        self.config.register_guild(**default_guild)

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def locksetup(self, ctx: commands.Context):
        """ Go through the initial setup process. """
        await ctx.send("Do you use roles to access channels? (yes/no)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        if not pred.result:
            await self.config.guild(ctx.guild).everyone.set(True)
        else:
            await self.config.guild(ctx.guild).everyone.set(False)
        await ctx.send("What is your Moderator role?")
        role = MessagePredicate.valid_role(ctx)
        try:
            await self.bot.wait_for("message", timeout=30, check=role)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        mod_role = role.result
        await self.config.guild(ctx.guild).moderator.set(str(mod_role))

        await ctx.send("You have finished the setup!")

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def lockignore(self, ctx: commands.Context, new_channel: discord.TextChannel):
        """ Ignore a channel during server lock. """
        if new_channel.id not in await self.config.guild(ctx.guild).ignore():
            async with self.config.guild(ctx.guild).ignore() as ignore:
                ignore.append(new_channel.id)
            await ctx.send(
                f"{new_channel.mention} has been added into the ignored channels list."
            )
        else:
            await ctx.send(
                f"{new_channel.mention} is already in the ignored channels list."
            )

    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.command()
    async def lockunignore(
        self, ctx: commands.Context, new_channel: discord.TextChannel
    ):
        """ Remove channels from the ignored list. """
        if new_channel.id not in await self.config.guild(ctx.guild).ignore():
            await ctx.send(
                f"{new_channel.mention} already isn't in the ignored channels list."
            )
        else:
            async with self.config.guild(ctx.guild).ignore() as ignore:
                ignore.remove(new_channel.id)
            await ctx.send(
                f"{new_channel.mention} has been removed from the ignored channels list."
            )

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        """ Lock `@everyone` from sending messages."""
        everyone = get(ctx.guild.roles, name="@everyone")
        name_moderator = await self.config.guild(ctx.guild).moderator()
        mods = get(ctx.guild.roles, name=name_moderator)
        which = await self.config.guild(ctx.guild).everyone()

        if not name_moderator:
            return await ctx.send(
                "Uh oh. Looks like your Admins haven't setup this yet."
            )
        if which:
            await ctx.channel.set_permissions(
                everyone, read_messages=True, send_messages=False
            )
        else:
            await ctx.channel.set_permissions(
                everyone, read_messages=False, send_messages=False
            )
        await ctx.channel.set_permissions(mods, read_messages=True, send_messages=True)
        await ctx.send(":lock: Channel locked. Only Moderators can type.")

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        """ Unlock the channel for `@everyone`. """
        everyone = get(ctx.guild.roles, name="@everyone")
        name_moderator = await self.config.guild(ctx.guild).moderator()
        which = await self.config.guild(ctx.guild).everyone()

        if not name_moderator:
            return await ctx.send(
                "Uh oh. Looks like your Admins haven't setup this yet."
            )
        if which:
            await ctx.channel.set_permissions(
                everyone, read_messages=True, send_messages=True
            )
        else:
            await ctx.channel.set_permissions(
                everyone, read_messages=False, send_messages=True
            )
        await ctx.send(":unlock: Channel unlocked.")

    @checks.mod_or_permissions(manage_roles=True)
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(manage_channels=True)
    async def lockserver(self, ctx: commands.Context, confirmation: bool = False):
        """ Lock `@everyone` from sending messages in the entire server."""
        if not confirmation:
            return await ctx.send(
                "This will overwrite every channel's permissions.\n"
                f"If you're sure, type `{ctx.clean_prefix}lockserver yes` (you can set an alias for this so I don't ask you every time)."
            )
        async with ctx.typing():
            everyone = get(ctx.guild.roles, name="@everyone")
            name_moderator = await self.config.guild(ctx.guild).moderator()
            mods = get(ctx.guild.roles, name=name_moderator)
            which = await self.config.guild(ctx.guild).everyone()
            ignore = await self.config.guild(ctx.guild).ignore()

            if not name_moderator:
                return await ctx.send(
                    "Uh oh. Looks like your Admins haven't setup this yet."
                )
            for channel in ctx.guild.text_channels:
                if channel.id in ignore:
                    continue
                if which:
                    await channel.set_permissions(
                        everyone, read_messages=True, send_messages=False
                    )
                else:
                    await channel.set_permissions(
                        everyone, read_messages=False, send_messages=False
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
        async with ctx.typing():
            everyone = get(ctx.guild.roles, name="@everyone")
            name_moderator = await self.config.guild(ctx.guild).moderator()
            which = await self.config.guild(ctx.guild).everyone()
            ignore = await self.config.guild(ctx.guild).ignore()

            if not name_moderator:
                return await ctx.send(
                    "Uh oh. Looks like your Admins haven't setup this yet."
                )
            for channel in ctx.guild.text_channels:
                if channel.id in ignore:
                    continue
                if which:
                    await channel.set_permissions(
                        everyone, read_messages=True, send_messages=True
                    )
                else:
                    await channel.set_permissions(
                        everyone, read_messages=False, send_messages=True
                    )
        await ctx.send(":unlock: Server unlocked.")
