import asyncio
import discord
import random
import calendar

from typing import Any, Union
from discord.utils import get
from datetime import datetime

from redbot.core import Config, checks, commands, bank
from redbot.core.utils.chat_formatting import pagify, box
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red

_MAX_BALANCE = 2 ** 63 - 1


class Cookies(commands.Cog):
    """
    Collect cookies.
    """

    __author__ = "saurichable"
    __version__ = "1.1.4"

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
            rate=0.5,
        )
        self.config.register_member(cookies=0, next_cookie=0, next_steal=0)
        self.config.register_role(cookies=0, multiplier=1)

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
                multipliers = []
                for role in ctx.author.roles:
                    role_multiplier = await self.config.role(role).multiplier()
                    if not role_multiplier:
                        role_multiplier = 1
                    multipliers.append(role_multiplier)
                cookies += (amount * max(multipliers)) 
            else:
                minimum = int(await self.config.guild(ctx.guild).minimum())
                maximum = int(await self.config.guild(ctx.guild).maximum())
                amount = int(random.choice(list(range(minimum, maximum))))
                cookies += amount
            if self._max_balance_check(cookies):
                return await ctx.send(
                    "Uh oh, you have reached the maximum amount of cookies that you can put in your bag. :frowning:"
                )
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

        if not enabled:
            return await ctx.send("Uh oh, stealing is disabled.")
        if cur_time < next_steal:
            dtime = self.display_time(next_steal - cur_time)
            return await ctx.send(f"Uh oh, you have to wait {dtime}.")

        if not target:
            ids = await self._get_ids(ctx)
            while not target:
                target_id = random.choice(ids)
                target = ctx.guild.get_member(target_id)
        if target.id == ctx.author.id:
            return await ctx.send("Uh oh, you can't steal from yourself.")
        target_cookies = int(await self.config.member(target).cookies())
        if target_cookies == 0:
            return await ctx.send(
                f"Uh oh, {target.display_name} doesn't have any :cookie:"
            )

        await self.config.member(ctx.author).next_steal.set(cur_time + await self.config.guild(ctx.guild).stealcd())

        success_chance = random.randint(1, 100)
        if success_chance > 90:
            cookies_stolen = int(target_cookies * 0.5)
            if cookies_stolen == 0:
                cookies_stolen = 1
            stolen = random.randint(1, cookies_stolen)
            author_cookies += stolen
            if self._max_balance_check(author_cookies):
                return await ctx.send(
                    "Uh oh, you have reached the maximum amount of cookies that you can put in your bag. :frowning:\n"
                    f"You stole any cookie of {target.display_name}."
                )
            target_cookies -= stolen
            await ctx.send(f"You stole {stolen} :cookie: from {target.display_name}!")
        else:
            cookies_penalty = int(author_cookies * 0.25)
            if cookies_penalty == 0:
                cookies_penalty = 1
            if cookies_penalty > 0:
                penalty = random.randint(1, cookies_penalty)
                if author_cookies < penalty:
                    penalty = author_cookies
                if self._max_balance_check(target_cookies + penalty):
                    return await ctx.send(
                        f"Uh oh, you got caught while trying to steal {target.display_name}'s :cookie:\n"
                        f"{target.display_name} has reached the maximum amount of cookies, "
                        "so you haven't lost any."
                    )
                author_cookies -= penalty
                target_cookies += penalty
                await ctx.send(
                    f"You got caught while trying to steal {target.display_name}'s :cookie:\nYour penalty is {penalty} :cookie: which they got!"
                )
            else:
                return await ctx.send(
                    f"Uh oh, you got caught while trying to steal {target.display_name}'s :cookie:\n"
                    f"You don't have any cookies, so you haven't lost any."
                )
        await self.config.member(target).cookies.set(target_cookies)
        await self.config.member(ctx.author).cookies.set(author_cookies)

    @commands.command()
    @commands.guild_only()
    async def gift(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Gift someone some yummy cookies."""
        author_cookies = int(await self.config.member(ctx.author).cookies())
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        if target.id == ctx.author.id:
            return await ctx.send("Why would you do that?")
        if amount > author_cookies:
            return await ctx.send("You don't have enough cookies yourself!")
        target_cookies = int(await self.config.member(target).cookies())
        target_cookies += amount
        if self._max_balance_check(target_cookies):
            return await ctx.send(
                f"Uh oh, {target.display_name} has reached the maximum amount of cookies that they can have in their bag. :frowning:"
            )
        author_cookies -= amount
        await self.config.member(ctx.author).cookies.set(author_cookies)
        await self.config.member(target).cookies.set(target_cookies)
        await ctx.send(
            f"{ctx.author.mention} has gifted {amount} :cookie: to {target.mention}"
        )

    @commands.command(aliases=["jar"])
    @commands.guild_only()
    async def cookies(self, ctx: commands.Context, target: discord.Member = None):
        """Check how many cookies you have."""
        if not target:
            cookies = int(await self.config.member(ctx.author).cookies())
            await ctx.send(f"You have {cookies} :cookie:")
        else:
            cookies = int(await self.config.member(target).cookies())
            await ctx.send(f"{target.display_name} has {cookies} :cookie:")

    @commands.command()
    @commands.guild_only()
    async def cookieexchange(self, ctx: commands.Context, amount: int):
        """Exchange currency into cookies."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")

        if not await bank.can_spend(ctx.author, amount):
            return await ctx.send(f"Uh oh, you cannot afford this.")
        await bank.withdraw_credits(ctx.author, amount)

        rate = await self.config.guild(ctx.guild).rate()
        new_cookies = amount * rate

        cookies = await self.config.member(ctx.author).cookies()
        cookies += new_cookies
        await self.config.member(ctx.author).cookies.set(cookies)
        currency = await bank.get_currency_name(ctx.guild)
        await ctx.send(f"You have exchanged {amount} {currency} and got {new_cookies} :cookie:\nYou now have {cookies} :cookie:")

    @commands.command(aliases=["cookieleaderboard"])
    @commands.guild_only()
    async def cookielb(self, ctx: commands.Context):
        """Display the server's cookie leaderboard."""
        ids = await self._get_ids(ctx)
        lst = []
        pos = 1
        pound_len = len(str(len(ids)))
        header = "{pound:{pound_len}}{score:{bar_len}}{name:2}\n".format(
            pound="#",
            name="Name",
            score="Cookies",
            pound_len=pound_len + 3,
            bar_len=pound_len + 9,
        )
        temp_msg = header
        for a_id in ids:
            a = get(ctx.guild.members, id=int(a_id))
            if not a:
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
                lst.append(box(temp_msg, lang="md"))
                temp_msg = header
            pos += 1
        if temp_msg != header:
            lst.append(box(temp_msg, lang="md"))
        if lst:
            if len(lst) > 1:
                await menu(ctx, lst, DEFAULT_CONTROLS)
            else:
                await ctx.send(lst[0])
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
        if amount < 0:
            return await ctx.send("Uh oh, the amount cannot be negative.")
        if self._max_balance_check(amount):
            return await ctx.send(
                f"Uh oh, you can't set an amount of cookies greater than {_MAX_BALANCE:,}."
            )
        await self.config.guild(ctx.guild).amount.set(amount)
        if amount != 0:
            await ctx.send(f"Members will receive {amount} cookies.")
        else:
            pred = MessagePredicate.valid_int(ctx)
            await ctx.send("What's the minimum amount of cookies members can obtain?")
            try:
                await self.bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            minimum = pred.result
            await self.config.guild(ctx.guild).minimum.set(minimum)

            await ctx.send("What's the maximum amount of cookies members can obtain?")
            try:
                await self.bot.wait_for("message", timeout=30, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            maximum = pred.result
            await self.config.guild(ctx.guild).maximum.set(maximum)

            await ctx.send(
                f"Members will receive a random amount of cookies between {minimum} and {maximum}."
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
            if on_off
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
        if self._max_balance_check(amount):
            return await ctx.send(
                f"Uh oh, amount can't be greater than {_MAX_BALANCE:,}."
            )
        await self.config.member(target).cookies.set(amount)
        await ctx.send(f"Set {target.mention}'s balance to {amount} :cookie:")

    @setcookies.command(name="add")
    async def setcookies_add(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Add cookies to someone."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        target_cookies = int(await self.config.member(target).cookies())
        target_cookies += amount
        if self._max_balance_check(target_cookies):
            return await ctx.send(
                f"Uh oh, {target.display_name} has reached the maximum amount of cookies."
            )
        await self.config.member(target).cookies.set(target_cookies)
        await ctx.send(f"Added {amount} :cookie: to {target.mention}'s balance.")

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
                f"Took away {amount} :cookie: from {target.mention}'s balance."
            )
        else:
            await ctx.send(f"{target.mention} doesn't have enough :cookies:")

    @setcookies.command(name="reset")
    async def setcookies_reset(self, ctx: commands.Context, confirmation: bool = False):
        """Delete all cookies from all members."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** cookies from all members. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}setcookies reset yes`."
            )
        for member in ctx.guild.members:
            cookies = int(await self.config.member(member).cookies())
            if cookies != 0:
                await self.config.member(member).cookies.set(0)
        await ctx.send("All cookies have been deleted from all members.")

    @setcookies.command(name="rate")
    async def setcookies_rate(self, ctx: commands.Context, rate: Union[int, float]):
        """Set the exchange rate for `[p]cookieexchange`."""
        if rate <= 0:
            return await ctx.send("Uh oh, rate has to be more than 0.")
        await self.config.guild(ctx.guild).rate.set(rate)
        currency = await bank.get_currency_name(ctx.guild)
        test_amount = 100*rate
        await ctx.send(f"Set the exchange rate {rate}. This means that 100 {currency} will give you {test_amount} :cookie:")

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

    @role.command(name="multiplier")
    async def setcookies_role_multiplier(
        self, ctx: commands.Context, role: discord.Role, multiplier: int
    ):
        """Set cookies multipler for role. Disabled when random amount is enabled.
        
        Default is 1 (aka the same amount)."""
        if multiplier <= 0:
            return await ctx.send("Uh oh, multiplier has to be more than 0.")
        await self.config.role(role).multiplier.set(multiplier)
        await ctx.send(f"Users with {role.name} will now get {multiplier} times more :cookie:")

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
                    if self._max_balance_check(new_cookies):
                        continue
                    await self.config.member(after).cookies.set(new_cookies)

    async def _get_ids(self, ctx):
        data = await self.config.all_members(ctx.guild)
        ids = sorted(data, key=lambda x: data[x]["cookies"], reverse=True)
        return ids

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
                result.append(f"{value} {name}")
        return ", ".join(result[:granularity])

    @staticmethod
    def _max_balance_check(value: int):
        if value > _MAX_BALANCE:
            return True
