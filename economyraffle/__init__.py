from .economyraffle import EconomyRaffle


def setup(bot):
    bot.add_cog(EconomyRaffle(bot))
