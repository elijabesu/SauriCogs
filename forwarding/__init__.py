from .forwarding import Forwarding


def setup(bot):
    n = Forwarding(bot)
    bot.add_cog(n)
