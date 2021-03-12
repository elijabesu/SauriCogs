import discord
import datetime
import typing

from discord.utils import get

from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import pagify, humanize_list
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS

from redbot.core.bot import Red


class CookieStore(commands.Cog):
    """
    Store add-on for SauriCogs' Cookies cog.
    """

    __author__ = "saurichable"
    __version__ = "1.1.0"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=16548964843212315, force_registration=True
        )
        self.config.register_guild(
            enabled=False, items={}, roles={}, games={}, ping=None
        )
        self.config.register_member(inventory={})

    @commands.group(autohelp=True, aliases=["cookiestore", "storeset"])
    @checks.admin()
    @commands.guild_only()
    async def cookiestoreset(self, ctx):
        """Various Cookie Store settings."""

    @cookiestoreset.command(name="toggle")
    async def cookiestoreset_toggle(self, ctx: commands.Context, on_off: bool = None):
        """Toggle store for current server.

        If `on_off` is not provided, the state will be flipped."""
        target_state = (
            on_off if on_off else not (await self.config.guild(ctx.guild).enabled())
        )
        await self.config.guild(ctx.guild).enabled.set(target_state)
        if target_state:
            await ctx.send("Store is now enabled.")
        else:
            await ctx.send("Store is now disabled.")

    @cookiestoreset.group(name="add")
    async def cookiestoreset_add(self, ctx: commands.Context):
        """Add purchasable stuff."""

    @cookiestoreset_add.command(name="role")
    async def cookiestoreset_add_role(self, ctx: commands.Context, role: discord.Role, price: int, quantity: int):
        """Add a purchasable (returnable) role."""
        if price <= 0 or quantity <= 0:
            return await ctx.send("Uh oh, price/quantity have to be over 0.")
        if await self.config.guild(ctx.guild).roles.get_raw(role):
            return await ctx.send(f"Uh oh, {role.name} is already registered.")
        await self.config.guild(ctx.guild).roles.set_raw(
            role.name, value={"price": price, "quantity": quantity}
        )
        await ctx.tick()

    @cookiestoreset_add.command(name="item")
    async def cookiestoreset_add_item(self, ctx: commands.Context, item: str, price: int, quantity: int, redeem: bool):
        """Add a purchasable (returnable) item."""
        if price <= 0 or quantity <= 0:
            return await ctx.send("Uh oh, price/quantity have to be over 0.")
        if await self.config.guild(ctx.guild).items.get_raw(item):
            return await ctx.send(f"Uh oh, {item} is already registered.")
        await self.config.guild(ctx.guild).items.set_raw(
            item,
            value={
                "price": price,
                "quantity": quantity,
                "redeemable": redeem,
            },
        )
        await ctx.tick()

    @cookiestoreset_add.command(name="game")
    async def cookiestoreset_add_game(self, ctx: commands.Context, game: str, price: int, quantity: int, redeem: bool):
        """Add a purchasable (non-returnable) game."""
        if price <= 0 or quantity <= 0:
            return await ctx.send("Uh oh, price/quantity have to be over 0.")
        if await self.config.guild(ctx.guild).games.get_raw(game):
            return await ctx.send(f"Uh oh, {game} is already registered.")
        await self.config.guild(ctx.guild).games.set_raw(
            game,
            value={
                "price": price,
                "quantity": quantity,
                "redeemable": redeem,
            },
        )
        await ctx.tick()

    @cookiestoreset.group(name="remove")
    async def cookiestoreset_remove(self, ctx: commands.Context):
        """Remove purchasable stuff."""

    @cookiestoreset_remove.command(name="role")
    async def cookiestoreset_remove_role(self, ctx: commands.Context, role: discord.Role):
        """Remove a purchasable role."""
        if not await self.config.guild(ctx.guild).roles.get_raw(role):
            return await ctx.send(f"Uh oh, {role.name} is not registered.")
        await self.config.guild(ctx.guild).roles.clear_raw(role)
        await ctx.tick()

    @cookiestoreset_remove.command(name="item")
    async def cookiestoreset_remove_item(self, ctx: commands.Context, item: str):
        """Remove a purchasable item."""
        if not await self.config.guild(ctx.guild).items.get_raw(item):
            return await ctx.send(f"Uh oh, {item} is not registered.")
        await self.config.guild(ctx.guild).items.clear_raw(item)
        await ctx.tick()

    @cookiestoreset_remove.command(name="game")
    async def cookiestoreset_remove_game(self, ctx: commands.Context, game: str):
        """Remove a purchasable game."""
        if not await self.config.guild(ctx.guild).games.get_raw(game):
            return await ctx.send(f"Uh oh, {game} is not registered.")
        await self.config.guild(ctx.guild).games.clear_raw(game)
        await ctx.tick()

    @cookiestoreset.command(name="show")
    async def cookiestoreset_show(self, ctx: commands.Context, *, item: str):
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

    @cookiestoreset.command(name="restock")
    async def cookiestoreset_restock(self, ctx: commands.Context, item: str, quantity: int):
        """Change the quantity of an existing purchasable item."""
        if quantity <= 0:
            return await ctx.send("Uh oh, quantity has to be more than 0.")
        items = await self.config.guild(ctx.guild).items.get_raw()
        roles = await self.config.guild(ctx.guild).roles.get_raw()
        games = await self.config.guild(ctx.guild).games.get_raw()

        if item in items:
            await self.config.guild(ctx.guild).items.set_raw(
                item, "quantity", value=quantity
            )
            await ctx.tick()
        elif item in roles:
            await self.config.guild(ctx.guild).roles.set_raw(
                item, "quantity", value=quantity
            )
            await ctx.tick()
        elif item in games:
            await self.config.guild(ctx.guild).games.set_raw(
                item, "quantity", value=quantity
            )
            await ctx.tick()
        else:
            await ctx.send("This item isn't in the store. Please, add it first.")

    @cookiestoreset.command(name="ping")
    async def cookiestoreset_ping(
        self, ctx: commands.Context, who: typing.Union[discord.Member, discord.Role] = None
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

    @cookiestoreset.group(name="reset", invoke_without_command=True)
    async def cookiestoreset_reset(self, ctx: commands.Context, confirmation: typing.Optional[bool]):
        """Delete all items from the store."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** items. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}cookiestoreset reset yes`."
            )
        for i in await self.config.guild(ctx.guild).items.get_raw():
            await self.config.guild(ctx.guild).items.clear_raw(i)
        for r in await self.config.guild(ctx.guild).roles.get_raw():
            await self.config.guild(ctx.guild).roles.clear_raw(r)
        for g in await self.config.guild(ctx.guild).games.get_raw():
            await self.config.guild(ctx.guild).games.clear_raw(g)
        await ctx.send("All items have been deleted from the store.")

    @cookiestoreset_reset.command(name="nventories")
    async def cookiestoreset_reset_inventories(
        self, ctx: commands.Context, confirmation: typing.Optional[bool]
    ):
        """Delete all items from all members' inventories."""
        if not confirmation:
            return await ctx.send(
                "This will delete **all** items from all members' inventories. This action **cannot** be undone.\n"
                f"If you're sure, type `{ctx.clean_prefix}cookiestoreset reset inventories yes`."
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
    async def buy(self, ctx: commands.Context, *, item: typing.Optional[str]):
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
    async def cookiestoreset_return(self, ctx: commands.Context, *, item: str):
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

    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    async def inventory(self, ctx: commands.Context):
        """See all items you own."""
        inventory = await self.config.member(ctx.author).inventory.get_raw()

        lst = list()
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
            description=desc, colour=ctx.author.colour, timestamp=datetime.datetime.now()
        )
        embed.set_author(
            name=f"{ctx.author.display_name}'s inventory",
            icon_url=ctx.author.avatar_url,
        )

        await ctx.send(embed=embed)

    @inventory.command(name="remove")
    @commands.guild_only()
    async def inventory_remove(self, ctx: commands.Context, *, item: str):
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
        stuff = list()
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
        page_list = list()
        for page in pagify(desc, delims=["\n"], page_length=1000):
            embed = discord.Embed(
                colour=await ctx.embed_colour(),
                description=page,
                timestamp=datetime.datetime.now(),
            )
            embed.set_author(
                name=f"{ctx.guild.name}'s cookie store",
                icon_url=ctx.guild.icon_url,
            )
            page_list.append(embed)
        return page_list
