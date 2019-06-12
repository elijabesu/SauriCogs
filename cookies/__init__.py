from .cookies import Cookies


def setup(bot):
    bot.add_cog(Cookies(bot))
