from .advancedlock import AdvancedLock


def setup(bot):
    bot.add_cog(AdvancedLock(bot))
