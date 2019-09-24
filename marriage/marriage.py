import asyncio
import discord
import random

from typing import Any
from discord.utils import get
from datetime import datetime

from redbot.core import Config, checks, commands, bank
from redbot.core.utils.chat_formatting import pagify, box, humanize_list
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red

__author__ = "saurichable"

Cog: Any = getattr(commands, "Cog", object)


class Marriage(Cog):
    """
    Simple marriage cog.
    """

    __author__ = "saurichable"
    __version__ = "0.4.7"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=5465461324979524, force_registration=True
        )

        self.config.register_member(
            married=False,
            current=[],
            divorced=False,
            exes=[],
            about="I'm mysterious",
            crush=None,
            marcount=0,
            temper=100,
        )
        self.config.register_guild(
            toggle=False,
            marprice=1500,
            divprice=2,
            currency=0,
            multi=False,
            shit={
                "flirt": [5, 0],
                "fuck": [15, 0],
                "dinner": [15, 0],
                "date": [10, 0],
                "flower": [5, 5],
                "sweets": [5, 5],
                "alcohol": [5, 5],
                "loveletter": [5, 1],
                "food": [5, 10],
                "makeup": [5, 20],
                "car": [15, 500],
                "yacht": [30, 1000],
                "house": [60, 25000],
            },
        )

    # Actions/Gifts are saved as lists, position 0 is temper, position 1 is cookies

    @commands.group(autohelp=True)
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def marriage(self, ctx):
        """Various Marriage settings."""
        pass

    @marriage.command(name="toggle")
    async def marriage_toggle(self, ctx: commands.Context, on_off: bool = None):
        """Toggle Marriage for current server. 
        
        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off
            if on_off is not None
            else not (await self.config.guild(ctx.guild).toggle())
        )
        await self.config.guild(ctx.guild).toggle.set(target_state)
        if target_state:
            await ctx.send("Marriage is now enabled.")
        else:
            await ctx.send("Marriage is now disabled.")

    @checks.is_owner()
    @marriage.command(name="currency")
    async def marriage_currency(self, ctx: commands.Context, currency: int):
        """Set the currency that should be used. 0 for Red's economy, 1 for SauriCogs' cookies"""
        if currency != 0:
            if currency != 1:
                return await ctx.send("Uh oh, currency can only be 0 or 1.")
            else:
                loaded = self.bot.get_cog("Cookies")
                if loaded is None:
                    return await ctx.send(
                        f"Uh oh, Cookies isn't loaded. Load it using `{ctx.clean_prefix}load cookies`"
                    )
        await self.config.guild(ctx.guild).currency.set(currency)
        await ctx.tick()

    @marriage.command(name="multiple")
    async def marriage_multiple(self, ctx: commands.Context, state: bool):
        """Enable/disable whether members can be married to multiple people at once."""
        if state is False:
            text = "Members cannot marry multiple people."
        else:
            text = "Members can marry multiple people."
        await self.config.guild(ctx.guild).multi.set(state)
        await ctx.send(text)

    @marriage.command(name="marprice")
    async def marriage_marprice(self, ctx: commands.Context, price: int):
        """Set the price for getting married.
        
        With each past marriage, the cost of getting married is 50% more"""
        if price <= 0:
            return await ctx.send("Uh oh, price cannot be 0 or less.")
        await self.config.guild(ctx.guild).marprice.set(price)
        await ctx.tick()

    @marriage.command(name="divprice")
    async def marriage_divprice(self, ctx: commands.Context, multiplier: int):
        """Set the MULTIPLIER for getting divorced.
        
        This is a multiplier, not the price! Default is 2."""
        if multiplier <= 1:
            return await ctx.send("Uh oh, that ain't a valia multiplier.")
        await self.config.guild(ctx.guild).divprice.set(multiplier)
        await ctx.tick()

    @marriage.command(name="changetemper")
    async def marriage_changetemper(
        self, ctx: commands.Context, action: str, temper: int
    ):
        """Temper has to be in range 1 to 100. Negative actions (f.e. flirting with someone other than one's spouse) should have negative temper.
        !!! Remember that starting point for everyone is 100 == happy and satisfied, 0 == leave their spouse"""
        available = [
            "flirt",
            "fuck",
            "dinner",
            "date",
            "flower",
            "sweets",
            "alcohol",
            "loveletter",
            "food",
            "makeup",
            "car",
            "yacht",
            "house",
        ]
        if action not in available:
            return await ctx.send(f"Available actions/gifts are: {available}")
        action = await self.config.guild(ctx.guild).shit.get_raw(action)
        action[0] = temper
        await self.config.guild(ctx.guild).shit.get_raw(action)

    @marriage.command(name="changeprice")
    async def marriage_changeprice(
        self, ctx: commands.Context, action: str, price: int
    ):
        """Set the action's/gift's price"""
        available = [
            "flirt",
            "fuck",
            "dinner",
            "date",
            "flower",
            "sweets",
            "alcohol",
            "loveletter",
            "food",
            "makeup",
            "car",
            "yacht",
            "house",
        ]
        if action not in available:
            return await ctx.send(f"Available actions/gifts are: {available}")
        action = await self.config.guild(ctx.guild).shit.get_raw(action)
        action[1] = price
        await self.config.guild(ctx.guild).shit.get_raw(action)

    @commands.guild_only()
    @commands.command()
    async def addabout(self, ctx: commands.Context, *, about: str):
        """Add your about text"""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if len(about) > 1000:
            return await ctx.send("Uh oh, this is not an essay.")
        else:
            await self.config.member(ctx.author).about.set(about)
            await ctx.tick()

    @commands.guild_only()
    @commands.command()
    async def about(self, ctx: commands.Context, member: discord.Member = None):
        """Display your or someone else's about"""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if not member:
            member = ctx.author
        conf = self.config.member(member)

        is_married = await conf.married()
        if is_married is False:
            is_divorced = await conf.married()
            if is_divorced is False:
                rs_status = "Single"
            else:
                rs_status = "Divorced"
        else:
            rs_status = "Married"
            spouse_ids = await conf.current()
            spouses = []
            for spouse_id in spouse_ids:
                try:
                    spouse = ctx.guild.get_member(spouse_id)
                    if spouse is None:
                        continue
                    else:
                        spouse = spouse.name
                    spouses.append(spouse)
                except:
                    continue
            if spouses == []:
                spouse_text = "None"
            else:
                spouse_text = humanize_list(spouses)

        been_married = f"{await conf.marcount()} time(s)"
        if await conf.marcount() != 0:
            exes_ids = await conf.exes()
            if exes_ids == []:
                ex_text = "None"
            else:
                exes = []
                for ex_id in exes_ids:
                    try:
                        ex = ctx.guild.get_member(ex_id)
                        if ex is None:
                            continue
                        else:
                            ex = ex.name
                        exes.append(ex)
                    except:
                        continue
                if exes == []:
                    ex_text = "None"
                else:
                    ex_text = humanize_list(exes)

        crush = ctx.guild.get_member(await conf.crush())
        if crush is None:
            crush = "None"
        else:
            crush = crush.name

        e = discord.Embed(colour=member.color)
        e.set_author(
            name="{0}'s Profile".format(member.name), icon_url=member.avatar_url
        )
        e.set_footer(
            text="{0}#{1} ({2})".format(member.name, member.discriminator, member.id)
        )
        e.set_thumbnail(url=member.avatar_url)
        e.add_field(name="Relationship status:", value=rs_status, inline=True)
        if is_married is True:
            e.add_field(name="Spouse(s):", value=spouse_text, inline=True)
        e.add_field(name="About:", value=await conf.about(), inline=False)
        e.add_field(name="Been married:", value=been_married, inline=True)
        if await conf.marcount() != 0:
            e.add_field(name="Ex spouses:", value=ex_text, inline=False)
        e.add_field(name="Crush:", value=crush, inline=True)
        e.add_field(name="Temper:", value=await conf.temper(), inline=True)

        await ctx.send(embed=e)

    @commands.guild_only()
    @commands.command()
    async def exes(self, ctx: commands.Context, member: discord.Member = None):
        """Display your or someone else's exes"""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if not member:
            member = ctx.author
        exes_ids = await self.config.member(member).exes()
        exes = []
        for ex_id in exes_ids:
            try:
                ex = ctx.guild.get_member(ex_id)
                if ex is None:
                    continue
                else:
                    ex = ex.name
                exes.append(ex)
            except:
                continue
        if exes == []:
            ex_text = "unknown"
        else:
            ex_text = humanize_list(exes)
        await ctx.send(f"{member.mention}'s exes are: {ex_text}")

    @commands.guild_only()
    @commands.command()
    async def crush(self, ctx: commands.Context, member: discord.Member = None):
        """Tell us who you have a crush on"""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if not member:
            await self.config.member(ctx.author).crush.set(None)
        else:
            if member.id == ctx.author.id:
                return await ctx.send("You cannot have a crush on yourself!")
            await self.config.member(ctx.author).crush.set(member.id)
        await ctx.tick()

    @commands.guild_only()
    @commands.command()
    async def marry(self, ctx: commands.Context, spouse: discord.Member):
        """Marry the love of your life!"""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if spouse.id == ctx.author.id:
            return await ctx.send("You cannot marry yourself!")
        if spouse.id in await self.config.member(ctx.author).current():
            return await ctx.send("You two are already married!")
        if await self.config.guild(ctx.guild).multi() is False:
            if await self.config.member(ctx.author).married() is True:
                return await ctx.send("You're already married!")
            if await self.config.member(spouse).married() is True:
                return await ctx.send("They're already married!")

        await ctx.send(
            f"{ctx.author.mention} has asked {spouse.mention} to marry them!\n{spouse.mention}, what do you say?"
        )
        pred = MessagePredicate.yes_or_no(ctx, ctx.channel, spouse)
        await self.bot.wait_for("message", check=pred)
        if pred.result is False:
            return await ctx.send("Oh no... I was looking forward to the cerenomy...")
        else:
            pass

        default_amount = await self.config.guild(ctx.guild).marprice()
        author_marcount = await self.config.member(ctx.author).marcount()
        target_marcount = await self.config.member(spouse).marcount()

        author_multiplier = author_marcount / 2 + 1
        target_multiplier = target_marcount / 2 + 1

        if author_multiplier <= target_multiplier:
            multiplier = target_multiplier
        else:
            multiplier = author_multiplier

        if multiplier != 0:
            amount = default_amount * multiplier
        else:
            amount = default_amount
        if await self.config.guild(ctx.guild).currency() == 0:
            currency = await bank.get_currency_name(ctx.guild)
            end_amount = f"{amount} {currency}"
            if await bank.can_spend(ctx.author, amount) is True:
                if await bank.can_spend(spouse, amount) is True:
                    await bank.withdraw_credits(ctx.author, amount)
                    await bank.withdraw_credits(spouse, amount)
                else:
                    return await ctx.send(f"Uh oh, you two cannot afford this...")
            else:
                return await ctx.send(f"Uh oh, you two cannot afford this...")
        else:
            author_cookies = int(
                await self.bot.get_cog("Cookies").config.member(ctx.author).cookies()
            )
            target_cookies = int(
                await self.bot.get_cog("Cookies").config.member(spouse).cookies()
            )
            end_amount = f"{amount} :cookie:"
            if amount <= author_cookies:
                if amount <= target_cookies:
                    await self.bot.get_cog("Cookies").config.member(
                        ctx.author
                    ).cookies.set(author_cookies - amount)
                    await self.bot.get_cog("Cookies").config.member(spouse).cookies.set(
                        target_cookies - amount
                    )
                else:
                    return await ctx.send(f"Uh oh, you two cannot afford this...")
            else:
                return await ctx.send(f"Uh oh, you two cannot afford this...")

        await self.config.member(ctx.author).marcount.set(author_marcount + 1)
        await self.config.member(spouse).marcount.set(target_marcount + 1)
        await self.config.member(ctx.author).married.set(True)
        await self.config.member(spouse).married.set(True)
        await self.config.member(ctx.author).divorced.set(False)
        await self.config.member(spouse).divorced.set(False)
        async with self.config.member(ctx.author).current() as acurrent:
            acurrent.append(spouse.id)
        async with self.config.member(spouse).current() as tcurrent:
            tcurrent.append(ctx.author.id)
        await ctx.send(
            f":church: {ctx.author.mention} and {spouse.mention} are now a happy married couple! Congrats! :tada:\n*You both paid {end_amount}.*"
        )

    @commands.guild_only()
    @commands.command()
    async def divorce(
        self, ctx: commands.Context, spouse: discord.Member, court: bool = False
    ):
        """Divorse your current spouse"""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if spouse.id == ctx.author.id:
            return await ctx.send("You cannot divorce yourself!")
        if spouse.id in await self.config.member(ctx.author).current():
            if court is False:
                await ctx.send(
                    f"{ctx.author.mention} wants to divorce you, {spouse.mention}, do you accept?\nIf you say no, you will go to the court."
                )
                pred = MessagePredicate.yes_or_no(ctx, ctx.channel, spouse)
                await self.bot.wait_for("message", check=pred)
                if pred.result is True:
                    default_amount = await self.config.guild(ctx.guild).marprice()
                    default_multiplier = await self.config.guild(ctx.guild).divprice()
                    author_marcount = await self.config.member(ctx.author).marcount()
                    target_marcount = await self.config.member(spouse).marcount()

                    author_multiplier = author_marcount / 2 + 1
                    target_multiplier = target_marcount / 2 + 1

                    if author_multiplier <= target_multiplier:
                        multiplier = target_multiplier
                    else:
                        multiplier = author_multiplier

                    if multiplier != 0:
                        amount = default_amount * multiplier * default_multiplier
                    else:
                        amount = default_amount * default_multiplier
                    if await self.config.guild(ctx.guild).currency() == 0:
                        currency = await bank.get_currency_name(ctx.guild)
                        end_amount = f"You both paid {amount} {currency}"
                        if await bank.can_spend(ctx.author, amount) is True:
                            if await bank.can_spend(spouse, amount) is True:
                                await bank.withdraw_credits(ctx.author, amount)
                                await bank.withdraw_credits(spouse, amount)
                            else:
                                return await ctx.send(
                                    f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`"
                                )
                        else:
                            return await ctx.send(
                                f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`"
                            )
                    else:
                        author_cookies = int(
                            await self.bot.get_cog("Cookies")
                            .config.member(ctx.author)
                            .cookies()
                        )
                        target_cookies = int(
                            await self.bot.get_cog("Cookies")
                            .config.member(spouse)
                            .cookies()
                        )
                        end_amount = f"You both paid {amount} :cookie:"
                        if amount <= author_cookies:
                            if amount <= target_cookies:
                                await self.bot.get_cog("Cookies").config.member(
                                    ctx.author
                                ).cookies.set(author_cookies - amount)
                                await self.bot.get_cog("Cookies").config.member(
                                    spouse
                                ).cookies.set(target_cookies - amount)
                            else:
                                return await ctx.send(
                                    f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`"
                                )
                        else:
                            return await ctx.send(
                                f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`"
                            )
                else:
                    pass
            else:  ## COURT:
                court = random.randint(1, 100)
                court_multiplier = court / 100
                if await self.config.guild(ctx.guild).currency() == 0:
                    currency = await bank.get_currency_name(ctx.guild)
                    abal = await bank.get_balance(ctx.author)
                    tbal = await bank.get_balance(spouse)
                    aamount = abal * court_multiplier
                    tamount = tbal * court_multiplier
                    end_amount = f"{ctx.author.name} paid {aamount} {currency}, {spouse.name} paid {tamount} {currency}"
                    await bank.withdraw_credits(ctx.author, amount)
                    await bank.withdraw_credits(spouse, amount)
                else:
                    author_cookies = int(
                        await self.bot.get_cog("Cookies")
                        .config.member(ctx.author)
                        .cookies()
                    )
                    target_cookies = int(
                        await self.bot.get_cog("Cookies")
                        .config.member(spouse)
                        .cookies()
                    )
                    aamount = author_cookies * court_multiplier
                    tamount = target_cookies * court_multiplier
                    end_amount = f"{ctx.author.name} paid {aamount} :cookie:, {spouse.name} paid {tamount} :cookie:"
                    await self.bot.get_cog("Cookies").config.member(
                        ctx.author
                    ).cookies.set(author_cookies - aamount)
                    await self.bot.get_cog("Cookies").config.member(spouse).cookies.set(
                        target_cookies - tamount
                    )
            async with self.config.member(ctx.author).current() as acurrent:
                acurrent.remove(spouse.id)
            async with self.config.member(spouse).current() as tcurrent:
                tcurrent.remove(ctx.author.id)
            async with self.config.member(ctx.author).exes() as aexes:
                aexes.append(spouse.id)
            async with self.config.member(spouse).exes() as texes:
                texes.append(ctx.author.id)
            if len(await self.config.member(ctx.author).current()) == 0:
                await self.config.member(ctx.author).married.set(False)
                await self.config.member(ctx.author).divorced.set(True)
            if len(await self.config.member(spouse).current()) == 0:
                await self.config.member(spouse).married.set(True)
                await self.config.member(spouse).divorced.set(False)
            return await ctx.send(
                f":broken_heart: {ctx.author.mention} and {spouse.mention} got divorced...\n*{end_amount}.*"
            )
        else:
            return await ctx.send("You two aren't married!")

    @commands.guild_only()
    @commands.command()
    async def perform(
        self,
        ctx: commands.Context,
        action: str,
        target: discord.Member,
        item: str = None,
    ):
        """Do something with someone"""
        gc = self.config.guild
        mc = self.config.member
        if await gc(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if action == "flirt":
            endtext = (
                f":heart_eyes: {ctx.author.mention} is flirting with {target.mention}"
            )
        elif action == "fuck":
            endtext = f":smirk: {ctx.author.mention} wants to bang {target.mention}, did they do it? We'll never know..."
        elif action == "dinner":
            endtext = (
                f":ramen: {ctx.author.mention} took {target.mention} on a fancy dinner"
            )
        elif action == "date":
            endtext = (
                f":relaxed: {ctx.author.mention} took {target.mention} on a nice date"
            )
        elif action == "gift":
            gifts = [
                "flower",
                "sweets",
                "alcohol",
                "loveletter",
                "food",
                "makeup",
                "car",
                "yacht",
                "house",
            ]
            if item not in gifts:
                return await ctx.send(f"Available actions/gifts are: {gifts}")
            action = item
            endtext = f":gift: {ctx.author.mention} has gifted {item} to {target.mention}"
        else:
            return await ctx.send(
                "Available actions are: `flirt`, `fuck`, `dinner`, `date`, `gift`"
            )

        action = await gc(ctx.guild).shit.get_raw(action)
        temper = action[0]
        cookies = action[1]

        t_temp = await mc(target).temper()
        t_missing = 100 - t_temp
        if t_missing != 0:
            if temper <= t_missing:
                await mc(target).temper.set(t_temp + temper)
            else:
                await mc(target).temper.set(100)

        a_temp = await mc(ctx.author).temper()
        a_missing = 100 - a_temp
        if a_missing != 0:
            if temper <= a_missing:
                await mc(ctx.author).temper.set(a_temp + temper)
            else:
                await mc(ctx.author).temper.set(100)

        spouses = await mc(ctx.author).current()
        if target.id in spouses:
            pass
        else:
            if await mc(ctx.author).married() is True:
                for sid in spouses:
                    spouse = ctx.guild.get_member(sid)
                    s_temp = await mc(spouse).temper()
                    if s_temp < temper:
                        new_s_temp = 0
                    else:
                        new_s_temp = s_temp - temper
                    await mc(spouse).temper.set(new_s_temp)
                    if new_s_temp <= 0:
                        async with self.config.member(ctx.author).current() as acurrent:
                            acurrent.remove(spouse.id)
                        async with self.config.member(spouse).current() as tcurrent:
                            tcurrent.remove(ctx.author.id)
                        async with self.config.member(ctx.author).exes() as aexes:
                            aexes.append(spouse.id)
                        async with self.config.member(spouse).exes() as texes:
                            texes.append(ctx.author.id)
                        if len(await self.config.member(ctx.author).current()) == 0:
                            await self.config.member(ctx.author).married.set(False)
                            await self.config.member(ctx.author).divorced.set(True)
                        if len(await self.config.member(spouse).current()) == 0:
                            await self.config.member(spouse).married.set(True)
                            await self.config.member(spouse).divorced.set(False)
                        if await self.config.guild(ctx.guild).currency() == 0:
                            abal = await bank.get_balance(ctx.author)
                            tamount = tbal * court_multiplier
                            await bank.withdraw_credits(ctx.author, abal)
                            await bank.deposit_credits(spouse, abal)
                        else:
                            author_cookies = int(
                                await self.bot.get_cog("Cookies")
                                .config.member(ctx.author)
                                .cookies()
                            )
                            target_cookies = int(
                                await self.bot.get_cog("Cookies")
                                .config.member(spouse)
                                .cookies()
                            )
                            await self.bot.get_cog("Cookies").config.member(
                                ctx.author
                            ).cookies.set(0)
                            await self.bot.get_cog("Cookies").config.member(
                                spouse
                            ).cookies.set(target_cookies + author_cookies)
                        await ctx.send(
                            f":broken_heart: {ctx.author.mention} has made {spouse.mention} completely unhappy with their actions so {spouse.mention} left them and took all their money!"
                        )

        await ctx.send(endtext)
