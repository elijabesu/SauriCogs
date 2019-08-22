from .customapi import CustomAPI


def setup(bot):
    bot.add_cog(CustomAPI(bot))