import discord

from pymongo import MongoClient
from datetime import datetime

from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red

client = MongoClient()
db = client["leveler"]


class LevelUpCookies(commands.Cog):
    """
    Set cookie rewards for users that level up!
    """

    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=646548484121544, force_registration=True
        )
        self.config.register_guild(rewards={})

    async def red_delete_data_for_user(self, *, requester, user_id):
        # nothing to delete
        return

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @checks.admin()
    @commands.guild_only()
    @commands.group(autohelp=True, aliases=["levelupcookies"])
    async def levelupcookiesset(self, ctx: commands.Context):
        """Various Level Up Cookies settings."""

    @levelupcookiesset.command(name="add")
    async def levelupcookiesset_add(
        self, ctx: commands.Context, level: int, cookies: int
    ):
        """Set a cookie reward for leveling up!"""
        await self.config.guild(ctx.guild).rewards.set_raw(
            level, value={"cookies": cookies}
        )
        await ctx.send(f"Gaining {level} will now give {cookies} :cookie:")

    @levelupcookiesset.command(name="del")
    async def levelupcookiesset_del(self, ctx: commands.Context, level: int):
        """Delete cookies for level."""
        await self.config.guild(ctx.guild).rewards.clear_raw(level)
        await ctx.send(f"Gaining {level} will now not give any :cookie:")

    @levelupcookiesset.command(name="show")
    async def levelupcookiesset_show(self, ctx: commands.Context):
        """Show how many cookies a level gives."""
        lst = []
        for level in await self.config.guild(ctx.guild).rewards.get_raw():
            l = await self.config.guild(ctx.guild).rewards.get_raw(level)
            c = l.get("cookies")
            name = "cookie" if int(c) == 1 else "cookies"
            text = f"Level {level} - {c} {name}"
            lst.append(text)
        desc = "Nothing to see here." if lst == [] else "\n".join(lst)
        page_list = list()
        for page in pagify(desc, delims=["\n"], page_length=1000):
            embed = discord.Embed(
                colour=await ctx.embed_colour(),
                description=page,
                timestamp=datetime.now(),
            )
            embed.set_author(
                name=f"Cookie rewards for {ctx.guild.name}",
                icon_url=ctx.guild.icon_url,
            )
            page_list.append(embed)
        await menu(ctx, page_list, DEFAULT_CONTROLS)

    @commands.Cog.listener()
    async def on_leveler_levelup(self, user, new_level):
        try:
            reward = await self.config.guild(user.guild).rewards.get_raw(int(new_level))
            if not reward:
                return
        except KeyError:
            return
        cookies = await self.bot.get_cog("Cookies").config.member(user).cookies()
        if cookies != 0:
            new_cookies = cookies + int(reward.get("cookies"))
        else:
            new_cookies = int(reward.get("cookies"))
        await self.bot.get_cog("Cookies").config.member(user).cookies.set(new_cookies)
