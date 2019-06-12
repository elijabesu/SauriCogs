from .application import Application


def setup(bot):
    bot.add_cog(Application(bot))
