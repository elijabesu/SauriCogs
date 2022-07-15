from .suggestion import Suggestion


async def setup(bot):
    await bot.add_cog(Suggestion(bot))
