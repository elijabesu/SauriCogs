from .economyraffle import EconomyRaffle


async def setup(bot):
    await bot.add_cog(EconomyRaffle(bot))
