from .suggestion import Suggestion


def setup(bot):
    bot.add_cog(Suggestion(bot))
