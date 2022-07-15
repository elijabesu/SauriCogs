from .advancedlock import AdvancedLock


async def setup(bot):
    await bot.add_cog(AdvancedLock(bot))
