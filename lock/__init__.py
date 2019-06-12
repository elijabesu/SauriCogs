from .lock import Lock


def setup(bot):
    bot.add_cog(Lock(bot))
