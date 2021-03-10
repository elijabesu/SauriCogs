import discord
import asyncio
import random
import typing

from redbot.core import Config, checks, commands, bank
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.utils.predicates import MessagePredicate

from redbot.core.bot import Red

__author__ = "saurichable"


class Marriage(commands.Cog):
    """
    Marriage cog with some extra stuff.
    """

    __author__ = "saurichable"
    __version__ = "1.5.2"

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
            gifts={
                # "gift": owned pcs
            },
        )
        self.config.register_guild(
            toggle=False,
            marprice=1500,
            divprice=2,
            currency=0,
            multi=False,
            custom_actions={},
            custom_gifts={},
            removed_actions=[],
            removed_gifts=[],
            gift_text=":gift: {author} has gifted one {item} to {target}",
        )

    @property
    def _DEFAULT_ACTIONS(self):
        return {
            "flirt": {
                "temper": 5,
                "price": 0,
                "require_consent": False,
                "description": ":heart_eyes: {author} is flirting with {target}",
            },
            "fuck": {
                "temper": 15,
                "price": 0,
                "require_consent": True,
                "consent_description": "{author} wants to bang you, {target}, give consent?",
                "description": ":smirk: {author} banged {target}",
            },
            "dinner": {
                "temper": 15,
                "price": 0,
                "require_consent": False,
                "description": ":ramen: {author} took {target} on a fancy dinner",
            },
            "date": {
                "temper": 10,
                "price": 0,
                "require_consent": False,
                "description": ":relaxed: {author} took {target} on a nice date",
            },
        }

    @property
    def _DEFAULT_GIFTS(self):
        return {
            "flower": {"temper": 5, "price": 5},
            "sweets": {"temper": 5, "price": 5},
            "alcohol": {"temper": 5, "price": 5},
            "loveletter": {"temper": 5, "price": 1},
            "food": {"temper": 5, "price": 10},
            "makeup": {"temper": 5, "price": 20},
            "car": {"temper": 15, "price": 500},
            "yacht": {"temper": 30, "price": 1000},
            "house": {"temper": 60, "price": 25000},
        }

    @commands.group(autohelp=True)
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def marriage(self, ctx: commands.Context):
        """Various Marriage settings."""
        pass

    @marriage.command(name="toggle")
    async def marriage_toggle(self, ctx: commands.Context, on_off: bool = None):
        """Toggle Marriage for current server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off if on_off else not (await self.config.guild(ctx.guild).toggle())
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
            loaded = self.bot.get_cog("Cookies")
            if not loaded:
                return await ctx.send(
                    f"Uh oh, Cookies isn't loaded. Load it using `{ctx.clean_prefix}load cookies`"
                )
        await self.config.guild(ctx.guild).currency.set(currency)
        await ctx.tick()

    @marriage.command(name="multiple")
    async def marriage_multiple(self, ctx: commands.Context, state: bool):
        """Enable/disable whether members can be married to multiple people at once."""
        if not state:
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

    @marriage.group(autohelp=True, name="actions")
    async def marriage_actions(self, ctx: commands.Context):
        """Custom actions"""
        pass

    @marriage_actions.command(name="add")
    async def marriage_actions_add(
        self,
        ctx: commands.Context,
        action: str,
        temper: int,
        price: int,
        consent_description: typing.Optional[str],
        consent: typing.Optional[bool],
        description: str,
    ):
        """Add custom action.

        Available parametres are `{author}` and `{target}`"""
        if action in await self._get_actions(ctx):
            return await ctx.send("Uh oh, that's already a registered action.")
        await self.config.guild(ctx.guild).custom_actions.set_raw(
            action,
            value={
                "temper": temper,
                "price": price,
                "require_consent": consent,
                "consent_description": consent_description,
                "description": description,
            },
        )
        await ctx.tick()

    @marriage_actions.command(name="remove")
    async def marriage_actions_remove(self, ctx: commands.Context, action: str):
        """Remove custom action."""
        if action not in await self._get_actions(ctx):
            return await ctx.send("Uh oh, that's not a registered action.")
        if await self._is_custom(ctx, action):
            await self.config.guild(ctx.guild).custom_actions.clear_raw(action)
        else:
            async with self.config.guild(ctx.guild).removed_actions() as removed:
                removed.append(action)
        await ctx.tick()

    @marriage_actions.command(name="show")
    async def marriage_actions_show(self, ctx: commands.Context, action: str):
        """Show custom action."""
        if await self._is_removed(ctx, action):
            return await ctx.send("Uh oh, that's not a registered action.")

        data = await self.config.guild(ctx.guild).custom_actions.get_raw(
            action, default=None
        )
        if not data:
            data = self._DEFAULT_ACTIONS.get(action)
            if not data:
                return await ctx.send("Uh oh, that's not a registered action.")
        await ctx.send(
            f"**{action}**\n"
            f"- temper: {data.get('temper')}\n"
            f"- price: {data.get('price')}\n"
            f"- require_consent: {data.get('require_consent')}\n"
            f"- consent_description: {data.get('consent_description')}\n"
            f"- description: {data.get('description')}"
        )

    @marriage_actions.command(name="list")
    async def marriage_actions_list(self, ctx: commands.Context):
        """Show custom action."""
        actions = await self._get_actions(ctx)
        await ctx.send(humanize_list(actions))

    @marriage.group(autohelp=True, name="gifts")
    async def marriage_gifts(self, ctx: commands.Context):
        """Custom gifts"""
        pass

    @marriage_gifts.command(name="add")
    async def marriage_gifts_add(
        self, ctx: commands.Context, gift: str, temper: int, price: int
    ):
        """Add custom gift.

        Available parametres are `{author}` and `{target}`"""
        if gift in await self._get_gifts(ctx):
            return await ctx.send("Uh oh, that's already a registered gift.")
        await self.config.guild(ctx.guild).custom_gifts.set_raw(
            gift, value={"temper": temper, "price": price}
        )
        await ctx.tick()

    @marriage_gifts.command(name="remove")
    async def marriage_gifts_remove(self, ctx: commands.Context, gift: str):
        """Remove custom gift."""
        if gift not in await self._get_gifts(ctx):
            return await ctx.send("Uh oh, that's not a registered gift.")
        if await self._is_custom(ctx, gift):
            await self.config.guild(ctx.guild).custom_gifts.clear_raw(gift)
        else:
            async with self.config.guild(ctx.guild).removed_gifts() as removed:
                removed.append(gift)
        await ctx.tick()

    @marriage_gifts.command(name="show")
    async def marriage_gifts_show(self, ctx: commands.Context, gift: str):
        """Show custom gift."""
        if await self._is_removed(ctx, gift):
            return await ctx.send("Uh oh, that's not a registered gift.")

        data = await self.config.guild(ctx.guild).custom_gifts.get_raw(
            gift, default=None
        )
        if not data:
            data = self._DEFAULT_GIFTS.get(gift)
            if not data:
                return await ctx.send("Uh oh, that's not a registered gift.")
        await ctx.send(
            f"**{gift}**\n"
            f"- temper: {data.get('temper')}\n"
            f"- price: {data.get('price')}"
        )

    @marriage_gifts.command(name="list")
    async def marriage_gifts_list(self, ctx: commands.Context):
        """Show custom gift."""
        gifts = await self._get_gifts(ctx)
        await ctx.send(humanize_list(gifts))

    @commands.guild_only()
    @commands.command()
    async def addabout(self, ctx: commands.Context, *, about: str):
        """Add your about text"""
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send("Marriage is not enabled!")
        if len(about) > 1000:
            return await ctx.send("Uh oh, this is not an essay.")
        await self.config.member(ctx.author).about.set(about)
        await ctx.tick()

    @commands.guild_only()
    @commands.command()
    async def about(self, ctx: commands.Context, member: discord.Member = None):
        """Display your or someone else's about"""
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send("Marriage is not enabled!")
        if not member:
            member = ctx.author
        conf = self.config.member(member)

        is_married = await conf.married()
        if not is_married:
            is_divorced = await conf.married()
            if not is_divorced:
                rs_status = "Single"
            else:
                rs_status = "Divorced"
        else:
            rs_status = "Married"
            spouse_ids = await conf.current()
            spouses = []
            for spouse_id in spouse_ids:
                spouse = ctx.guild.get_member(spouse_id)
                if not spouse:
                    continue
                spouse = spouse.name
                spouses.append(spouse)
            if spouses == []:
                spouse_header = "Spouse:"
                spouse_text = "None"
            else:
                spouse_text = humanize_list(spouses)
                if len(spouses) == 1:
                    spouse_header = "Spouse:"
                else:
                    spouse_header = "Spouses:"
        marcount = await conf.marcount()
        if marcount == 1:
            been_married = f"{marcount} time"
        else:
            been_married = f"{marcount} times"
        if marcount != 0:
            exes_ids = await conf.exes()
            if exes_ids == []:
                ex_text = "None"
            else:
                exes = []
                for ex_id in exes_ids:
                    ex = ctx.guild.get_member(ex_id)
                    if not ex:
                        continue
                    ex = ex.name
                    exes.append(ex)
                if exes == []:
                    ex_text = "None"
                else:
                    ex_text = humanize_list(exes)
        crush = ctx.guild.get_member(await conf.crush())
        if not crush:
            crush = "None"
        else:
            crush = crush.name
        if await self.config.guild(ctx.guild).currency() == 0:
            currency = await bank.get_currency_name(ctx.guild)
            bal = await bank.get_balance(member)
        else:
            bal = int(await self.bot.get_cog("Cookies").config.member(member).cookies())
            currency = ":cookie:"
        gifts = await conf.gifts.get_raw()
        giftos = []
        for gift in gifts:
            amount = gifts.get(gift)
            if amount > 0:
                if amount == 1:
                    textos = f"{gift} - {amount} pc"
                else:
                    textos = f"{gift} - {amount} pcs"
                giftos.append(textos)
            else:
                continue
        if giftos == []:
            gift_text = "None"
        else:
            gift_text = humanize_list(giftos)
        e = discord.Embed(colour=member.color)
        e.set_author(name=f"{member.name}'s Profile", icon_url=member.avatar_url)
        e.set_footer(text=f"{member.name}#{member.discriminator} ({member.id})")
        e.set_thumbnail(url=member.avatar_url)
        e.add_field(name="About:", value=await conf.about(), inline=False)
        e.add_field(name="Status:", value=rs_status)
        if is_married:
            e.add_field(name=spouse_header, value=spouse_text)
        e.add_field(name="Crush:", value=crush)
        e.add_field(name="Temper:", value=await conf.temper())
        e.add_field(name="Been married:", value=been_married)
        if await conf.marcount() != 0:
            e.add_field(name="Ex spouses:", value=ex_text)
        e.add_field(name="Balance:", value=f"{bal} {currency}")
        e.add_field(name="Available gifts:", value=gift_text)

        await ctx.send(embed=e)

    @commands.guild_only()
    @commands.command()
    async def exes(self, ctx: commands.Context, member: discord.Member = None):
        """Display your or someone else's exes"""
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send("Marriage is not enabled!")
        if not member:
            member = ctx.author
        exes_ids = await self.config.member(member).exes()
        exes = []
        for ex_id in exes_ids:
            ex = ctx.guild.get_member(ex_id)
            if not ex:
                continue
            ex = ex.name
            exes.append(ex)
        if exes == []:
            ex_text = "unknown"
        else:
            ex_text = humanize_list(exes)
        await ctx.send(f"{member.mention}'s exes are: {ex_text}")

    @commands.guild_only()
    @commands.command()
    async def crush(self, ctx: commands.Context, member: discord.Member = None):
        """Tell us who you have a crush on"""
        if not await self.config.guild(ctx.guild).toggle():
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
    async def marry(self, ctx: commands.Context, member: discord.Member):
        """Marry the love of your life!"""
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send("Marriage is not enabled!")
        if member.id == ctx.author.id:
            return await ctx.send("You cannot marry yourself!")
        if member.id in await self.config.member(ctx.author).current():
            return await ctx.send("You two are already married!")
        if not await self.config.guild(ctx.guild).multi():
            if await self.config.member(ctx.author).married():
                return await ctx.send("You're already married!")
            if await self.config.member(member).married():
                return await ctx.send("They're already married!")
        await ctx.send(
            f"{ctx.author.mention} has asked {member.mention} to marry them!\n"
            f"{member.mention}, what do you say?"
        )
        pred = MessagePredicate.yes_or_no(ctx, ctx.channel, member)
        try:
            await self.bot.wait_for("message", timeout=75, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to respond!")
        if not pred.result:
            return await ctx.send("Oh no... I was looking forward to the cerenomy...")
        default_amount = await self.config.guild(ctx.guild).marprice()
        author_marcount = await self.config.member(ctx.author).marcount()
        target_marcount = await self.config.member(member).marcount()

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
        amount = int(round(amount))
        if await self.config.guild(ctx.guild).currency() == 0:
            currency = await bank.get_currency_name(ctx.guild)
            end_amount = f"{amount} {currency}"
            if await bank.can_spend(ctx.author, amount):
                if await bank.can_spend(member, amount):
                    await bank.withdraw_credits(ctx.author, amount)
                    await bank.withdraw_credits(member, amount)
                else:
                    return await ctx.send(f"Uh oh, you two cannot afford this...")
            else:
                return await ctx.send(f"Uh oh, you two cannot afford this...")
        else:
            author_cookies = int(
                await self.bot.get_cog("Cookies").config.member(ctx.author).cookies()
            )
            target_cookies = int(
                await self.bot.get_cog("Cookies").config.member(member).cookies()
            )
            end_amount = f"{amount} :cookie:"
            if amount <= author_cookies:
                if amount <= target_cookies:
                    await self.bot.get_cog("Cookies").config.member(
                        ctx.author
                    ).cookies.set(author_cookies - amount)
                    await self.bot.get_cog("Cookies").config.member(member).cookies.set(
                        target_cookies - amount
                    )
                else:
                    return await ctx.send(f"Uh oh, you two cannot afford this...")
            else:
                return await ctx.send(f"Uh oh, you two cannot afford this...")
        await self.config.member(ctx.author).marcount.set(author_marcount + 1)
        await self.config.member(member).marcount.set(target_marcount + 1)

        await self.config.member(ctx.author).married.set(True)
        await self.config.member(member).married.set(True)

        await self.config.member(ctx.author).divorced.set(False)
        await self.config.member(member).divorced.set(False)

        async with self.config.member(ctx.author).current() as acurrent:
            acurrent.append(member.id)
        async with self.config.member(member).current() as tcurrent:
            tcurrent.append(ctx.author.id)
        await self.config.member(ctx.author).temper.set(100)
        await self.config.member(member).temper.set(100)

        await ctx.send(
            f":church: {ctx.author.mention} and {member.mention} are now a happy married couple! "
            f"Congrats! :tada:\n*You both paid {end_amount}.*"
        )

    @commands.guild_only()
    @commands.command()
    async def divorce(
        self, ctx: commands.Context, member: discord.Member, court: bool = False
    ):
        """Divorce your current spouse"""
        if not await self.config.guild(ctx.guild).toggle():
            return await ctx.send("Marriage is not enabled!")
        if member.id == ctx.author.id:
            return await ctx.send("You cannot divorce yourself!")
        if member.id not in await self.config.member(ctx.author).current():
            return await ctx.send("You two aren't married!")
        if not court:
            await ctx.send(
                f"{ctx.author.mention} wants to divorce you, {member.mention}, do you accept?\n"
                "If you say no, you will go to the court."
            )
            pred = MessagePredicate.yes_or_no(ctx, ctx.channel, member)
            await self.bot.wait_for("message", check=pred)
            if pred.result:
                default_amount = await self.config.guild(ctx.guild).marprice()
                default_multiplier = await self.config.guild(ctx.guild).divprice()
                author_marcount = await self.config.member(ctx.author).marcount()
                target_marcount = await self.config.member(member).marcount()

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
                amount = int(round(amount))
                if await self.config.guild(ctx.guild).currency() == 0:
                    currency = await bank.get_currency_name(ctx.guild)
                    end_amount = f"You both paid {amount} {currency}"
                    if await bank.can_spend(ctx.author, amount):
                        if await bank.can_spend(member, amount):
                            await bank.withdraw_credits(ctx.author, amount)
                            await bank.withdraw_credits(member, amount)
                        else:
                            return await ctx.send(
                                f"Uh oh, you two cannot afford this... But you can force a court by "
                                f"doing `{ctx.clean_prefix}divorce {member.mention} yes`"
                            )
                    else:
                        return await ctx.send(
                            f"Uh oh, you two cannot afford this... But you can force a court by "
                            f"doing `{ctx.clean_prefix}divorce {member.mention} yes`"
                        )
                else:
                    author_cookies = int(
                        await self.bot.get_cog("Cookies")
                        .config.member(ctx.author)
                        .cookies()
                    )
                    target_cookies = int(
                        await self.bot.get_cog("Cookies")
                        .config.member(member)
                        .cookies()
                    )
                    end_amount = f"You both paid {amount} :cookie:"
                    if amount <= author_cookies:
                        if amount <= target_cookies:
                            await self.bot.get_cog("Cookies").config.member(
                                ctx.author
                            ).cookies.set(author_cookies - amount)
                            await self.bot.get_cog("Cookies").config.member(
                                member
                            ).cookies.set(target_cookies - amount)
                        else:
                            return await ctx.send(
                                f"Uh oh, you two cannot afford this... But you can force a court by "
                                f"doing `{ctx.clean_prefix}divorce {member.mention} yes`"
                            )
                    else:
                        return await ctx.send(
                            f"Uh oh, you two cannot afford this... But you can force a court by "
                            f"doing `{ctx.clean_prefix}divorce {member.mention} yes`"
                        )
            else:
                court = True
        if court:
            court = random.randint(1, 100)
            court_multiplier = court / 100
            if await self.config.guild(ctx.guild).currency() == 0:
                currency = await bank.get_currency_name(ctx.guild)
                abal = await bank.get_balance(ctx.author)
                tbal = await bank.get_balance(member)
                aamount = int(round(abal * court_multiplier))
                tamount = int(round(tbal * court_multiplier))
                end_amount = f"{ctx.author.name} paid {aamount} {currency}, {member.name} paid {tamount} {currency}"
                await bank.withdraw_credits(ctx.author, aamount)
                await bank.withdraw_credits(member, tamount)
            else:
                author_cookies = int(
                    await self.bot.get_cog("Cookies")
                    .config.member(ctx.author)
                    .cookies()
                )
                target_cookies = int(
                    await self.bot.get_cog("Cookies").config.member(member).cookies()
                )
                aamount = int(round(author_cookies * court_multiplier))
                tamount = int(round(target_cookies * court_multiplier))
                end_amount = f"{ctx.author.name} paid {aamount} :cookie:, {member.name} paid {tamount} :cookie:"
                await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(
                    author_cookies - aamount
                )
                await self.bot.get_cog("Cookies").config.member(member).cookies.set(
                    target_cookies - tamount
                )
        async with self.config.member(ctx.author).current() as acurrent:
            acurrent.remove(member.id)
        async with self.config.member(member).current() as tcurrent:
            tcurrent.remove(ctx.author.id)
        async with self.config.member(ctx.author).exes() as aexes:
            aexes.append(member.id)
        async with self.config.member(member).exes() as texes:
            texes.append(ctx.author.id)
        if len(await self.config.member(ctx.author).current()) == 0:
            await self.config.member(ctx.author).married.set(False)
            await self.config.member(ctx.author).divorced.set(True)
        if len(await self.config.member(member).current()) == 0:
            await self.config.member(member).married.set(False)
            await self.config.member(member).divorced.set(True)
        await ctx.send(
            f":broken_heart: {ctx.author.mention} and {member.mention} got divorced...\n*{end_amount}.*"
        )

    @commands.guild_only()
    @commands.command()
    async def perform(
        self,
        ctx: commands.Context,
        action: str,
        member: discord.Member,
        item: str = None,
    ):
        """Do something with someone"""
        gc = self.config.guild
        mc = self.config.member
        actions = await self._get_actions(ctx)
        gifts = await self._get_gifts(ctx)

        if not await gc(ctx.guild).toggle():
            return await ctx.send("Marriage is not enabled!")

        if member.id == ctx.author.id:
            return await ctx.send("You cannot perform anything with yourself!")

        if action in actions:
            exertion = await gc(ctx.guild).custom_actions.get_raw(action, default=None)
            if not exertion:
                exertion = self._DEFAULT_ACTIONS.get(action)
            endtext = exertion.get("description").format(
                author=ctx.author.mention, target=member.mention
            )

            author_gift = 0
            member_gift = -1

        elif action == "gift":
            exertion = await gc(ctx.guild).custom_gifts.get_raw(item, default=None)
            if not exertion:
                exertion = self._DEFAULT_GIFTS.get(item)

            if item not in gifts:
                return await ctx.send(f"Available gifts are: {humanize_list(gifts)}")

            endtext_format = await gc(ctx.guild).gift_text()
            endtext = endtext_format.format(
                author=ctx.author.mention, item=item, target=member.mention
            )

            author_gift = await mc(ctx.author).gifts.get_raw(item, default=0)
            member_gift = await mc(member).gifts.get_raw(item, default=0)

        else:
            return await ctx.send(f"Available actions are: {humanize_list(actions)}")

        temper = exertion.get("temper")
        price = exertion.get("price")

        if author_gift == 0:
            price = int(round(price))
            if await self.config.guild(ctx.guild).currency() == 0:
                if await bank.can_spend(ctx.author, price):
                    await bank.withdraw_credits(ctx.author, price)
                    member_gift += 1
                    author_gift -= 1
                else:
                    return await ctx.send("Uh oh, you cannot afford this.")
            else:
                author_cookies = int(
                    await self.bot.get_cog("Cookies")
                    .config.member(ctx.author)
                    .cookies()
                )
                if price <= author_cookies:
                    await self.bot.get_cog("Cookies").config.member(
                        ctx.author
                    ).cookies.set(author_cookies - price)
                    member_gift += 1
                    author_gift -= 1
                else:
                    return await ctx.send("Uh oh, you cannot afford this.")
        else:
            author_gift -= 1
            member_gift += 1
        if author_gift >= 0:
            await mc(ctx.author).gifts.set_raw(item, value=author_gift)
        if member_gift > 0:
            await mc(member).gifts.set_raw(item, value=member_gift)
        if exertion.get("require_consent"):
            await ctx.send(
                exertion.get("consent_description").format(
                    author=ctx.author.mention, target=member.mention
                )
            )
            pred = MessagePredicate.yes_or_no(ctx, ctx.channel, member)
            try:
                await self.bot.wait_for("message", timeout=60, check=pred)
            except asyncio.TimeoutError:
                return await ctx.send(
                    "They took too long. Try again later, please. (You didn't lose any temper.)"
                )
            if pred.result:
                t_temp = await mc(member).temper()
                t_missing = 100 - t_temp
                if t_missing != 0:
                    if temper <= t_missing:
                        await mc(member).temper.set(t_temp + temper)
                    else:
                        await mc(member).temper.set(100)
                a_temp = await mc(ctx.author).temper()
                a_missing = 100 - a_temp
                if a_missing != 0:
                    if temper <= a_missing:
                        await mc(ctx.author).temper.set(a_temp + temper)
                    else:
                        await mc(ctx.author).temper.set(100)
                endtext = exertion.get("description").format(
                    author=ctx.author.mention, target=member.mention
                )
            else:
                a_temp = await mc(ctx.author).temper()
                if temper < a_temp:
                    await mc(ctx.author).temper.set(a_temp - temper)
                else:
                    await mc(ctx.author).temper.set(0)
                endtext = "They do not wish to do that."
        else:
            t_temp = await mc(member).temper()
            t_missing = 100 - t_temp
            if t_missing != 0:
                if temper <= t_missing:
                    await mc(member).temper.set(t_temp + temper)
                else:
                    await mc(member).temper.set(100)
            a_temp = await mc(ctx.author).temper()
            a_missing = 100 - a_temp
            if a_missing != 0:
                if temper <= a_missing:
                    await mc(ctx.author).temper.set(a_temp + temper)
                else:
                    await mc(ctx.author).temper.set(100)
        spouses = await mc(ctx.author).current()
        if member.id in spouses:
            pass
        else:
            if await mc(ctx.author).married():
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
                            await self.config.member(spouse).married.set(False)
                            await self.config.member(spouse).divorced.set(True)
                        if await self.config.guild(ctx.guild).currency() == 0:
                            abal = await bank.get_balance(ctx.author)
                            tamount = int(round(tbal * court_multiplier))
                            await bank.withdraw_credits(ctx.author, abal)
                            await bank.deposit_credits(spouse, abal)
                        else:
                            author_cookies = int(
                                await self.bot.get_cog("Cookies")
                                .config.member(ctx.author)
                                .cookies()
                            )
                            spouse_cookies = int(
                                await self.bot.get_cog("Cookies")
                                .config.member(spouse)
                                .cookies()
                            )
                            await self.bot.get_cog("Cookies").config.member(
                                ctx.author
                            ).cookies.set(0)
                            await self.bot.get_cog("Cookies").config.member(
                                spouse
                            ).cookies.set(spouse_cookies + author_cookies)
                        endtext = f"{endtext}\n:broken_heart: {ctx.author.mention} has made {spouse.mention} completely unhappy "
                        f"with their actions so {spouse.mention} left them and took all their money!"
        await ctx.send(endtext)

    async def _get_actions(self, ctx):
        actions = list(self._DEFAULT_ACTIONS.keys())
        removed_actions = await self.config.guild(ctx.guild).removed_actions()
        custom_actions = await self.config.guild(ctx.guild).custom_actions()
        if len(custom_actions) == 0:
            custom_actions = list()
        else:
            custom_actions = list(custom_actions.keys())

        for removed in removed_actions:
            actions.remove(removed)

        actions.extend(custom_actions)

        return actions

    async def _get_gifts(self, ctx):
        gifts = list(self._DEFAULT_GIFTS.keys())
        removed_gifts = await self.config.guild(ctx.guild).removed_gifts()
        custom_gifts = await self.config.guild(ctx.guild).custom_gifts()
        if len(custom_gifts) == 0:
            custom_gifts = list()
        else:
            custom_gifts = list(custom_gifts.keys())

        for removed in removed_gifts:
            gifts.remove(removed)

        gifts.extend(custom_gifts)

        return gifts

    async def _get_all(self, ctx):
        all_items = list()
        all_items.extend(await self._get_actions(ctx))
        all_items.extend(await self._get_gifts(ctx))
        return all_items

    async def _is_custom(self, ctx, item):
        actions = await self.config.guild(ctx.guild).custom_actions()
        if len(actions) == 0:
            actions = list()
        else:
            actions = list(actions.keys())

        gifts = await self.config.guild(ctx.guild).custom_gifts()
        if len(gifts) == 0:
            gifts = list()
        else:
            gifts = list(gifts.keys())

        return item in actions or item in gifts

    async def _is_removed(self, ctx, item):
        actions = await self.config.guild(ctx.guild).removed_actions()
        gifts = await self.config.guild(ctx.guild).removed_gifts()

        return item in actions or item in gifts