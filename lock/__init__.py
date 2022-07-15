from .lock import Lock


async def setup(bot):
    await bot.add_cog(Lock(bot))
