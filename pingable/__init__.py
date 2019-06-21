from .pingable import Pingable


def setup(bot):
    bot.add_cog(Pingable(bot))
