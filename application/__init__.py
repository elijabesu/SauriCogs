from .application import Application


async def setup(bot):
    await bot.add_cog(Application(bot))
