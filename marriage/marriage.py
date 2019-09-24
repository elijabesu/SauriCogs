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

__author__ = 'saurichable'

Cog: Any = getattr(commands, "Cog", object)

class Marriage(Cog):
    """
    Simple marriage cog.
    """

    __author__ = "saurichable"
    __version__ = "0.3.1"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=5465461324979524, force_registration=True)

        self.config.register_member(married=False, current=[], divorced=False, exes=[], about="I'm mysterious", crush=None, marcount=0, temper=100)
        self.config.register_guild(toggle=False, marprice=1500, divprice=2, currency=0, multi=False)

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
                    return await ctx.send(f"Uh oh, Cookies isn't loaded. Load it using `{ctx.clean_prefix}load cookies`")
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

    @marriage.group(autohelp=True)
    async def stuff(self, ctx):
        """Various actions and gifts settings."""
        pass

    @stuff.command(name="temper")
    async def marriage_stuff_temper(self, ctx: commands.Context, id: int, temper: int):
        """Temper has to be in range [-100; 100]. Negative actions (f.e. flirting with someone other than one's spouse) should have negative temper.
        !!! Remember that starting point for everyone is 100 == happy and satisfied"""

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
                    spouse = ctx.guild.get_member(spouse_id).name
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
            exes = []
            for ex_id in exes_ids:
                try:
                    ex = ctx.guild.get_member(ex_id).name
                    exes.append(ex)
                except:
                    continue 
            if exes == []:
                ex_text = "None"
            else:
                ex_text = humanize_list(exes)
        
        crush = ctx.guild.get_member(await conf.crush()).name

        e = discord.Embed(colour = member.color)
        e.set_author(name="{0}'s Profile".format(member.name), icon_url=member.avatar_url)
        e.set_footer(text="{0}#{1} ({2})".format(member.name, member.discriminator, member.id))
        e.set_thumbnail(url=member.avatar_url)
        e.add_field(name="Relationship status:", value=rs_status, inline=True)
        if is_married is True:
            e.add_field(name="Spouse(s):", value=spouse_text, inline=True)
        e.add_field(name="About:", value=await conf.about(), inline=False)
        e.add_field(name="Been married:", value=been_married, inline=True)
        if await conf.marcount() != 0:
            e.add_field(name="Ex spouses:", value=ex_text, inline=False)
        e.add_field(name="Crush:", value=crush, inline=True)

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
                ex = ctx.guild.get_member(ex_id).name
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
        if await self.config.guild(ctx.guild).multi() is False:
            if await self.config.member(ctx.author).married() is True:
                return await ctx.send("You're already married!")
            if await self.config.member(spouse).married() is True:
                return await ctx.send("They're already married!")

        await ctx.send(f"{ctx.author.mention} has asked {spouse.mention} to marry them!\n{spouse.mention}, what do you say?")
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
            author_cookies = int(await self.bot.get_cog("Cookies").config.member(ctx.author).cookies())
            target_cookies = int(await self.bot.get_cog("Cookies").config.member(spouse).cookies())
            end_amount = f"{amount} :cookie:"
            if amount <= author_cookies:
                if amount <= target_cookies:
                    await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(author_cookies - amount)
                    await self.bot.get_cog("Cookies").config.member(spouse).cookies.set(target_cookies - amount)
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
        await ctx.send(f":church: {ctx.author.mention} and {spouse.mention} are now a happy married couple! Congrats! :tada:\n*You both paid {end_amount}.*")

    @commands.guild_only()
    @commands.command()
    async def divorce(self, ctx: commands.Context, spouse: discord.Member, court: bool=False):
        """Divorse your current spouse"""
        if await self.config.guild(ctx.guild).toggle() is False:
            return await ctx.send("Marriage is not enabled!")

        if spouse.id == ctx.author.id:
            return await ctx.send("You cannot divorce yourself!")
        is_spouse = await self.config.member(ctx.author).current(spouse.id)
        if is_spouse:
            if court is False:
                await ctx.send(f"{ctx.author.mention} wants to divorce you, {spouse.mention}, do you accept?\nIf you say no, you will go to the court.")
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
                                return await ctx.send(f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`")
                        else:
                            return await ctx.send(f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`")
                    else:
                        author_cookies = int(await self.bot.get_cog("Cookies").config.member(ctx.author).cookies())
                        target_cookies = int(await self.bot.get_cog("Cookies").config.member(spouse).cookies())
                        end_amount = f"You both paid {amount} :cookie:"
                        if amount <= author_cookies:
                            if amount <= target_cookies:
                                await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(author_cookies - amount)
                                await self.bot.get_cog("Cookies").config.member(spouse).cookies.set(target_cookies - amount)
                            else:
                                return await ctx.send(f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`")
                        else:
                            return await ctx.send(f"Uh oh, you two cannot afford this... But you can force a court by doing `{ctx.clean_prefix}divorce {spouse.mention} yes`")
                else:
                    pass
            else: ## COURT:
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
                    author_cookies = int(await self.bot.get_cog("Cookies").config.member(ctx.author).cookies())
                    target_cookies = int(await self.bot.get_cog("Cookies").config.member(spouse).cookies())
                    aamount = author_cookies * court_multiplier
                    tamount = target_cookies * court_multiplier
                    end_amount = f"{ctx.author.name} paid {aamount} :cookie:, {spouse.name} paid {tamount} :cookie:"
                    await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(author_cookies - aamount)
                    await self.bot.get_cog("Cookies").config.member(spouse).cookies.set(target_cookies - tamount)
            async with self.config.member(ctx.author).current() as acurrent:
                acurrent.remove(spouse.id)
            async with self.config.member(spouse).current() as tcurrent:
                tcurrent.remove(ctx.author.id)
            if len(await self.config.member(ctx.author).current()) == 0:
                await self.config.member(ctx.author).married.set(False)
                await self.config.member(ctx.author).divorced.set(True)
            if len(await self.config.member(spouse).current()) == 0:
                await self.config.member(spouse).married.set(True)
                await self.config.member(spouse).divorced.set(False)
            return await ctx.send(f":broken_heart: {ctx.author.mention} and {spouse.mention} got divorced...\n*{end_amount}.*")
        else:
            return await ctx.send("You two aren't married!")
