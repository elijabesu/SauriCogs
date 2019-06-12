from .cookiestore import CookieStore


def setup(bot):
    bot.add_cog(CookieStore(bot))
