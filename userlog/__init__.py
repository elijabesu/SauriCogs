from .userlog import UserLog


def setup(bot):
    bot.add_cog(UserLog(bot))
