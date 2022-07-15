from .gallery import Gallery


async def setup(bot):
    await bot.add_cog(Gallery(bot))
