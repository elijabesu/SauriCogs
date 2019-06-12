import discord

from discord.utils import get

from redbot.core import commands, checks

from redbot.core.bot import Red
from typing import Any

Cog: Any = getattr(commands, "Cog", object)


class Forwarding(commands.Cog):
    """Forward messages to the bot owner, incl. pictures (max one per message).
    You can also DM someone as the bot with `[p]pm <user_ID> <message>`."""

    __author__ = "saurichable"
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot

    async def sendowner(self, embed2):
        await self.bot.is_owner(discord.Object(id=None))
        owner = self.bot.get_user(self.bot.owner_id)
        await owner.send(embed=embed2)

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.guild is not None:
            return
        if message.channel.recipient.id == self.bot.owner_id:
            return
        sender = message.author
        if message.author == self.bot.user:
            return
        else:
            if not message.attachments:
                embed = discord.Embed(
                    colour=discord.Colour.red(),
                    description=message.content,
                    timestamp=message.created_at,
                )
                embed.set_author(
                    name=message.author, icon_url=message.author.avatar_url
                )
                embed.set_footer(text=f"User ID: {message.author.id}")
                await sender.send("Message has been delivered.")
            else:
                embed = discord.Embed(
                    colour=discord.Colour.red(),
                    description=message.content,
                    timestamp=message.created_at,
                )
                embed.set_author(
                    name=message.author, icon_url=message.author.avatar_url
                )
                embed.set_image(url=message.attachments[0].url)
                embed.set_footer(text=f"User ID: {message.author.id}")
                await sender.send(
                    "Message has been delivered. Note that if you've added multiple attachments, I've sent only the first one."
                )
            await self.sendowner(embed)

    @commands.command()
    @checks.is_owner()
    async def pm(self, ctx: commands.Context, user_id: int, *, message: str):
        """PMs a person."""
        destination = discord.utils.get(ctx.bot.get_all_members(), id=user_id)
        if destination is None:
            await ctx.send(
                "Invalid ID or user not found. You can only send messages to people I share a server with."
            )
            return
        await destination.send(message)
        await ctx.send("Sent message to {}.".format(destination))

    @checks.is_owner()
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(add_reactions=True)
    async def self(self, ctx: commands.Context, *, message: str):
        """Send yourself a DM. Owner command only."""
        author = ctx.author
        await author.send(message)
        await ctx.tick()
