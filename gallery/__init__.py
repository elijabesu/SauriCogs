from .gallery import Gallery


def setup(bot):
    bot.add_cog(Gallery(bot))
