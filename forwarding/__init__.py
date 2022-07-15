from .forwarding import Forwarding


async def setup(bot):
    n = Forwarding(bot)
    await bot.add_cog(n)
