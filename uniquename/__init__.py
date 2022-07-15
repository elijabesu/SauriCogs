from .uniquename import UniqueName


async def setup(bot):
    await bot.add_cog(UniqueName(bot))
