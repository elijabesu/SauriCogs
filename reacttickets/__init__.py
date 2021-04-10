from .reacttickets import ReactTickets


async def setup(bot):
    cog = ReactTickets(bot)
    bot.add_cog(cog)
    await cog.initialize()
