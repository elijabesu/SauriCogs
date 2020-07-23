import asyncio
import discord

from typing import Union
from discord.utils import get
from datetime import datetime

from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify, humanize_list
from redbot.core.utils.predicates import MessagePredicate
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red


class CookieStore(commands.Cog):
    """
    Store add-on for SauriCogs' Cookies cog.
    """

    __author__ = "saurichable"
    __version__ = "1.0.5"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=16548964843212315, force_registration=True
        )
        self.config.register_guild(
            enabled=False, items={}, roles={}, games={}, ping=None
        )
        self.config.register_member(inventory={})

    @commands.group(autohelp=True)
    @checks.admin_or_permissions(manage_guild=True)
    @commands.guild_only()
    async def store(self, ctx):
        """Cookie store."""
        pass

    @store.command(name="toggle")
    async def store_toggle(self, ctx: commands.Context, on_off: bool = None):
        """Toggle store for current server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off
            if on_off
            else not (await self.config.guild(ctx.guild).enabled())
        )
        await self.config.guild(ctx.guild).enabled.set(target_state)
        if target_state:
            await ctx.send("Store is now enabled.")
        else:
            await ctx.send("Store is now disabled.")

    @store.command(name="add")
    async def store_add(self, ctx: commands.Context):
        """Add a buyable item/role/game key."""

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        types = ["item", "role", "game"]
        pred = MessagePredicate.lower_contained_in(types)
        pred_int = MessagePredicate.valid_int(ctx)
        pred_role = MessagePredicate.valid_role(ctx)
        pred_yn = MessagePredicate.yes_or_no(ctx)

        await ctx.send(
            "Do you want to add an item, role or game?\nItem and role = returnable, game = non returnable."
        )
        try:
            await self.bot.wait_for("message", timeout=30, check=pred)
        except asyncio.TimeoutError:
            return await ctx.send("You took too long. Try again, please.")
        if pred.result == 0:
            await ctx.send(
                "What is the name of the item? Note that you cannot include `@` in the name."
            )
            try:
                answer = await self.bot.wait_for("message", timeout=120, check=check)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            item_name = answer.content
            item_name = item_name.strip("@")
            try:
                is_already_item = await self.config.guild(ctx.guild).items.get_raw(
                    item_name
                )
                if is_already_item:
                    return await ctx.send(
                        "This item is already set. Please, remove it first."
                    )
            except KeyError:
                await ctx.send("How many cookies should this item be?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_int)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                price = pred_int.result
                if price <= 0:
                    return await ctx.send("Uh oh, price has to be more than 0.")
                await ctx.send("What quantity of this item should be available?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_int)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                quantity = pred_int.result
                if quantity <= 0:
                    return await ctx.send("Uh oh, quantity has to be more than 0.")
                await ctx.send("Is the item redeemable?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_yn)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                redeemable = pred_yn.result
                await self.config.guild(ctx.guild).items.set_raw(
                    item_name,
                    value={
                        "price": price,
                        "quantity": quantity,
                        "redeemable": redeemable,
                    },
                )
                await ctx.send(f"{item_name} added.")
        elif pred.result == 1:
            await ctx.send("What is the role?")
            try:
                await self.bot.wait_for("message", timeout=30, check=pred_role)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            role = pred_role.result
            try:
                is_already_role = await self.config.guild(ctx.guild).roles.get_raw(
                    role.name
                )
                if is_already_role:
                    return await ctx.send(
                        "This item is already set. Please, remove it first."
                    )
            except KeyError:
                await ctx.send("How many cookies should this role be?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_int)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                price = pred_int.result
                if price <= 0:
                    return await ctx.send("Uh oh, price has to be more than 0.")
                await ctx.send("What quantity of this item should be available?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_int)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                quantity = pred_int.result
                if quantity <= 0:
                    return await ctx.send("Uh oh, quantity has to be more than 0.")
                await self.config.guild(ctx.guild).roles.set_raw(
                    role.name, value={"price": price, "quantity": quantity}
                )
                await ctx.send(f"{role.name} added.")
        elif pred.result == 2:
            await ctx.send(
                "What is the name of the game? Note that you cannot include `@` in the name."
            )
            try:
                answer = await self.bot.wait_for("message", timeout=120, check=check)
            except asyncio.TimeoutError:
                return await ctx.send("You took too long. Try again, please.")
            game_name = answer.content
            game_name = game_name.strip("@")
            try:
                is_already_game = await self.config.guild(ctx.guild).games.get_raw(
                    game_name
                )
                if is_already_game:
                    return await ctx.send(
                        "This item is already set. Please, remove it first."
                    )
            except KeyError:
                await ctx.send("How many cookies should this game be?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_int)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                price = pred_int.result
                if price <= 0:
                    return await ctx.send("Uh oh, price has to be more than 0.")
                await ctx.send("What quantity of this item should be available?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_int)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                quantity = pred_int.result
                if quantity <= 0:
                    return await ctx.send("Uh oh, quantity has to be more than 0.")
                await ctx.send("Is the item redeemable?")
                try:
                    await self.bot.wait_for("message", timeout=120, check=pred_yn)
                except asyncio.TimeoutError:
                    return await ctx.send("You took too long. Try again, please.")
                redeemable = pred_yn.result
                await self.config.guild(ctx.guild).games.set_raw(
                    game_name,
                    value={
                        "price": price,
                        "quantity": quantity,
                        "redeemable": redeemable,
                    },
                )
                await ctx.send(f"{game_name} added.")
        else:
            await ctx.send("This answer is not supported. Try again, please.")

    @store.command(name="remove")
    async def store_remove(self, ctx: commands.Context, *, item: str):
        """Remove a buyable item/role/game key."""
        item = item.strip("@")
        try:
            is_already_item = await self.config.guild(ctx.guild).items.get_raw(item)
            if is_already_item:
                await self.config.guild(ctx.guild).items.clear_raw(item)
                return await ctx.send(f"{item} removed.")
        except KeyError:
            try:
                is_already_game = await self.config.guild(ctx.guild).games.get_raw(item)
                if is_already_game:
                    await self.config.guild(ctx.guild).games.clear_raw(item)
                    return await ctx.send(f"{item} removed.")
            except KeyError:
                try:
                    is_already_role = await self.config.guild(ctx.guild).roles.get_raw(
                        item
                    )
                    if is_already_role:
                        await self.config.guild(ctx.guild).roles.clear_raw(item)
                        await ctx.send(f"{item} removed.")
                except KeyError:
                    await ctx.send("That item isn't buyable.")

    @store.command(name="show")
    async def store_show(self, ctx: commands.Context, *, item: str):
        """Show information about a buyable item/role/game key."""
        item = item.strip("@")
        items = await self.config.guild(ctx.guild).items.get_raw()
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        games = await self.config.guild(ctx.guild).games.get_raw()

        if item in items:
            info = await self.config.guild(ctx.guild).items.get_raw(item)
            item_type = "item"
        elif item in roles:
            info = await self.config.guild(ctx.guild).roles.get_raw(item)
            item_type = "role"
        elif item in games:
            info = await self.config.guild(ctx.guild).games.get_raw(item)
            item_type = "game"
        else:
            return await ctx.send("This item isn't buyable.")
        price = info.get("price")
        quantity = info.get("quantity")
        redeemable = info.get("redeemable")
        if not redeemable:
            redeemable = False
        await ctx.send(
            f"**__{item}:__**\n*Type:* {item_type}\n*Price:* {price}\n*Quantity:* {quantity}\n*Redeemable:* {redeemable}"
        )

    @store.command(name="price")
    async def store_price(self, ctx: commands.Context, price: int, *, item: str):
        """Change the price of an existing buyable item."""
        if price <= 0:
            return await ctx.send("Uh oh, price has to be more than 0.")
        item = item.strip("@")
        items = await self.config.guild(ctx.guild).items.get_raw()
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        games = await self.config.guild(ctx.guild).games.get_raw()

        if item in items:
            await self.config.guild(ctx.guild).items.set_raw(item, "price", value=price)
            await ctx.send(f"{item}'s price changed to {price}.")
        elif item in roles:
            await self.config.guild(ctx.guild).roles.set_raw(item, "price", value=price)
            await ctx.send(f"{item}'s price changed to {price}.")
        elif item in games:
            await self.config.guild(ctx.guild).games.set_raw(item, "price", value=price)
            await ctx.send(f"{item}'s price changed to {price}.")
        else:
            await ctx.send("This item isn't in the store. Please, add it first.")

    @store.command(name="quantity")
    async def store_quantity(self, ctx: commands.Context, quantity: int, *, item: str):
        """Change the quantity of an existing buyable item."""
        if quantity <= 0:
            return await ctx.send("Uh oh, quantity has to be more than 0.")
        item = item.strip("@")
        items = await self.config.guild(ctx.guild).items.get_raw()
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        games = await self.config.guild(ctx.guild).games.get_raw()

        if item in items:
            await self.config.guild(ctx.guild).items.set_raw(
                item, "quantity", value=quantity
            )
            await ctx.send(f"{item}'s quantity changed to {quantity}.")
        elif item in roles:
            await self.config.guild(ctx.guild).roles.set_raw(
                item, "quantity", value=quantity
            )
            await ctx.send(f"{item}'s quantity changed to {quantity}.")
        elif item in games:
            await self.config.guild(ctx.guild).games.set_raw(
                item, "quantity", value=quantity
            )
            await ctx.send(f"{item}'s quantity changed to {quantity}.")
        else:
            await ctx.send("This item isn't in the store. Please, add it first.")

    @store.command(name="redeemable")
    async def store_redeemable(
        self, ctx: commands.Context, redeemable: bool, *, item: str
    ):
        """Change the redeemable of an existing buyable item."""
        items = await self.config.guild(ctx.guild).items.get_raw()
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        games = await self.config.guild(ctx.guild).games.get_raw()

        item = item.strip("@")
        if item in items:
            await self.config.guild(ctx.guild).items.set_raw(
                item, "redeemable", value=redeemable
            )
            await ctx.send(f"{item}'s redeemability changed to {redeemable}.")
        elif item in roles:
            await self.config.guild(ctx.guild).roles.set_raw(
                item, "redeemable", value=redeemable
            )
            await ctx.send(f"{item}'s redeemability changed to {redeemable}.")
        elif item in games:
            await self.config.guild(ctx.guild).games.set_raw(
                item, "redeemable", value=redeemable
            )
            await ctx.send(f"{item}'s redeemability changed to {redeemable}.")
        else:
            await ctx.send("This item isn't in the store. Please, add it first.")

    @store.command(name="reset")
    async def store_reset(self, ctx: commands.Context, confirmation: bool = False):
        """Delete all items from the store."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** items. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}store reset yes`."
            )
        for i in await self.config.guild(ctx.guild).items.get_raw():
            await self.config.guild(ctx.guild).items.clear_raw(i)
        for r in await self.config.guild(ctx.guild).roles.get_raw():
            await self.config.guild(ctx.guild).roles.clear_raw(r)
        for g in await self.config.guild(ctx.guild).games.get_raw():
            await self.config.guild(ctx.guild).games.clear_raw(i)
        await ctx.send("All items have been deleted from the store.")

    @store.command(name="ping")
    async def store_ping(
        self, ctx: commands.Context, who: Union[discord.Member, discord.Role] = None
    ):
        """Set the role/member that should be pinged when a member wants to redeem their item.

        If who isn't provided, it will show the current ping set."""
        if not who:
            ping_id = await self.config.guild(ctx.guild).ping()
            if not ping_id:
                return await ctx.send("No ping is set.")
            ping = get(ctx.guild.members, id=ping_id)
            if not ping:
                ping = get(ctx.guild.roles, id=ping_id)
                if not ping:
                    return await ctx.send(
                        "The role must have been deleted or user must have left."
                    )
            return await ctx.send(f"{ping.name} is set to be pinged.")
        await self.config.guild(ctx.guild).ping.set(who.id)
        await ctx.send(
            f"{who.name} has been set to be pinged when a member wants to redeem their item."
        )

    @store.command(name="resetinventories")
    async def store_resetinventories(
        self, ctx: commands.Context, confirmation: bool = False
    ):
        """Delete all items from all members' inventories."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** items from all members' inventories. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}store resetinventories yes`."
            )
        for member in ctx.guild.members:
            inventory = await self.config.member(member).inventory.get_raw()
            for item in inventory:
                await self.config.member(member).inventory.clear_raw(item)
        await ctx.send("All items have been deleted from all members' inventories.")

    @commands.command()
    @commands.guild_only()
    async def shop(self, ctx: commands.Context):
        """Display the cookie store."""
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            return await ctx.send("Uh oh, store is disabled.")
        page_list = await self._show_store(ctx)
        if len(page_list) > 1:
            await menu(ctx, page_list, DEFAULT_CONTROLS)
        else:
            await ctx.send(embed=page_list[0])

    @commands.command()
    @commands.guild_only()
    async def buy(self, ctx: commands.Context, *, item: str = ""):
        """Buy an item from the cookie store."""
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            return await ctx.send("Uh oh, store is disabled.")
        cookies = int(
            await self.bot.get_cog("Cookies").config.member(ctx.author).cookies()
        )
        items = await self.config.guild(ctx.guild).items.get_raw()
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        games = await self.config.guild(ctx.guild).games.get_raw()

        if not item:
            page_list = await self._show_store(ctx)
            if len(page_list) > 1:
                return await menu(ctx, page_list, DEFAULT_CONTROLS)
            return await ctx.send(embed=page_list[0])
        item = item.strip("@")
        inventory = await self.config.member(ctx.author).inventory.get_raw()
        if item in inventory:
            return await ctx.send("You already own this item.")
        if item in roles:
            role_obj = get(ctx.guild.roles, name=item)
            if role_obj:
                role = await self.config.guild(ctx.guild).roles.get_raw(item)
                price = int(role.get("price"))
                quantity = int(role.get("quantity"))
                if quantity == 0:
                    return await ctx.send("Uh oh, this item is out of stock.")
                if price <= cookies:
                    pass
                else:
                    return await ctx.send("You don't have enough cookies!")
                await ctx.author.add_roles(role_obj)
                cookies -= price
                quantity -= 1
                await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(
                    cookies
                )
                await self.config.member(ctx.author).inventory.set_raw(
                    item,
                    value={
                        "price": price,
                        "is_role": True,
                        "is_game": False,
                        "redeemable": False,
                        "redeemed": True,
                    },
                )
                await self.config.guild(ctx.guild).roles.set_raw(
                    item, "quantity", value=quantity
                )
                await ctx.send(f"You have bought {item}.")
            else:
                await ctx.send("Uh oh, can't find the role.")
        elif item in items:
            item_info = await self.config.guild(ctx.guild).items.get_raw(item)
            price = int(item_info.get("price"))
            quantity = int(item_info.get("quantity"))
            redeemable = item_info.get("redeemable")
            if not redeemable:
                redeemable = False
            if quantity == 0:
                return await ctx.send("Uh oh, this item is out of stock.")
            if price <= cookies:
                pass
            else:
                return await ctx.send("You don't have enough cookies!")
            cookies -= price
            quantity -= 1
            await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(
                cookies
            )
            await self.config.guild(ctx.guild).items.set_raw(
                item, "quantity", value=quantity
            )
            if not redeemable:
                await self.config.member(ctx.author).inventory.set_raw(
                    item,
                    value={
                        "price": price,
                        "is_role": False,
                        "is_game": False,
                        "redeemable": False,
                        "redeemed": True,
                    },
                )
                await ctx.send(f"You have bought {item}.")
            else:
                await self.config.member(ctx.author).inventory.set_raw(
                    item,
                    value={
                        "price": price,
                        "is_role": False,
                        "is_game": False,
                        "redeemable": True,
                        "redeemed": False,
                    },
                )
                await ctx.send(
                    f"You have bought {item}. You may now redeem it with `{ctx.clean_prefix}redeem {item}`"
                )
        elif item in games:
            game_info = await self.config.guild(ctx.guild).games.get_raw(item)
            price = int(game_info.get("price"))
            quantity = int(game_info.get("quantity"))
            redeemable = game_info.get("redeemable")
            if not redeemable:
                redeemable = False
            if quantity == 0:
                return await ctx.send("Uh oh, this item is out of stock.")
            if price <= cookies:
                pass
            else:
                return await ctx.send("You don't have enough cookies!")
            cookies -= price
            quantity -= 1
            await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(
                cookies
            )
            await self.config.guild(ctx.guild).games.set_raw(
                item, "quantity", value=quantity
            )
            if not redeemable:
                await self.config.member(ctx.author).inventory.set_raw(
                    item,
                    value={
                        "price": price,
                        "is_role": False,
                        "is_game": True,
                        "redeemable": False,
                        "redeemed": True,
                    },
                )
                await ctx.send(f"You have bought {item}.")
            else:
                await self.config.member(ctx.author).inventory.set_raw(
                    item,
                    value={
                        "price": price,
                        "is_role": False,
                        "is_game": True,
                        "redeemable": True,
                        "redeemed": False,
                    },
                )
                await ctx.send(
                    f"You have bought {item}. You may now redeem it with `{ctx.clean_prefix}redeem {item}`"
                )
        else:
            page_list = await self._show_store(ctx)
            if len(page_list) > 1:
                return await menu(ctx, page_list, DEFAULT_CONTROLS)
            return await ctx.send(embed=page_list[0])

    @commands.command(name="return")
    @commands.guild_only()
    async def store_return(self, ctx: commands.Context, *, item: str):
        """Return an item, you will only get 50% of the price."""
        enabled = await self.config.guild(ctx.guild).enabled()
        if not enabled:
            return await ctx.send("Uh oh, store is disabled.")
        cookies = int(
            await self.bot.get_cog("Cookies").config.member(ctx.author).cookies()
        )
        inventory = await self.config.member(ctx.author).inventory.get_raw()

        if item in inventory:
            pass
        else:
            return await ctx.send("You don't own this item.")
        info = await self.config.member(ctx.author).inventory.get_raw(item)

        is_game = info.get("is_game")
        if is_game:
            return await ctx.send("This item isn't returnable.")
        is_role = info.get("is_role")
        if is_role:
            role_obj = get(ctx.guild.roles, name=item)
            if role_obj:
                await ctx.author.remove_roles(role_obj)
        redeemed = info.get("redeemed")
        if not redeemed:
            redeemed = False
        if redeemed:
            return await ctx.send("You can't return an item you have redeemed.")
        price = int(info.get("price"))
        return_price = price * 0.5
        cookies += return_price
        await self.config.member(ctx.author).inventory.clear_raw(item)
        await self.bot.get_cog("Cookies").config.member(ctx.author).cookies.set(cookies)
        await ctx.send(
            f"You have returned {item} and got {return_price} :cookie: back."
        )

    @commands.command()
    @commands.guild_only()
    async def inventory(self, ctx: commands.Context):
        """See all items you own."""
        inventory = await self.config.member(ctx.author).inventory.get_raw()

        lst = []
        for i in inventory:
            info = await self.config.member(ctx.author).inventory.get_raw(i)
            if not info.get("is_role"):
                lst.append(i)
            else:
                role_obj = get(ctx.guild.roles, name=i)
                lst.append(role_obj.mention)
        if lst == []:
            desc = "Nothing to see here."
        else:
            desc = humanize_list(lst)
        embed = discord.Embed(
            description=desc, colour=ctx.author.colour, timestamp=datetime.now()
        )
        embed.set_author(
            name=f"{ctx.author.display_name}'s inventory",
            icon_url=ctx.author.avatar_url,
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def removeinventory(self, ctx: commands.Context, *, item: str):
        """Remove an item from your inventory."""
        inventory = await self.config.member(ctx.author).inventory.get_raw()
        if item not in inventory:
            return await ctx.send("You don't own this item.")
        await self.config.member(ctx.author).inventory.clear_raw(item)
        await ctx.send(f"{item} removed.")

    @commands.command()
    @commands.guild_only()
    async def redeem(self, ctx: commands.Context, *, item: str):
        """Redeem an item from your inventory."""
        inventory = await self.config.member(ctx.author).inventory.get_raw()
        if item not in inventory:
            return await ctx.send("You don't own this item.")
        info = await self.config.member(ctx.author).inventory.get_raw(item)
        is_role = info.get("is_role")
        if is_role:
            return await ctx.send("Roles aren't redeemable.")
        redeemable = info.get("redeemable")
        if not redeemable:
            return await ctx.send("This item isn't redeemable.")
        redeemed = info.get("redeemed")
        if redeemed:
            return await ctx.send("You have already redeemed this item.")
        ping_id = await self.config.guild(ctx.guild).ping()
        if not ping_id:
            return await ctx.send("Uh oh, your Admins haven't set this yet.")
        ping = get(ctx.guild.members, id=ping_id)
        if not ping:
            ping = get(ctx.guild.roles, id=ping_id)
            if not ping:
                return await ctx.send("Uh oh, your Admins haven't set this yet.")
            if not ping.mentionable:
                await ping.edit(mentionable=True)
                await ctx.send(
                    f"{ping.mention}, {ctx.author.mention} would like to redeem {item}."
                )
                await ping.edit(mentionable=False)
            else:
                await ctx.send(
                    f"{ping.mention}, {ctx.author.mention} would like to redeem {item}."
                )
            await self.config.member(ctx.author).inventory.set_raw(
                item, "redeemed", value=True
            )
        else:
            await ctx.send(
                f"{ping.mention}, {ctx.author.mention} would like to redeem {item}."
            )
            await self.config.member(ctx.author).inventory.set_raw(
                item, "redeemed", value=True
            )

    async def _show_store(self, ctx):
        items = await self.config.guild(ctx.guild).items.get_raw()
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        games = await self.config.guild(ctx.guild).games.get_raw()
        stuff = []
        for i in items:
            item = await self.config.guild(ctx.guild).items.get_raw(i)
            price = int(item.get("price"))
            quantity = int(item.get("quantity"))
            item_text = f"__Item:__ **{i}** | __Price:__ {price} :cookie: | __Quantity:__ {quantity}"
            stuff.append(item_text)
        for g in games:
            game = await self.config.guild(ctx.guild).games.get_raw(g)
            price = int(game.get("price"))
            quantity = int(game.get("quantity"))
            game_text = f"__Item:__ **{g}** | __Price:__ {price} :cookie: | __Quantity:__ {quantity}"
            stuff.append(game_text)
        for r in roles:
            role_obj = get(ctx.guild.roles, name=r)
            if not role_obj:
                continue
            role = await self.config.guild(ctx.guild).roles.get_raw(r)
            price = int(role.get("price"))
            quantity = int(role.get("quantity"))
            role_text = f"__Role:__ **{role_obj.mention}** | __Price:__ {price} :cookie: | __Quantity:__ {quantity}"
            stuff.append(role_text)
        if stuff == []:
            desc = "Nothing to see here."
        else:
            desc = "\n".join(stuff)
        page_list = []
        for page in pagify(desc, delims=["\n"], page_length=1000):
            embed = discord.Embed(
                colour=await ctx.embed_colour(),
                description=page,
                timestamp=datetime.now(),
            )
            embed.set_author(
                name=f"{ctx.guild.name}'s cookie store", icon_url=ctx.guild.icon_url,
            )
            page_list.append(embed)
        return page_list
