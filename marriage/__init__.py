from .marriage import Marriage


def setup(bot):
    bot.add_cog(Marriage(bot))
