import requests
import asyncio
import discord

from typing import Any

from redbot.core import commands
from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class CustomAPI(Cog):
    """
    Custom API cog for api.saurich.com
    """

    __author__ = "saurichable"
    __version__ = "1.0.1"

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def next(self, ctx: commands.Context):
        """What and when is Ellie streaming next?"""
        r = requests.get("http://api.saurich.com/next.php")
        await ctx.send(r.text)

    @commands.command()
    async def today(self, ctx: commands.Context):
        """What and when is Ellie streaming today?"""
        r = requests.get("http://api.saurich.com/today.php")
        await ctx.send(r.text)

    @commands.command()
    async def tomorrow(self, ctx: commands.Context):
        """What and when is Ellie streaming tomorrow?"""
        r = requests.get("http://api.saurich.com/tomorrow.php")
        await ctx.send(r.text)