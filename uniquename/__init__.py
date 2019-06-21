from .uniquename import UniqueName


def setup(bot):
    bot.add_cog(UniqueName(bot))
