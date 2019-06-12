import asyncio
import discord
import random
import calendar

from typing import Any, Union
from discord.utils import get
from datetime import datetime

from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify, box
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)


class Cookies(Cog):
    """
    Collect cookies.
    """

    __author__ = "saurichable"
    __version__ = "1.0.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=16548964843212314, force_registration=True
        )
        self.config.register_guild(
            amount=1,
            minimum=0,
            maximum=0,
            cooldown=86400,
            stealing=False,
            stealcd=43200,
        )
        self.config.register_member(cookies=0, next_cookie=0, next_steal=0)
        self.config.register_role(cookies=0)

    @commands.command()
    @commands.guild_only()
    async def cookie(self, ctx: commands.Context):
        """Get your daily dose of cookies."""
        amount = int(await self.config.guild(ctx.guild).amount())
        cookies = int(await self.config.member(ctx.author).cookies())
        cur_time = calendar.timegm(ctx.message.created_at.utctimetuple())
        next_cookie = await self.config.member(ctx.author).next_cookie()
        if cur_time >= next_cookie:
            if amount != 0:
                cookies += amount
            else:
                minimum = int(await self.config.guild(ctx.guild).minimum())
                maximum = int(await self.config.guild(ctx.guild).maximum())
                amount = int(random.choice(list(range(minimum, maximum))))
                cookies += amount
            next_cookie = cur_time + await self.config.guild(ctx.guild).cooldown()
            await self.config.member(ctx.author).next_cookie.set(next_cookie)
            await self.config.member(ctx.author).cookies.set(cookies)
            await ctx.send(f"Here is your {amount} :cookie:")
        else:
            dtime = self.display_time(next_cookie - cur_time)
            await ctx.send(f"Uh oh, you have to wait {dtime}.")

    @commands.command()
    @commands.guild_only()
    async def steal(self, ctx: commands.Context, target: discord.Member = None):
        """Steal cookies from members."""
        cur_time = calendar.timegm(ctx.message.created_at.utctimetuple())
        next_steal = await self.config.member(ctx.author).next_steal()
        enabled = await self.config.guild(ctx.guild).stealing()
        author_cookies = int(await self.config.member(ctx.author).cookies())
        if enabled is False:
            return await ctx.send("Uh oh, stealing is disabled.")
        if cur_time < next_steal:
            dtime = self.display_time(next_steal - cur_time)
            return await ctx.send(f"Uh oh, you have to wait {dtime}.")
        if not target:
            target = random.choice(ctx.guild.members)
        if target.id == ctx.author.id:
            return await ctx.send("Uh oh, you can't steal from yourself.")
        target_cookies = int(await self.config.member(target).cookies())
        if target_cookies == 0:
            return await ctx.send(
                f"Uh oh, {target.display_name} doesn't have any :cookie:"
            )
        success_chance = random.randint(1, 100)
        if success_chance <= 90:
            cookies_stolen = int(target_cookies * 0.5)
            if cookies_stolen == 0:
                cookies_stolen = 1
            stolen = random.randint(1, cookies_stolen)
            target_cookies -= stolen
            author_cookies += stolen
            await ctx.send(f"You stole {stolen} :cookie: from {target.display_name}!")
        else:
            cookies_penalty = int(author_cookies * 0.25)
            if cookies_penalty == 0:
                cookies_penalty = 1
            penalty = random.randint(1, cookies_penalty)
            target_cookies += penalty
            author_cookies -= penalty
            await ctx.send(
                f"You got caught while trying to steal {target.display_name}'s :cookie:\nYour penalty is {penalty} :cookie: which they got!"
            )
        next_steal = cur_time + await self.config.guild(ctx.guild).stealcd()
        await self.config.member(target).cookies.set(target_cookies)
        await self.config.member(ctx.author).cookies.set(author_cookies)
        await self.config.member(ctx.author).next_steal.set(next_steal)

    @commands.command()
    @commands.guild_only()
    async def gift(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Gift someone some yummy cookies."""
        author_cookies = int(await self.config.member(ctx.author).cookies())
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        if target.id == ctx.author.id:
            return await ctx.send("Why would you do that?")
        if amount <= author_cookies:
            pass
        else:
            return await ctx.send("You don't have enough cookies yourself!")
        author_cookies -= amount
        await self.config.member(ctx.author).cookies.set(author_cookies)

        target_cookies = int(await self.config.member(target).cookies())
        target_cookies += amount
        await self.config.member(target).cookies.set(target_cookies)
        await ctx.send(
            "{0} has gifted {1} :cookie: to {2}".format(
                ctx.author.mention, amount, target.mention
            )
        )

    @commands.command(aliases=["jar"])
    @commands.guild_only()
    async def cookies(self, ctx: commands.Context, target: discord.Member = None):
        """Check how many cookies you have."""
        if not target:
            cookies = int(await self.config.member(ctx.author).cookies())
            await ctx.send("You have {0} :cookie:".format(cookies))
        else:
            cookies = int(await self.config.member(target).cookies())
            await ctx.send("{0} has {1} :cookie:".format(target.display_name, cookies))

    @commands.command(aliases=["cookieleaderboard"])
    @commands.guild_only()
    async def cookielb(self, ctx: commands.Context):
        """Display the server's cookie leaderboard."""
        data = await self.config.all_members(ctx.guild)
        accs = sorted(data, key=lambda x: data[x]["cookies"], reverse=True)
        list = []
        pos = 1
        pound_len = len(str(len(accs)))
        header = "{pound:{pound_len}}{score:{bar_len}}{name:2}\n".format(
            pound="#",
            name="Name",
            score="Cookies",
            pound_len=pound_len + 3,
            bar_len=pound_len + 9,
        )
        temp_msg = header
        for a_id in accs:
            a = get(ctx.guild.members, id=int(a_id))
            if a is None:
                continue
            name = a.display_name
            cookies = await self.config.member(a).cookies()
            if cookies == 0:
                continue
            score = "Cookies"
            if a_id != ctx.author.id:
                temp_msg += (
                    f"{f'{pos}.': <{pound_len+2}} {cookies: <{pound_len+8}} {name}\n"
                )
            else:
                temp_msg += (
                    f"{f'{pos}.': <{pound_len+2}} "
                    f"{cookies: <{pound_len+8}} "
                    f"<<{name}>>\n"
                )
            if pos % 10 == 0:
                list.append(box(temp_msg, lang="md"))
                temp_msg = header
            pos += 1
        if temp_msg != header:
            list.append(box(temp_msg, lang="md"))
        if list:
            if len(list) > 1:
                await menu(ctx, list, DEFAULT_CONTROLS)
            else:
                await ctx.send(list[0])
        else:
            empty = "Nothing to see here."
            await ctx.send(box(empty, lang="md"))

    @commands.group(autohelp=True)
    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def setcookies(self, ctx):
        """Admin settings for cookies."""
        pass

    @setcookies.command(name="amount")
    async def setcookies_amount(self, ctx: commands.Context, amount: int):
        """Set the amount of cookies members can obtain.

        If 0, members will get a random amount."""
        bot = self.bot
        await self.config.guild(ctx.guild).amount.set(amount)
        if amount < 0:
            return await ctx.send("Uh oh, the amount cannot be negative.")
        if amount != 0:
            await ctx.send("Members will receive {0} cookies.".format(amount))
        else:
            pred = MessagePredicate.valid_int(ctx)
            await ctx.send("What's the minimum amount of cookies members can obtain?")
            try:
                await bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            minimum = pred.result
            await self.config.guild(ctx.guild).minimum.set(minimum)

            await ctx.send("What's the maximum amount of cookies members can obtain?")
            try:
                await bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            maximum = pred.result
            await self.config.guild(ctx.guild).maximum.set(maximum)

            await ctx.send(
                "Members will receive a random amount of cookies between {0} and {1}.".format(
                    minimum, maximum
                )
            )

    @setcookies.command(name="cooldown", aliases=["cd"])
    async def setcookies_cd(self, ctx: commands.Context, seconds: int):
        """Set the cooldown for `[p]cookie`.

        This is in seconds! Default is 86400 seconds (24 hours)."""
        if seconds <= 0:
            return await ctx.send("Uh oh, cooldown has to be more than 0 seconds.")
        await self.config.guild(ctx.guild).cooldown.set(seconds)
        await ctx.send(f"Set the cooldown to {seconds} seconds.")

    @setcookies.command(name="stealcooldown", aliases=["stealcd"])
    async def setcookies_stealcd(self, ctx: commands.Context, seconds: int):
        """Set the cooldown for `[p]steal`.

        This is in seconds! Default is 43200 seconds (12 hours)."""
        if seconds <= 0:
            return await ctx.send("Uh oh, cooldown has to be more than 0 seconds.")
        await self.config.guild(ctx.guild).stealcd.set(seconds)
        await ctx.send(f"Set the cooldown to {seconds} seconds.")

    @setcookies.command(name="steal")
    async def setcookies_steal(self, ctx: commands.Context, on_off: bool = None):
        """Toggle cookie stealing for current server. 

        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off
            if on_off is not None
            else not (await self.config.guild(ctx.guild).stealing())
        )
        await self.config.guild(ctx.guild).stealing.set(target_state)
        if target_state:
            await ctx.send("Stealing is now enabled.")
        else:
            await ctx.send("Stealing is now disabled.")

    @setcookies.command(name="set")
    async def setcookies_set(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Set someone's amount of cookies."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        await self.config.member(target).cookies.set(amount)
        await ctx.send(
            "Set {0}'s balance to {1} :cookie:".format(target.mention, amount)
        )

    @setcookies.command(name="add")
    async def setcookies_add(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Add cookies to someone."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        target_cookies = int(await self.config.member(target).cookies())
        target_cookies += amount
        await self.config.member(target).cookies.set(target_cookies)
        await ctx.send(
            "Added {0} :cookie: to {1}'s balance.".format(amount, target.mention)
        )

    @setcookies.command(name="take")
    async def setcookies_take(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Take cookies away from someone."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        target_cookies = int(await self.config.member(target).cookies())
        if amount <= target_cookies:
            target_cookies -= amount
            await self.config.member(target).cookies.set(target_cookies)
            await ctx.send(
                "Took away {0} :cookie: from {1}'s balance.".format(
                    amount, target.mention
                )
            )
        else:
            await ctx.send("{0} doesn't have enough :cookies:".format(target.mention))

    @setcookies.command(name="reset")
    async def setcookies_reset(self, ctx: commands.Context, confirmation: bool = False):
        """Delete all cookies from all members."""
        if confirmation is False:
            return await ctx.send(
                "This will delete **all** cookies from all members. This action **cannot** be undone.\n"
                "If you're sure, type `{0}setcookies reset yes`.".format(
                    ctx.clean_prefix
                )
            )

        for member in ctx.guild.members:
            cookies = int(await self.config.member(member).cookies())
            if cookies != 0:
                await self.config.member(member).cookies.set(0)

        await ctx.send("All cookies have been deleted from all members.")

    @setcookies.group(autohelp=True)
    async def role(self, ctx):
        """Cookie rewards for roles."""
        pass

    @role.command(name="add")
    async def setcookies_role_add(
        self, ctx: commands.Context, role: discord.Role, amount: int
    ):
        """Set cookies for role."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        await self.config.role(role).cookies.set(amount)
        await ctx.send(f"Gaining {role.name} will now give {amount} :cookie:")

    @role.command(name="del")
    async def setcookies_role_del(self, ctx: commands.Context, role: discord.Role):
        """Delete cookies for role."""
        await self.config.role(role).cookies.set(0)
        await ctx.send(f"Gaining {role.name} will now not give any :cookie:")

    @role.command(name="show")
    async def setcookies_role_show(self, ctx: commands.Context, role: discord.Role):
        """Show how many cookies a role gives."""
        cookies = int(await self.config.role(role).cookies())
        await ctx.send(f"Gaining {role.name} gives {cookies} :cookie:")

    @commands.command()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def nostore(self, ctx):
        """Cookie store."""
        await ctx.send(
            f"Uh oh. Cookie store had to be made into a separate cog... You can install it by `{ctx.clean_prefix}cog install SauriCogs cookiestore`. Note that you will have to readd all items again.\n"
            f"*Replace `SauriCogs` with the name you gave when adding the repo.*"
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        b = set(before.roles)
        a = set(after.roles)
        after_roles = [list(a - b)][0]
        if after_roles:
            for role in after_roles:
                cookies = int(await self.config.role(role).cookies())
                if cookies != 0:
                    old_cookies = int(await self.config.member(after).cookies())
                    new_cookies = old_cookies + cookies
                    await self.config.member(after).cookies.set(new_cookies)

    @staticmethod
    def display_time(seconds, granularity=2):
        intervals = (  # Source: from economy.py
            (("weeks"), 604800),  # 60 * 60 * 24 * 7
            (("days"), 86400),  # 60 * 60 * 24
            (("hours"), 3600),  # 60 * 60
            (("minutes"), 60),
            (("seconds"), 1),
        )

        result = []

        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip("s")
                result.append("{} {}".format(value, name))
        return ", ".join(result[:granularity])
