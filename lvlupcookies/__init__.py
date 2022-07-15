from .lvlupcookies import LevelUpCookies


async def setup(bot):
    await bot.add_cog(LevelUpCookies(bot))
