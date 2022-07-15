from .mentionable import Mentionable


async def setup(bot):
    await bot.add_cog(Mentionable(bot))
