import discord

from discord.utils import get

from redbot.core import Config, commands, checks

from typing import Union, Optional


class Forwarding(commands.Cog):
    """Forward messages to the bot owner, incl. pictures (max one per message).
    You can also DM someone as the bot with `[p]pm <user_ID> <message>`."""

    __author__ = "saurichable"
    __version__ = "2.3.2"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=5412156465899465526156, force_registration=True
        )
        self.config.register_global(
            guild_id=0, channel_id=0, ping_role_id=0, ping_user_id=0
        )

    async def _send_to(self, embed):
        guild = self.bot.get_guild(await self.config.guild_id())
        if not guild:
            return await self._send_to_owners(embed)
        channel = guild.get_channel(await self.config.channel_id())
        if not channel:
            return await self._send_to_owners(embed)
        ping_role = guild.get_role(await self.config.ping_role_id())
        ping_user = guild.get_member(await self.config.ping_user_id())
        if not ping_role:
            if not ping_user:
                return await channel.send(embed=embed)
            return await channel.send(content=f"{ping_user.mention}", embed=embed)
        if not ping_role.mentionable:
            await ping_role.edit(mentionable=True)
            await channel.send(content=f"{ping_role.mention}", embed=embed)
            await ping_role.edit(mentionable=False)
        else:
            await channel.send(content=f"{ping_role.mention}", embed=embed)

    async def _send_to_owners(self, embed):
        for owner_id in self.bot.owner_ids:
            await self.bot.get_user(owner_id).send(embed=embed)

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.guild:
            return
        if message.channel.recipient.id in self.bot.owner_ids:
            return
        if message.author == self.bot.user:
            return
        if not (await self.bot.allowed_by_whitelist_blacklist(message.author)):
            return
        if not message.attachments:
            embed = discord.Embed(
                colour=discord.Colour.red(),
                description=message.content,
                timestamp=message.created_at,
            )
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            embed.set_footer(text=f"User ID: {message.author.id}")
            await message.author.send("Message has been delivered.")
        else:
            embed = discord.Embed(
                colour=discord.Colour.red(),
                description=message.content,
                timestamp=message.created_at,
            )
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)
            embed.set_image(url=message.attachments[0].url)
            embed.set_footer(text=f"User ID: {message.author.id}")
            await message.author.send(
                "Message has been delivered. Note that if you've added multiple attachments, I've sent only the first one."
            )
        await self._send_to(embed)

    @commands.command()
    @checks.admin()
    async def pm(self, ctx: commands.Context, user_id: int, *, message: str):
        """PMs a person."""
        destination = get(ctx.bot.get_all_members(), id=user_id)
        if not destination:
            return await ctx.send(
                "Invalid ID or user not found. You can only send messages to people I share a server with."
            )
        await destination.send(message)
        await ctx.send(f"Sent message to {destination}.")

    @checks.admin()
    @commands.command()
    @commands.guild_only()
    @checks.bot_has_permissions(add_reactions=True)
    async def self(self, ctx: commands.Context, *, message: str):
        """Send yourself a DM. Owner command only."""
        await ctx.author.send(message)
        await ctx.tick()

    @commands.group()
    @checks.is_owner()
    @commands.guild_only()
    async def setforward(self, ctx: commands.Context):
        """Configuration commands for forwarding."""
        pass

    @setforward.command(name="channel")
    async def setforward_channel(
            self, ctx: commands.Context, *, channel: Optional[discord.TextChannel]
    ):
        """Set a channel in the current guild to be used for forwarding."""
        if channel:
            await self.config.guild_id.set(ctx.guild.id)
            await self.config.channel_id.set(channel.id)
            await ctx.send(f"I will forward all DMs to {channel.mention}.")
        else:
            await self.config.guild_id.clear()
            await self.config.channel_id.clear()
            await ctx.send("I will forward all DMs to you.")

    @setforward.command(name="ping")
    async def setforward_ping(
        self, ctx: commands.Context, *, ping: Union[discord.Role, discord.Member, None]
    ):
        """Set a role or a member to be pinged for forwarding."""
        if ping:
            if isinstance(ping, discord.Role):
                await self.config.ping_role_id.set(ping.id)
            else:
                await self.config.ping_user_id(ping.id)
            await ctx.send(f"I will ping {ping.name}.\n"
            f"Remember to `{ctx.clean_prefix}setforward channel`")
        else:
            await self.config.ping_role_id.clear()
            await self.config.ping_user_id.clear()
            await ctx.send("I will not ping any role nor member.")
