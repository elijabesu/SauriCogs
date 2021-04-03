from asyncio import create_task

from .marriage import Marriage


async def setup_after_ready(bot):
    await bot.wait_until_red_ready()
    cog = Marriage(bot)
    for name, command in cog.all_commands.items():
        if not command.parent:
            if bot.get_command(name):
                command.name = f"m{command.name}"
            for alias in command.aliases:
                if bot.get_command(alias):
                    command.aliases[command.aliases.index(alias)] = f"m{alias}"
    bot.add_cog(cog)

def setup(bot):
    create_task(setup_after_ready(bot))
