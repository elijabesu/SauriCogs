from .userlog import UserLog


async def setup(bot):
    await bot.add_cog(UserLog(bot))
