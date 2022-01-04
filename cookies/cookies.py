import asyncio
import discord
import random
import calendar
import typing
import datetime

from redbot.core import Config, checks, commands, bank, errors
from redbot.core.utils.chat_formatting import pagify, box
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red

_MAX_BALANCE = 2 ** 63 - 1


class Cookies(commands.Cog):
    """
    Collect cookies and steal from others.
    """

    __version__ = "1.2.3"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=16548964843212314, force_registration=True
        )
        self.config.register_guild(
            amount=1,
            minimum=0,
            maximum=0,
            cooldown=43200,
            stealing=False,
            stealcd=43200,
            rate=0.5,
        )
        self.config.register_global(
            is_global=False,
            amount=1,
            minimum=0,
            maximum=0,
            cooldown=43200,
            stealing=False,
            stealcd=43200,
            rate=0.5,
        )

        self.config.register_member(cookies=0, next_cookie=0, next_steal=0)
        self.config.register_user(cookies=0, next_cookie=0, next_steal=0)

        self.config.register_role(cookies=0, multiplier=1)

    async def red_delete_data_for_user(self, *, requester, user_id):
        await self.config.user_from_id(user_id).clear()
        for guild in self.bot.guilds:
            await self.config.member_from_ids(guild.id, user_id).clear()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @commands.command()
    @commands.guild_only()
    async def cookie(self, ctx: commands.Context):
        """Get your daily dose of cookies."""
        cur_time = calendar.timegm(ctx.message.created_at.utctimetuple())

        if await self.config.is_global():
            conf = self.config
            um_conf = self.config.user(ctx.author)
        else:
            conf = self.config.guild(ctx.guild)
            um_conf = self.config.member(ctx.author)

        amount = await conf.amount()
        cookies = await um_conf.cookies()
        next_cookie = await um_conf.next_cookie()
        minimum = await conf.minimum()
        maximum = await conf.maximum()

        if cur_time >= next_cookie:
            if amount != 0:
                multipliers = []
                for role in ctx.author.roles:
                    role_multiplier = await self.config.role(role).multiplier()
                    if not role_multiplier:
                        role_multiplier = 1
                    multipliers.append(role_multiplier)
                amount *= max(multipliers)
            else:
                amount = int(random.choice(list(range(minimum, maximum))))
            if self._max_balance_check(cookies + amount):
                return await ctx.send(
                    "Uh oh, you have reached the maximum amount of cookies that you can put in your bag. :frowning:"
                )
            next_cookie = cur_time + await conf.cooldown()
            await um_conf.next_cookie.set(next_cookie)
            await self.deposit_cookies(ctx.author, amount)
            await ctx.send(
                f"Here {'is' if amount == 1 else 'are'} your {amount} :cookie:"
            )
        else:
            dtime = self.display_time(next_cookie - cur_time)
            await ctx.send(f"Uh oh, you have to wait {dtime}.")

    @commands.command()
    @commands.guild_only()
    async def steal(
        self, ctx: commands.Context, *, target: typing.Optional[discord.Member]
    ):
        """Steal cookies from members."""
        cur_time = calendar.timegm(ctx.message.created_at.utctimetuple())

        if await self.config.is_global():
            conf = self.config
            um_conf = self.config.user(ctx.author)
        else:
            conf = self.config.guild(ctx.guild)
            um_conf = self.config.member(ctx.author)

        next_steal = await um_conf.next_steal()
        enabled = await conf.stealing()
        author_cookies = await um_conf.cookies()

        if not enabled:
            return await ctx.send("Uh oh, stealing is disabled.")
        if cur_time < next_steal:
            dtime = self.display_time(next_steal - cur_time)
            return await ctx.send(f"Uh oh, you have to wait {dtime}.")

        if not target:
            # target can only be from the same server
            ids = await self._get_ids(ctx)
            while not target:
                target_id = random.choice(ids)
                target = ctx.guild.get_member(target_id)
        if target.id == ctx.author.id:
            return await ctx.send("Uh oh, you can't steal from yourself.")
        if await self.config.is_global():
            target_cookies = await self.config.user(target).cookies()
        else:
            target_cookies = await self.config.member(target).cookies()
        if target_cookies == 0:
            return await ctx.send(
                f"Uh oh, {target.display_name} doesn't have any :cookie:"
            )

        await um_conf.next_steal.set(cur_time + await conf.stealcd())

        if random.randint(1, 100) > 90:
            cookies_stolen = int(target_cookies * 0.5)
            if cookies_stolen == 0:
                cookies_stolen = 1
            stolen = random.randint(1, cookies_stolen)
            if self._max_balance_check(author_cookies + stolen):
                return await ctx.send(
                    "Uh oh, you have reached the maximum amount of cookies that you can put in your jar. :frowning:\n"
                    f"You didn't steal any :cookie: from {target.display_name}."
                )
            await self.deposit_cookies(ctx.author, stolen)
            await self.withdraw_cookies(target, stolen)
            return await ctx.send(
                f"You stole {stolen} :cookie: from {target.display_name}!"
            )

        cookies_penalty = int(author_cookies * 0.25)
        if cookies_penalty == 0:
            cookies_penalty = 1
        if cookies_penalty <= 0:
            return await ctx.send(
                f"Uh oh, you got caught while trying to steal {target.display_name}'s :cookie:\n"
                f"You don't have any cookies, so you haven't lost any."
            )
        penalty = random.randint(1, cookies_penalty)
        if author_cookies < penalty:
            penalty = author_cookies
        if self._max_balance_check(target_cookies + penalty):
            return await ctx.send(
                f"Uh oh, you got caught while trying to steal {target.display_name}'s :cookie:\n"
                f"{target.display_name} has reached the maximum amount of cookies, "
                "so you haven't lost any."
            )
        await self.deposit_cookies(target, penalty)
        await self.withdraw_cookies(ctx.author, penalty)
        await ctx.send(
            f"You got caught while trying to steal {target.display_name}'s :cookie:\nYour penalty is {penalty} :cookie: which they got!"
        )

    @commands.command()
    @commands.guild_only()
    async def give(self, ctx: commands.Context, target: discord.Member, amount: int):
        """Give someone some yummy cookies."""
        um_conf = (
            self.config.user(ctx.author)
            if await self.config.is_global()
            else self.config.member(ctx.author)
        )

        author_cookies = await um_conf.cookies()
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        if target.id == ctx.author.id:
            return await ctx.send("Why would you do that?")
        if amount > author_cookies:
            return await ctx.send("You don't have enough cookies yourself!")
        target_cookies = await self.config.member(target).cookies()
        if self._max_balance_check(target_cookies + amount):
            return await ctx.send(
                f"Uh oh, {target.display_name}'s jar would be way too full."
            )
        await self.withdraw_cookies(ctx.author, amount)
        await self.deposit_cookies(target, amount)
        await ctx.send(
            f"{ctx.author.mention} has gifted {amount} :cookie: to {target.mention}"
        )

    @commands.command(aliases=["jar"])
    @commands.guild_only()
    async def cookies(
        self, ctx: commands.Context, *, target: typing.Optional[discord.Member]
    ):
        """Check how many cookies you have."""
        if not target:
            um_conf = (
                self.config.user(ctx.author)
                if await self.config.is_global()
                else self.config.member(ctx.author)
            )
            cookies = await um_conf.cookies()
            await ctx.send(f"You have {cookies} :cookie:")
        else:
            um_conf = (
                self.config.user(target)
                if await self.config.is_global()
                else self.config.member(target)
            )
            cookies = await um_conf.cookies()
            await ctx.send(f"{target.display_name} has {cookies} :cookie:")

    @commands.command()
    @commands.guild_only()
    async def exchange(
        self,
        ctx: commands.Context,
        amount: int,
        to_currency: typing.Optional[bool] = False,
    ):
        """Exchange currency into cookies and vice versa."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")

        conf = (
            self.config
            if await self.config.is_global()
            else self.config.guild(ctx.guild)
        )

        rate = await conf.rate()
        currency = await bank.get_currency_name(ctx.guild)

        if not await self._can_spend(to_currency, ctx.author, amount):
            return await ctx.send(f"Uh oh, you cannot afford this.")

        if not to_currency:
            await bank.withdraw_credits(ctx.author, amount)
            new_cookies = int(amount * rate)
            if self._max_balance_check(new_cookies):
                return await ctx.send(f"Uh oh, your jar would be way too full.")
            await self.deposit_cookies(ctx.author, new_cookies)
            return await ctx.send(
                f"You have exchanged {amount} {currency} and got {new_cookies} :cookie:"
            )
        new_currency = int(amount / rate)
        try:
            await bank.deposit_credits(ctx.author, new_currency)
        except errors.BalanceTooHigh:
            return await ctx.send(f"Uh oh, your bank balance would be way too high.")
        await self.withdraw_cookies(ctx.author, amount)
        return await ctx.send(
            f"You have exchanged {amount} :cookie: and got {new_currency} {currency}"
        )

    @commands.command()
    @commands.guild_only()
    async def leaderboard(self, ctx: commands.Context):
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
        is_global = await self.config.is_global()
        for a_id in ids:
            a = self.bot.get_user(a_id) if is_global else ctx.guild.get_member(a_id)
            if not a:
                continue
            name = a.display_name
            cookies = (
                await self.config.user(a).cookies()
                if is_global
                else await self.config.member(a).cookies()
            )
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
    @checks.admin()
    @commands.guild_only()
    async def cookieset(self, ctx):
        """Various Cookies settings."""

    @cookieset.command(name="gg")
    async def cookieset_gg(
        self,
        ctx: commands.Context,
        make_global: bool,
        confirmation: typing.Optional[bool],
    ):
        """Switch from per-guild to global cookies and vice versa."""
        if await self.config.is_global() == make_global:
            return await ctx.send("Uh oh, you're not really changing anything.")
        if not confirmation:
            return await ctx.send(
                "This will delete **all** current settings. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}cookieset gg <make_global> yes`."
            )
        await self.config.clear_all_members()
        await self.config.clear_all_users()
        await self.config.clear_all_guilds()
        await self.config.clear_all_globals()
        await self.config.is_global.set(make_global)
        await ctx.send(f"Cookies are now {'global' if make_global else 'per-guild'}.")

    @cookieset.command(name="amount")
    async def cookieset_amount(self, ctx: commands.Context, amount: int):
        """Set the amount of cookies members can obtain.

        If 0, members will get a random amount."""
        if amount < 0:
            return await ctx.send("Uh oh, the amount cannot be negative.")
        if self._max_balance_check(amount):
            return await ctx.send(
                f"Uh oh, you can't set an amount of cookies greater than {_MAX_BALANCE:,}."
            )
        conf = (
            self.config
            if await self.config.is_global()
            else self.config.guild(ctx.guild)
        )
        await conf.amount.set(amount)
        if amount != 0:
            return await ctx.send(f"Members will receive {amount} cookies.")

        pred = MessagePredicate.valid_int(ctx)
        await ctx.send("What's the minimum amount of cookies members can obtain?")
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        minimum = pred.result
        await conf.minimum.set(minimum)

        await ctx.send("What's the maximum amount of cookies members can obtain?")
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        maximum = pred.result
        await conf.maximum.set(maximum)

        await ctx.send(
            f"Members will receive a random amount of cookies between {minimum} and {maximum}."
        )

    @cookieset.command(name="cooldown", aliases=["cd"])
    async def cookieset_cd(self, ctx: commands.Context, seconds: int):
        """Set the cooldown for `[p]cookie`.

        This is in seconds! Default is 43200 seconds (12 hours)."""
        if seconds <= 0:
            return await ctx.send("Uh oh, cooldown has to be more than 0 seconds.")
        conf = (
            self.config
            if await self.config.is_global()
            else self.config.guild(ctx.guild)
        )
        await conf.cooldown.set(seconds)
        await ctx.send(f"Set the cooldown to {seconds} seconds.")

    @cookieset.command(name="stealcooldown", aliases=["stealcd"])
    async def cookieset_stealcd(self, ctx: commands.Context, seconds: int):
        """Set the cooldown for `[p]steal`.

        This is in seconds! Default is 43200 seconds (12 hours)."""
        if seconds <= 0:
            return await ctx.send("Uh oh, cooldown has to be more than 0 seconds.")
        conf = (
            self.config
            if await self.config.is_global()
            else self.config.guild(ctx.guild)
        )
        await conf.stealcd.set(seconds)
        await ctx.send(f"Set the cooldown to {seconds} seconds.")

    @cookieset.command(name="steal")
    async def cookieset_steal(
        self, ctx: commands.Context, on_off: typing.Optional[bool]
    ):
        """Toggle cookie stealing for current server.

        If `on_off` is not provided, the state will be flipped."""
        conf = (
            self.config
            if await self.config.is_global()
            else self.config.guild(ctx.guild)
        )
        target_state = on_off or not (await conf.stealing())
        await conf.stealing.set(target_state)
        if target_state:
            await ctx.send("Stealing is now enabled.")
        else:
            await ctx.send("Stealing is now disabled.")

    @cookieset.command(name="set")
    async def cookieset_set(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Set someone's amount of cookies."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        if self._max_balance_check(amount):
            return await ctx.send(
                f"Uh oh, amount can't be greater than {_MAX_BALANCE:,}."
            )
        um_conf = (
            self.config.user(target)
            if await self.config.is_global()
            else self.config.member(target)
        )
        await um_conf.cookies.set(amount)
        await ctx.send(f"Set {target.mention}'s balance to {amount} :cookie:")

    @cookieset.command(name="add")
    async def cookieset_add(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Add cookies to someone."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        um_conf = (
            self.config.user(target)
            if await self.config.is_global()
            else self.config.member(target)
        )
        target_cookies = await um_conf.cookies()
        if self._max_balance_check(target_cookies + amount):
            return await ctx.send(
                f"Uh oh, {target.display_name} has reached the maximum amount of cookies."
            )
        await self.deposit_cookies(target, amount)
        await ctx.send(f"Added {amount} :cookie: to {target.mention}'s balance.")

    @cookieset.command(name="take")
    async def cookieset_take(
        self, ctx: commands.Context, target: discord.Member, amount: int
    ):
        """Take cookies away from someone."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        um_conf = (
            self.config.user(target)
            if await self.config.is_global()
            else self.config.member(target)
        )
        target_cookies = await um_conf.cookies()
        if amount <= target_cookies:
            await self.withdraw_cookies(target, amount)
            return await ctx.send(
                f"Took away {amount} :cookie: from {target.mention}'s balance."
            )
        await ctx.send(f"{target.mention} doesn't have enough :cookies:")

    @cookieset.command(name="reset")
    async def cookieset_reset(
        self, ctx: commands.Context, confirmation: typing.Optional[bool]
    ):
        """Delete all cookies from all members."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** cookies from all members. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}cookieset reset yes`."
            )
        if await self.config.is_global():
            await self.config.clear_all_users()
        else:
            await self.config.clear_all_members(ctx.guild)
        await ctx.send("All cookies have been deleted from all members.")

    @cookieset.command(name="rate")
    async def cookieset_rate(
        self, ctx: commands.Context, rate: typing.Union[int, float]
    ):
        """Set the exchange rate for `[p]cookieexchange`."""
        if rate <= 0:
            return await ctx.send("Uh oh, rate has to be more than 0.")
        conf = (
            self.config
            if await self.config.is_global()
            else self.config.guild(ctx.guild)
        )
        await conf.rate.set(rate)
        currency = await bank.get_currency_name(ctx.guild)
        test_amount = 100 * rate
        await ctx.send(
            f"Set the exchange rate {rate}. This means that 100 {currency} will give you {test_amount} :cookie:"
        )

    @cookieset.command(name="settings")
    async def cookieset_settings(self, ctx: commands.Context):
        """See current settings."""
        is_global = await self.config.is_global()
        data = (
            await self.config.all()
            if is_global
            else await self.config.guild(ctx.guild).all()
        )

        amount = data["amount"]
        amount = (
            str(amount)
            if amount != 0
            else f"random amount between {data['minimum']} and {data['maximum']}"
        )

        stealing = data["stealing"]
        stealing = "Enabled" if stealing else "Disabled"

        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Cookies settings:__**"
        embed.set_footer(text="*required to function properly")

        embed.add_field(name="Global:", value=str(is_global))
        embed.add_field(name="Exchange rate:", value=str(data["rate"]))
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Amount:", value=amount)
        embed.add_field(name="Cooldown:", value=self.display_time(data["cooldown"]))
        embed.add_field(name="\u200b", value="\u200b")
        embed.add_field(name="Stealing:", value=stealing)
        embed.add_field(name="Cooldown:", value=self.display_time(data["stealcd"]))

        await ctx.send(embed=embed)

    @cookieset.group(autohelp=True)
    async def role(self, ctx):
        """Cookie rewards for roles."""
        pass

    @role.command(name="add")
    async def cookieset_role_add(
        self, ctx: commands.Context, role: discord.Role, amount: int
    ):
        """Set cookies for role."""
        if amount <= 0:
            return await ctx.send("Uh oh, amount has to be more than 0.")
        await self.config.role(role).cookies.set(amount)
        await ctx.send(f"Gaining {role.name} will now give {amount} :cookie:")

    @role.command(name="del")
    async def cookieset_role_del(self, ctx: commands.Context, role: discord.Role):
        """Delete cookies for role."""
        await self.config.role(role).cookies.set(0)
        await ctx.send(f"Gaining {role.name} will now not give any :cookie:")

    @role.command(name="show")
    async def cookieset_role_show(self, ctx: commands.Context, role: discord.Role):
        """Show how many cookies a role gives."""
        cookies = int(await self.config.role(role).cookies())
        await ctx.send(f"Gaining {role.name} gives {cookies} :cookie:")

    @role.command(name="multiplier")
    async def cookieset_role_multiplier(
        self, ctx: commands.Context, role: discord.Role, multiplier: int
    ):
        """Set cookies multipler for role. Disabled when random amount is enabled.

        Default is 1 (aka the same amount)."""
        if multiplier <= 0:
            return await ctx.send("Uh oh, multiplier has to be more than 0.")
        await self.config.role(role).multiplier.set(multiplier)
        await ctx.send(
            f"Users with {role.name} will now get {multiplier} times more :cookie:"
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        b = set(before.roles)
        a = set(after.roles)
        after_roles = [list(a - b)][0]
        if after_roles:
            for role in after_roles:
                cookies = await self.config.role(role).cookies()
                if cookies != 0:
                    old_cookies = await self.config.member(after).cookies()
                    if self._max_balance_check(old_cookies + cookies):
                        continue
                    await self.deposit_cookies(after, cookies)

    async def _get_ids(self, ctx):
        if await self.config.is_global():
            data = await self.config.all_users()
        else:
            data = await self.config.all_members(ctx.guild)
        return sorted(data, key=lambda x: data[x]["cookies"], reverse=True)

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

    async def can_spend(self, user, amount):
        if await self.config.is_global():
            return await self.config.user(user).cookies() >= amount
        return await self.config.member(user).cookies() >= amount

    async def _can_spend(self, to_currency, user, amount):
        if to_currency:
            return bool(await self.can_spend(user, amount))
        return bool(await bank.can_spend(user, amount))

    async def withdraw_cookies(self, user, amount):
        if await self.config.is_global():
            cookies = await self.config.user(user).cookies() - amount
            await self.config.user(user).cookies.set(cookies)
        else:
            cookies = await self.config.member(user).cookies() - amount
            await self.config.member(user).cookies.set(cookies)

    async def deposit_cookies(self, user, amount):
        if await self.config.is_global():
            cookies = await self.config.user(user).cookies() + amount
            await self.config.user(user).cookies.set(cookies)
        else:
            cookies = await self.config.member(user).cookies() + amount
            await self.config.member(user).cookies.set(cookies)

    async def get_cookies(self, user):
        conf = (
            self.config.user(user)
            if await self.config.is_global()
            else self.config.member(user)
        )
        return await conf.cookies()
