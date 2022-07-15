from .pick import Pick


async def setup(bot):
    await bot.add_cog(Pick(bot))
