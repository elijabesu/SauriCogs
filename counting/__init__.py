from .counting import Counting


def setup(bot):
    bot.add_cog(Counting(bot))
