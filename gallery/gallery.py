import asyncio
import discord

from typing import Any

from redbot.core import Config, checks, commands

from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class Gallery(Cog):
    """
    Gallery channels!
    """

    __author__ = "saurichable"
    __version__ = "1.0.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=564154651321346431, force_registration=True
        )

        self.config.register_guild(channels=[], whitelist=None)


    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_messages=True)
    async def addgallery(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Add a channel to the list of Gallery channels."""
        if channel.id not in await self.config.guild(ctx.guild).channels():
            async with self.config.guild(ctx.guild).channels() as channels:
                channels.append(channel.id)
            await ctx.send(f"{channel.mention} has been added into the Gallery channels list.")
        else:
            await ctx.send(f"{channel.mention} is already in the Gallery channels list.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_messages=True)
    async def rmgallery(
        self, ctx: commands.Context, channel: discord.TextChannel
    ):
        """Remove a channel from the list of Gallery channels."""
        if channel.id in await self.config.guild(ctx.guild).channels():
            async with self.config.guild(ctx.guild).channels() as channels:
                channels.remove(channel.id)
            await ctx.send(f"{channel.mention} has been removed from the Gallery channels list.")
        else:
            await ctx.send(f"{channel.mention} already isn't in the Gallery channels list.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @checks.bot_has_permissions(manage_messages=True)
    async def galleryrole(
        self, ctx: commands.Context, role: discord.Role=None
    ):
        """Add a whitelisted role."""
        if not role:
            await self.config.guild(ctx.guild).whitelist.set(None)
            await ctx.send(f"Whitelisted role has been deleted.")
        else:
            await self.config.guild(ctx.guild).whitelist.set(role.id)
            await ctx.send(f"{role.name} has been whitelisted.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if message.channel.id not in await self.config.guild(message.guild).channels():
            return
        if not message.attachments:
            rid = await self.config.guild(message.guild).whitelist()
            if rid is not None:
                role = message.guild.get_role(int(rid))
                if role is not None:
                    if role in message.author.roles:
                        return
                    else:
                        await message.delete()
                else:
                    await message.delete()
            else:
                await message.delete()