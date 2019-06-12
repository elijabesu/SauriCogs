from .mentionable import Mentionable


def setup(bot):
    bot.add_cog(Mentionable(bot))
