from .pingable import Pingable


async def setup(bot):
    await bot.add_cog(Pingable(bot))
