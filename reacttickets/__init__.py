from .reacttickets import ReactTickets


async def setup(bot):
    cog = ReactTickets(bot)
    await bot.add_cog(cog)
    await cog.initialize()
