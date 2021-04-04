from asyncio import create_task

from .cookiestore import CookieStore


async def setup_after_ready(bot):
    await bot.wait_until_red_ready()
    cog = CookieStore(bot)
    for name, command in cog.all_commands.items():
        if not command.parent:
            if bot.get_command(name):
                command.name = f"c{command.name}"
            for alias in command.aliases:
                if bot.get_command(alias):
                    command.aliases[command.aliases.index(alias)] = f"c{alias}"
    bot.add_cog(cog)


def setup(bot):
    create_task(setup_after_ready(bot))
