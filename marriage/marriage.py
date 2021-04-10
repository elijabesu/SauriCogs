import discord
import asyncio
import random
import datetime
import typing

from redbot.core import Config, checks, commands, bank
from redbot.core.utils.chat_formatting import humanize_list, box
from redbot.core.utils.predicates import MessagePredicate

from redbot.core.bot import Red


class Marriage(commands.Cog):
    """
    Marry, divorce, and give gifts to other members.
    """

    __version__ = "1.6.2"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=5465461324979524, force_registration=True
        )
        default_user = {
            "married": False,
            "current": [],
            "divorced": False,
            "exes": [],
            "about": "I'm mysterious.",
            "crush": None,
            "marcount": 0,
            "dircount": 0,
            "contentment": 100,
            "gifts": {
                # "gift": owned pcs
            },
        }

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

        self.config.register_global(
            is_global=False,
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

        self.config.register_member(**default_user)
        self.config.register_user(**default_user)

    async def red_delete_data_for_user(self, *, requester, user_id):
        await self.config.user_from_id(user_id).clear()
        for guild in self.bot.guilds:
            await self.config.member_from_ids(guild.id, user_id).clear()
            for member in guild.members:
                member_exes = await self.config.member(member).exes()
                member_spouses = await self.config.member(member).spouses()
                if user_id in member_exes:
                    member_exes.remove(user_id)
                    await self.config.member(member).exes.set(member_exes)
                if user_id in member_spouses:
                    member_spouses.remove(user_id)
                    if len(member_spouses) == 0:
                        await self.config.member(member).married.set(False)
                    await self.config.member(member).spouses.set(member_spouses)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        context = super().format_help_for_context(ctx)
        return f"{context}\n\nVersion: {self.__version__}"

    @property
    def _DEFAULT_ACTIONS(self):
        return {
            "flirt": {
                "contentment": 5,
                "price": 0,
                "require_consent": False,
                "description": ":heart_eyes: {author} is flirting with {target}",
            },
            "fuck": {
                "contentment": 15,
                "price": 0,
                "require_consent": True,
                "consent_description": "{author} wants to bang you, {target}, give consent?",
                "description": ":smirk: {author} banged {target}",
            },
            "dinner": {
                "contentment": 15,
                "price": 25,
                "require_consent": False,
                "description": ":ramen: {author} took {target} on a fancy dinner",
            },
            "date": {
                "contentment": 10,
                "price": 0,
                "require_consent": False,
                "description": ":relaxed: {author} took {target} on a nice date",
            },
        }

    @property
    def _DEFAULT_GIFTS(self):
        return {
            "flower": {"contentment": 5, "price": 5},
            "sweets": {"contentment": 5, "price": 5},
            "alcohol": {"contentment": 5, "price": 5},
            "loveletter": {"contentment": 5, "price": 1},
            "food": {"contentment": 5, "price": 10},
            "makeup": {"contentment": 5, "price": 20},
            "car": {"contentment": 15, "price": 500},
            "yacht": {"contentment": 30, "price": 1000},
            "house": {"contentment": 60, "price": 25000},
        }

    @commands.group(autohelp=True, aliases=["marriage"])
    @commands.guild_only()
    @checks.admin()
    async def marryset(self, ctx: commands.Context):
        """Various Marriage settings."""

    @marryset.command(name="gg")
    async def marryset_gg(
        self,
        ctx: commands.Context,
        make_global: bool,
        confirmation: typing.Optional[bool],
    ):
        """Switch from per-guild to global marriage and vice versa."""
        if await self.config.is_global() == make_global:
            return await ctx.send("Uh oh, you're not really changing anything.")
        if not confirmation:
            return await ctx.send(
                "This will delete **all** current settings. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}marryset gg <make_global> yes`."
            )
        await self.config.clear_all_members()
        await self.config.clear_all_users()
        await self.config.clear_all_guilds()
        await self.config.clear_all_globals()
        await self.config.is_global.set(make_global)
        await ctx.send(f"Marriage is now {'global' if make_global else 'per-guild'}.")

    @marryset.command(name="toggle")
    async def marryset_toggle(
        self, ctx: commands.Context, on_off: typing.Optional[bool]
    ):
        """Toggle Marriage.

        If `on_off` is not provided, the state will be flipped."""
        conf = await self._get_conf_group(ctx.guild)
        target_state = on_off or not (await conf.toggle())
        await conf.toggle.set(target_state)
        await ctx.send(f"Marriage is now {'enabled' if target_state else 'disabled'}.")

    @checks.is_owner()
    @marryset.command(name="currency")
    async def marryset_currency(self, ctx: commands.Context, currency: int):
        """Set the currency that should be used.

        0 for Red's economy, 1 for SauriCogs' cookies."""
        if currency != 0:
            if currency != 1:
                return await ctx.send("Uh oh, currency can only be 0 or 1.")
            if not self.bot.get_cog("Cookies"):
                return await ctx.send(
                    f"Uh oh, Cookies isn't loaded. Load it using `{ctx.clean_prefix}load cookies`"
                )
        conf = await self._get_conf_group(ctx.guild)
        await conf.currency.set(currency)
        await ctx.tick()

    @marryset.command(name="multiple")
    async def marryset_multiple(self, ctx: commands.Context, state: bool):
        """Enable/disable whether members can be married to multiple people at once."""
        conf = await self._get_conf_group(ctx.guild)
        await conf.multi.set(state)
        await ctx.send(f"Members {'can' if state else 'cannot'} marry multiple people.")

    @marryset.command(name="marprice")
    async def marryset_marprice(self, ctx: commands.Context, price: int):
        """Set the price for getting married.

        With each past marriage, the cost of getting married is 50% more"""
        if price <= 0:
            return await ctx.send("Uh oh, price cannot be 0 or less.")
        conf = await self._get_conf_group(ctx.guild)
        await conf.marprice.set(price)
        await ctx.tick()

    @marryset.command(name="divprice")
    async def marryset_divprice(self, ctx: commands.Context, multiplier: int):
        """Set the MULTIPLIER for getting divorced.

        This is a multiplier, not the price! Default is 2."""
        if multiplier <= 1:
            return await ctx.send("Uh oh, that ain't a valia multiplier.")
        conf = await self._get_conf_group(ctx.guild)
        await conf.divprice.set(multiplier)
        await ctx.tick()

    @marryset.command(name="settings")
    async def marryset_settings(self, ctx: commands.Context):
        """See current settings."""
        is_global = await self.config.is_global()
        conf = await self._get_conf_group(ctx.guild)
        data = (
            await self.config.all()
            if is_global
            else await self.config.guild(ctx.guild).all()
        )
        currency_used = (
            "Red's economy" if data["currency"] == 0 else "SauriCogs' cookies"
        )

        actions_keys, gifts_keys = await self._get_actions(ctx), await self._get_gifts(
            ctx
        )

        custom_actions = await conf.custom_actions()
        custom_gifts = await conf.custom_gifts()

        actions, gifts = "", ""

        if len(actions_keys) == 0:
            actions = "None"
        else:
            for key in actions_keys:
                actions += f"{key.capitalize()}: "
                if await self._is_custom(ctx, key):
                    actions += (
                        f"{custom_actions.get(key).get('contentment')} contentment, "
                        f"{custom_actions.get(key).get('price')} price\n"
                    )
                else:
                    actions += (
                        f"{self._DEFAULT_ACTIONS.get(key).get('contentment')} contentment, "
                        f"{self._DEFAULT_ACTIONS.get(key).get('price')} price\n"
                    )
        if len(gifts_keys) == 0:
            gifts = "None"
        else:
            for key in gifts_keys:
                gifts += f"{key.capitalize()}: "
                if await self._is_custom(ctx, key):
                    gifts += (
                        f"{custom_gifts.get(key).get('contentment')} contentment, "
                        f"{custom_gifts.get(key).get('price')} price\n"
                    )
                else:
                    gifts += (
                        f"{self._DEFAULT_GIFTS.get(key).get('contentment')} contentment, "
                        f"{self._DEFAULT_GIFTS.get(key).get('price')} price\n"
                    )

        embed = discord.Embed(
            colour=await ctx.embed_colour(), timestamp=datetime.datetime.now()
        )
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.title = "**__Marriage settings:__**"
        embed.add_field(name="Global:", value=str(is_global))
        embed.add_field(name="Enabled*:", value=str(data["toggle"]))
        embed.add_field(name="Currency:", value=currency_used)
        embed.add_field(name="Marriage price:", value=str(data["marprice"]))
        embed.add_field(name="Divorce price:", value=str(data["divprice"]))
        embed.add_field(name="Multiple spouses:", value=str(data["multi"]))
        embed.add_field(name="Actions:", value=actions.strip())
        embed.add_field(name="Gifts:", value=gifts.strip())
        embed.set_footer(text="*required to function properly")
        await ctx.send(embed=embed)

    @marryset.group(autohelp=True, name="actions")
    async def marryset_actions(self, ctx: commands.Context):
        """Custom actions"""

    @marryset_actions.command(name="add")
    async def marryset_actions_add(
        self,
        ctx: commands.Context,
        action: str,
        contentment: int,
        price: int,
        consent_description: str,
        consent: bool,
        description: str,
    ):
        """Add a custom action.

        Available parameters are `{author}` and `{target}`

        If you don't want consent_description, use empty quotation marks."""
        if action in await self._get_actions(ctx):
            return await ctx.send("Uh oh, that's already a registerOHed action.")
        conf = await self._get_conf_group(ctx.guild)
        await conf.custom_actions.set_raw(
            action,
            value={
                "contentment": contentment,
                "price": price,
                "require_consent": consent,
                "consent_description": consent_description,
                "description": description,
            },
        )
        await ctx.tick()

    @marryset_actions.command(name="remove")
    async def marryset_actions_remove(self, ctx: commands.Context, action: str):
        """Remove a custom action."""
        if action not in await self._get_actions(ctx):
            return await ctx.send("Uh oh, that's not a registered action.")

        conf = await self._get_conf_group(ctx.guild)
        if await self._is_custom(ctx, action):
            await conf.custom_actions.clear_raw(action)
        else:
            async with conf.removed_actions() as removed:
                removed.append(action)
        await ctx.tick()

    @marryset_actions.command(name="show")
    async def marryset_actions_show(self, ctx: commands.Context, action: str):
        """Show a custom action."""
        if await self._is_removed(ctx, action):
            return await ctx.send("Uh oh, that's not a registered action.")

        conf = await self._get_conf_group(ctx.guild)
        data = await conf.custom_actions.get_raw(action, default=None)
        if not data:
            data = self._DEFAULT_ACTIONS.get(action)
        if not data:
            return await ctx.send("Uh oh, that's not a registered action.")
        await ctx.send(
            box(
                f"""= {action.capitalize()} =
contentment:: {data.get('contentment')}
price:: {data.get('price')}
require_consent:: {data.get('require_consent')}
consent_description:: {data.get('consent_description')}
description:: {data.get('description')}""",
                lang="asciidoc",
            )
        )

    @marryset_actions.command(name="list")
    async def marryset_actions_list(self, ctx: commands.Context):
        """Show custom action."""
        actions = await self._get_actions(ctx)
        await ctx.send(humanize_list(actions))

    @marryset.group(autohelp=True, name="gifts")
    async def marryset_gifts(self, ctx: commands.Context):
        """Custom gifts"""

    @marryset_gifts.command(name="add")
    async def marryset_gifts_add(
        self, ctx: commands.Context, gift: str, contentment: int, price: int
    ):
        """Add a custom gift.

        Available parameters are `{author}` and `{target}`"""
        if gift in await self._get_gifts(ctx):
            return await ctx.send("Uh oh, that's already a registered gift.")

        conf = await self._get_conf_group(ctx.guild)
        await conf.custom_gifts.set_raw(
            gift, value={"contentment": contentment, "price": price}
        )
        await ctx.tick()

    @marryset_gifts.command(name="remove")
    async def marryset_gifts_remove(self, ctx: commands.Context, gift: str):
        """Remove a custom gift."""
        if gift not in await self._get_gifts(ctx):
            return await ctx.send("Uh oh, that's not a registered gift.")

        conf = await self._get_conf_group(ctx.guild)
        if await self._is_custom(ctx, gift):
            await conf.custom_gifts.clear_raw(gift)
        else:
            async with conf.removed_gifts() as removed:
                removed.append(gift)
        await ctx.tick()

    @marryset_gifts.command(name="show")
    async def marryset_gifts_show(self, ctx: commands.Context, gift: str):
        """Show a custom gift."""
        if await self._is_removed(ctx, gift):
            return await ctx.send("Uh oh, that's not a registered gift.")

        conf = await self._get_conf_group(ctx.guild)
        data = await conf.custom_gifts.get_raw(gift, default=None)
        if not data:
            data = self._DEFAULT_GIFTS.get(gift)
        if not data:
            return await ctx.send("Uh oh, that's not a registered gift.")
        await ctx.send(
            box(
                f"""= {gift.capitalize()} =
contentment:: {data.get('contentment')}
price:: {data.get('price')}""",
                lang="asciidoc",
            )
        )

    @marryset_gifts.command(name="list")
    async def marryset_gifts_list(self, ctx: commands.Context):
        """Show custom gift."""
        gifts = await self._get_gifts(ctx)
        await ctx.send(humanize_list(gifts))

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def about(
        self, ctx: commands.Context, member: typing.Optional[discord.Member]
    ):
        """Display your or someone else's about"""
        conf = await self._get_conf_group(ctx.guild)
        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")
        if not member:
            member = ctx.author
        m_conf = await self._get_user_conf(member)

        is_married = await m_conf.married()
        if not is_married:
            rs_status = "Single" if not await m_conf.divorced() else "Divorced"
        else:
            rs_status = "Married"
            spouse_ids = await m_conf.current()
            spouses = []
            for spouse_id in spouse_ids:
                spouse = self.bot.get_user(spouse_id)
                if spouse:
                    spouses.append(spouse.name)
            if spouses == []:
                spouse_header = "Spouse:"
                spouse_text = "None"
            else:
                spouse_text = humanize_list(spouses)
                spouse_header = "Spouse:" if len(spouses) == 1 else "Spouses:"
        marcount = await m_conf.marcount()
        been_married = f"{marcount} time" if marcount == 1 else f"{marcount} times"
        if marcount != 0:
            exes_ids = await m_conf.exes()
            if exes_ids == []:
                ex_text = "None"
            else:
                exes = list()
                for ex_id in exes_ids:
                    ex = self.bot.get_user(ex_id)
                    if not ex:
                        continue
                    ex = ex.name
                    exes.append(ex)
                ex_text = "None" if exes == [] else humanize_list(exes)
        crush = self.bot.get_user(await m_conf.crush())
        crush = "None" if not crush else crush.name
        if await conf.currency() == 0:
            currency = await bank.get_currency_name(ctx.guild)
            bal = await bank.get_balance(member)
        else:
            bal = await self._get_cookies(member)
            currency = ":cookie:"
        gifts = await m_conf.gifts.get_raw()
        giftos = list()
        for gift in gifts:
            amount = gifts.get(gift)
            if amount > 0:
                textos = (
                    f"{gift} - {amount} pc" if amount == 1 else f"{gift} - {amount} pcs"
                )
                giftos.append(textos)
        gift_text = "None" if giftos == [] else humanize_list(giftos)
        e = discord.Embed(colour=member.color)
        e.set_author(name=f"{member.name}'s Profile", icon_url=member.avatar_url)
        e.set_footer(text=f"{member.name}#{member.discriminator} ({member.id})")
        e.set_thumbnail(url=member.avatar_url)
        e.add_field(name="About:", value=await m_conf.about(), inline=False)
        e.add_field(name="Status:", value=rs_status)
        if is_married:
            e.add_field(name=spouse_header, value=spouse_text)
        e.add_field(name="Crush:", value=crush)
        e.add_field(name="Contentment:", value=await m_conf.contentment())
        e.add_field(name="Been married:", value=been_married)
        if await m_conf.marcount() != 0:
            e.add_field(name="Ex spouses:", value=ex_text)
        e.add_field(name="Balance:", value=f"{bal} {currency}")
        e.add_field(name="Available gifts:", value=gift_text)

        await ctx.send(embed=e)

    @about.command(name="add")
    async def about_add(self, ctx: commands.Context, *, about: str):
        """Add your about text

        Maximum is 1000 characters."""
        conf = await self._get_conf_group(ctx.guild)
        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")
        if len(about) > 1000:
            return await ctx.send("Uh oh, this is not an essay.")
        m_conf = await self._get_user_conf(ctx.author)
        await m_conf.about.set(about)
        await ctx.tick()

    @commands.guild_only()
    @commands.command()
    async def exes(
        self, ctx: commands.Context, member: typing.Optional[discord.Member]
    ):
        """Display your or someone else's exes."""
        conf = await self._get_conf_group(ctx.guild)
        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")
        if not member:
            member = ctx.author
        m_conf = await self._get_user_conf(member)
        exes_ids = await m_conf.exes()
        exes = list()
        for ex_id in exes_ids:
            ex = self.bot.get_user(ex_id)
            if ex:
                exes.append(ex.name)
        ex_text = "None" if exes == [] else humanize_list(exes)
        await ctx.send(f"{member.mention}'s exes are: {ex_text}")

    @commands.guild_only()
    @commands.command()
    async def spouses(
        self, ctx: commands.Context, member: typing.Optional[discord.Member]
    ):
        """Display your or someone else's spouses."""
        conf = await self._get_conf_group(ctx.guild)
        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")
        if not member:
            member = ctx.author
        m_conf = await self._get_user_conf_group()
        spouses_ids = await m_conf(member).current()
        sp_text = ""
        for s_id in spouses_ids:
            spouse = self.bot.get_user(s_id)
            if spouse:
                sp_contentment = await m_conf(spouse).contentment()
                sp_text += f"{spouse.name}:: {sp_contentment}\n"
        if sp_text == "":
            sp_text = "None"
        await ctx.send(
            box(
                f"""= {member.name}'s spouses =
{sp_text.strip()}""",
                lang="asciidoc",
            )
        )

    @commands.guild_only()
    @commands.command()
    async def crush(
        self, ctx: commands.Context, member: typing.Optional[discord.Member]
    ):
        """Tell us who you have a crush on."""
        conf = await self._get_conf_group(ctx.guild)
        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")
        m_conf = await self._get_user_conf(ctx.author)
        if not member:
            await m_conf.crush.clear()
        else:
            if member.id == ctx.author.id:
                return await ctx.send("You cannot have a crush on yourself!")
            await m_conf.crush.set(member.id)
        await ctx.tick()

    @commands.max_concurrency(1, commands.BucketType.channel, wait=True)
    @commands.guild_only()
    @commands.command()
    async def marry(self, ctx: commands.Context, member: discord.Member):
        """Marry the love of your life!"""
        conf = await self._get_conf_group(ctx.guild)
        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")
        if member.id == ctx.author.id:
            return await ctx.send("You cannot marry yourself!")
        m_conf = await self._get_user_conf_group()
        if member.id in await m_conf(ctx.author).current():
            return await ctx.send("You two are already married!")
        if not await conf.multi():
            if await m_conf(ctx.author).married():
                return await ctx.send("You're already married!")
            if await m_conf(member).married():
                return await ctx.send("They're already married!")
        await ctx.send(
            f"{ctx.author.mention} has asked {member.mention} to marry them!\n"
            f"{member.mention}, what do you say?"
        )
        pred = MessagePredicate.yes_or_no(ctx, ctx.channel, member)
        try:
            await self.bot.wait_for("message", timeout=120, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("Oh no... I was looking forward to the cerenomy...")
        if not pred.result:
            return await ctx.send("Oh no... I was looking forward to the cerenomy...")
        default_amount = await conf.marprice()
        author_marcount = await m_conf(ctx.author).marcount()
        target_marcount = await m_conf(member).marcount()

        author_multiplier = author_marcount / 2 + 1
        target_multiplier = target_marcount / 2 + 1

        multiplier = (
            target_multiplier
            if author_multiplier <= target_multiplier
            else author_multiplier
        )
        amount = (
            int(round(default_amount * multiplier))
            if multiplier != 0
            else int(round(default_amount))
        )
        if await conf.currency() == 0:
            currency = await bank.get_currency_name(ctx.guild)
            end_amount = f"{amount} {currency}"
            if not await bank.can_spend(ctx.author, amount) or not await bank.can_spend(
                member, amount
            ):
                return await ctx.send(f"Uh oh, you two cannot afford this...")
            await bank.withdraw_credits(ctx.author, amount)
            await bank.withdraw_credits(member, amount)
        else:
            end_amount = f"{amount} :cookie:"
            if not await self._can_spend_cookies(
                ctx.author, amount
            ) or not await self._can_spend_cookies(member, amount):
                return await ctx.send(f"Uh oh, you two cannot afford this...")
            await self._withdraw_cookies(ctx.author, amount)
            await self._withdraw_cookies(member, amount)
        await m_conf(ctx.author).marcount.set(author_marcount + 1)
        await m_conf(member).marcount.set(target_marcount + 1)

        await m_conf(ctx.author).married.set(True)
        await m_conf(member).married.set(True)

        await m_conf(ctx.author).divorced.clear()
        await m_conf(member).divorced.clear()

        async with m_conf(ctx.author).current() as acurrent:
            acurrent.append(member.id)
        async with m_conf(member).current() as tcurrent:
            tcurrent.append(ctx.author.id)
        await m_conf(ctx.author).contentment.set(100)
        await m_conf(member).contentment.set(100)

        await ctx.send(
            f":church: {ctx.author.mention} and {member.mention} are now a happy married couple! "
            f"Congrats! :tada:\n*You both paid {end_amount}.*"
        )

    @commands.max_concurrency(1, commands.BucketType.channel, wait=True)
    @commands.guild_only()
    @commands.command()
    async def divorce(
        self, ctx: commands.Context, member: discord.Member, court: bool = False
    ):
        """Divorce your current spouse"""
        conf = await self._get_conf_group(ctx.guild)
        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")
        if member.id == ctx.author.id:
            return await ctx.send("You cannot divorce yourself!")
        m_conf = await self._get_user_conf_group()
        if member.id not in await m_conf(ctx.author).current():
            return await ctx.send("You two aren't married!")
        if not court:
            await ctx.send(
                f"{ctx.author.mention} wants to divorce you, {member.mention}, do you accept?\n"
                "If you say no, you will go to the court."
            )
            pred = MessagePredicate.yes_or_no(ctx, ctx.channel, member)
            await self.bot.wait_for("message", check=pred)
            if pred.result:
                default_amount = await conf.marprice()
                default_multiplier = await conf.divprice()
                author_marcount = await m_conf(ctx.author).marcount()
                target_marcount = await m_conf(member).marcount()

                author_multiplier = author_marcount / 2 + 1
                target_multiplier = target_marcount / 2 + 1

                multiplier = (
                    target_multiplier
                    if author_multiplier <= target_multiplier
                    else author_multiplier
                )
                amount = (
                    int(round(default_amount * multiplier * default_multiplier))
                    if multiplier != 0
                    else int(round(default_amount * default_multiplier))
                )
                if await conf.currency() == 0:
                    currency = await bank.get_currency_name(ctx.guild)
                    end_amount = f"You both paid {amount} {currency}"
                    if not await bank.can_spend(
                        ctx.author, amount
                    ) or not await bank.can_spend(member, amount):
                        return await ctx.send(
                            f"Uh oh, you two cannot afford this... But you can force a court by "
                            f"doing `{ctx.clean_prefix}divorce {member.mention} yes`"
                        )
                    await bank.withdraw_credits(ctx.author, amount)
                    await bank.withdraw_credits(member, amount)
                else:
                    end_amount = f"You both paid {amount} :cookie:"
                    if not await self._can_spend_cookies(
                        ctx.author, amount
                    ) or not await self._can_spend_cookies(member, amount):
                        return await ctx.send(
                            f"Uh oh, you two cannot afford this... But you can force a court by "
                            f"doing `{ctx.clean_prefix}divorce {member.mention} yes`"
                        )
                    await self._withdraw_cookies(ctx.author, amount)
                    await self._withdraw_cookies(member, amount)
            else:
                court = True
        if court:
            court = random.randint(1, 100)
            court_multiplier = court / 100
            if await conf.currency() == 0:
                currency = await bank.get_currency_name(ctx.guild)
                abal = await bank.get_balance(ctx.author)
                tbal = await bank.get_balance(member)
                aamount = int(round(abal * court_multiplier))
                tamount = int(round(tbal * court_multiplier))
                end_amount = f"{ctx.author.name} paid {aamount} {currency}, {member.name} paid {tamount} {currency}"
                await bank.withdraw_credits(ctx.author, aamount)
                await bank.withdraw_credits(member, tamount)
            else:
                author_cookies = await self._get_cookies(ctx.author)
                target_cookies = await self._get_cookies(member)
                aamount = int(round(author_cookies * court_multiplier))
                tamount = int(round(target_cookies * court_multiplier))
                end_amount = f"{ctx.author.name} paid {aamount} :cookie:, {member.name} paid {tamount} :cookie:"
                await self._withdraw_cookies(ctx.author, aamount)
                await self._withdraw_cookies(member, tamount)
        async with m_conf(ctx.author).current() as acurrent:
            acurrent.remove(member.id)
        async with m_conf(member).current() as tcurrent:
            tcurrent.remove(ctx.author.id)
        async with m_conf(ctx.author).exes() as aexes:
            aexes.append(member.id)
        async with m_conf(member).exes() as texes:
            texes.append(ctx.author.id)
        if len(await m_conf(ctx.author).current()) == 0:
            await m_conf(ctx.author).married.clear()
            await m_conf(ctx.author).divorced.set(True)
        if len(await m_conf(member).current()) == 0:
            await m_conf(member).married.clear()
            await m_conf(member).divorced.set(True)
        await ctx.send(
            f":broken_heart: {ctx.author.mention} and {member.mention} got divorced...\n*{end_amount}.*"
        )

    @commands.max_concurrency(1, commands.BucketType.channel, wait=True)
    @commands.guild_only()
    @commands.command()
    async def perform(
        self,
        ctx: commands.Context,
        action: str,
        member: discord.Member,
    ):
        """Do something with someone."""
        conf = await self._get_conf_group(ctx.guild)
        m_conf = await self._get_user_conf_group()
        actions = await self._get_actions(ctx)

        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")

        if member.id == ctx.author.id:
            return await ctx.send("You cannot perform anything with yourself!")

        if action not in actions:
            return await ctx.send(f"Available actions are: {humanize_list(actions)}")

        exertion = await conf.custom_actions.get_raw(action, default=None)
        if not exertion:
            exertion = self._DEFAULT_ACTIONS.get(action)
        endtext = exertion.get("description").format(
            author=ctx.author.mention, target=member.mention
        )

        contentment, price = exertion.get("contentment"), exertion.get("price")

        if await conf.currency() == 0:
            if await bank.can_spend(ctx.author, price):
                await bank.withdraw_credits(ctx.author, price)
            else:
                return await ctx.send("Uh oh, you cannot afford this.")
        else:
            if not await self._can_spend_cookies(ctx.author, price):
                return await ctx.send("Uh oh, you cannot afford this.")
            await self._withdraw_cookies(ctx.author, price)

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
                    "They took too long. Try again later, please. (You didn't lose any contentment.)"
                )
            if pred.result:
                t_temp = await m_conf(member).contentment()
                t_missing = 100 - t_temp
                if t_missing != 0:
                    if contentment <= t_missing:
                        await m_conf(member).contentment.set(t_temp + contentment)
                    else:
                        await m_conf(member).contentment.set(100)
                a_temp = await m_conf(ctx.author).contentment()
                a_missing = 100 - a_temp
                if a_missing != 0:
                    if contentment <= a_missing:
                        await m_conf(ctx.author).contentment.set(a_temp + contentment)
                    else:
                        await m_conf(ctx.author).contentment.set(100)
                endtext = exertion.get("description").format(
                    author=ctx.author.mention, target=member.mention
                )
            else:
                a_temp = await m_conf(ctx.author).contentment()
                if contentment < a_temp:
                    await m_conf(ctx.author).contentment.set(a_temp - contentment)
                else:
                    await m_conf(ctx.author).contentment.set(0)
                endtext = "They do not wish to do that."
        else:
            t_temp = await m_conf(member).contentment()
            t_missing = 100 - t_temp
            if t_missing != 0:
                if contentment <= t_missing:
                    await m_conf(member).contentment.set(t_temp + contentment)
                else:
                    await m_conf(member).contentment.set(100)
            a_temp = await m_conf(ctx.author).contentment()
            a_missing = 100 - a_temp
            if a_missing != 0:
                if contentment <= a_missing:
                    await m_conf(ctx.author).contentment.set(a_temp + contentment)
                else:
                    await m_conf(ctx.author).contentment.set(100)
        spouses = await m_conf(ctx.author).current()
        if member.id not in spouses and await m_conf(ctx.author).married():
            for sid in spouses:
                spouse = (
                    self.bot.get_user(sid)
                    if await self.config.is_global()
                    else ctx.guild.get_member(sid)
                )
                endtext = await self._maybe_divorce(ctx, spouse, endtext, contentment)
        await ctx.send(endtext)

    @commands.guild_only()
    @commands.command()
    async def gift(
        self,
        ctx: commands.Context,
        member: discord.Member,
        item: str,
    ):
        """Give someone something."""
        conf = await self._get_conf_group(ctx.guild)
        m_conf = await self._get_user_conf_group()
        gifts = await self._get_gifts(ctx)

        if not await conf.toggle():
            return await ctx.send("Marriage is not enabled!")

        if member.id == ctx.author.id:
            return await ctx.send("You cannot perform anything with yourself!")

        exertion = await conf.custom_gifts.get_raw(item, default=None)
        if not exertion:
            exertion = self._DEFAULT_GIFTS.get(item)

        if item not in gifts:
            return await ctx.send(f"Available gifts are: {humanize_list(gifts)}")

        endtext_format = await conf.gift_text()
        endtext = endtext_format.format(
            author=ctx.author.mention, item=item, target=member.mention
        )

        author_gift = await m_conf(ctx.author).gifts.get_raw(item, default=0)
        member_gift = await m_conf(member).gifts.get_raw(item, default=0)

        contentment, price = exertion.get("contentment"), exertion.get("price")

        if author_gift == 0:
            if await conf.currency() == 0:
                if not await bank.can_spend(ctx.author, price):
                    return await ctx.send("Uh oh, you cannot afford this.")
                await bank.withdraw_credits(ctx.author, price)
            else:
                if not await self._can_spend_cookies(ctx.author, price):
                    return await ctx.send("Uh oh, you cannot afford this.")
                await self._withdraw_cookies(ctx.author, price)
        author_gift -= 1
        member_gift += 1
        if author_gift >= 0:
            await m_conf(ctx.author).gifts.set_raw(item, value=author_gift)
        if member_gift > 0:
            await m_conf(member).gifts.set_raw(item, value=member_gift)

        t_temp = await m_conf(member).contentment()
        t_missing = 100 - t_temp
        if t_missing != 0:
            if contentment <= t_missing:
                await m_conf(member).contentment.set(t_temp + contentment)
            else:
                await m_conf(member).contentment.set(100)
        a_temp = await m_conf(ctx.author).contentment()
        a_missing = 100 - a_temp
        if a_missing != 0:
            if contentment <= a_missing:
                await m_conf(ctx.author).contentment.set(a_temp + contentment)
            else:
                await m_conf(ctx.author).contentment.set(100)

        spouses = await m_conf(ctx.author).current()
        if member.id not in spouses and await m_conf(ctx.author).married():
            for sid in spouses:
                spouse = (
                    self.bot.get_user(sid)
                    if await self.config.is_global()
                    else ctx.guild.get_member(sid)
                )
                endtext = await self._maybe_divorce(ctx, spouse, endtext, contentment)
        await ctx.send(endtext)

    async def _get_actions(self, ctx):
        conf = await self._get_conf_group(ctx.guild)

        actions = list(self._DEFAULT_ACTIONS.keys())
        removed_actions = await conf.removed_actions()
        custom_actions = await conf.custom_actions()
        if len(custom_actions) == 0:
            custom_actions = []
        else:
            custom_actions = list(custom_actions.keys())

        for removed in removed_actions:
            actions.remove(removed)

        actions.extend(custom_actions)

        return actions

    async def _get_gifts(self, ctx):
        conf = await self._get_conf_group(ctx.guild)

        gifts = list(self._DEFAULT_GIFTS.keys())
        removed_gifts = await conf.removed_gifts()
        custom_gifts = await conf.custom_gifts()
        custom_gifts = list() if len(custom_gifts) == 0 else list(custom_gifts.keys())
        for removed in removed_gifts:
            gifts.remove(removed)

        gifts.extend(custom_gifts)

        return gifts

    async def _get_all(self, ctx):
        all_items = list(await self._get_actions(ctx))
        all_items.extend(await self._get_gifts(ctx))
        return all_items

    async def _is_custom(self, ctx, item):
        conf = await self._get_conf_group(ctx.guild)
        actions = await conf.custom_actions()
        actions = list() if len(actions) == 0 else list(actions.keys())
        gifts = await conf.custom_gifts()
        gifts = list() if len(gifts) == 0 else list(gifts.keys())
        return item in actions or item in gifts

    async def _is_removed(self, ctx, item):
        conf = await self._get_conf_group(ctx.guild)
        actions = await conf.removed_actions()
        gifts = await conf.removed_gifts()

        return item in actions or item in gifts

    async def _get_cookies(self, user):
        return await self.bot.get_cog("Cookies").get_cookies(user)

    async def _can_spend_cookies(self, user, amount):
        return bool(await self.bot.get_cog("Cookies").can_spend(user, amount))

    async def _withdraw_cookies(self, user, amount):
        return await self.bot.get_cog("Cookies").withdraw_cookies(user, amount)

    async def _deposit_cookies(self, user, amount):
        return await self.bot.get_cog("Cookies").deposit_cookies(user, amount)

    async def _maybe_divorce(self, ctx, spouse, endtext, contentment):
        conf = await self._get_conf_group(ctx.guild)
        m_conf = await self._get_user_conf_group()
        s_temp = await m_conf(spouse).contentment()
        new_s_temp = 0 if s_temp < contentment else s_temp - contentment
        await m_conf(spouse).contentment.set(new_s_temp)
        if new_s_temp <= 0:
            async with m_conf(ctx.author).current() as acurrent:
                acurrent.remove(spouse.id)
            async with m_conf(spouse).current() as tcurrent:
                tcurrent.remove(ctx.author.id)
            async with m_conf(ctx.author).exes() as aexes:
                aexes.append(spouse.id)
            async with m_conf(spouse).exes() as texes:
                texes.append(ctx.author.id)
            if len(await m_conf(ctx.author).current()) == 0:
                await m_conf(ctx.author).married.set(False)
                await m_conf(ctx.author).divorced.set(True)
            if len(await m_conf(spouse).current()) == 0:
                await m_conf(spouse).married.set(False)
                await m_conf(spouse).divorced.set(True)
            if await conf.currency() == 0:
                abal = await bank.get_balance(ctx.author)
                await bank.withdraw_credits(ctx.author, abal)
                await bank.deposit_credits(spouse, abal)
            else:
                author_cookies = await self._get_cookies(ctx.author)
                await self._withdraw_cookies(ctx.author, author_cookies)
                await self._deposit_cookies(spouse, author_cookies)
            endtext = f"{endtext}\n:broken_heart: {ctx.author.mention} has made {spouse.mention} completely unhappy "
            f"with their actions so {spouse.mention} left them and took all their money!"
        return endtext

    async def _get_conf_group(self, guild):
        return (
            self.config if await self.config.is_global() else self.config.guild(guild)
        )

    async def _get_user_conf(self, user):
        return (
            self.config.user(user)
            if await self.config.is_global()
            else self.config.member(user)
        )

    async def _get_user_conf_group(self):
        return self.config.user if await self.config.is_global() else self.config.member
