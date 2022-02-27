from .youtube_cog import Youtube


def setup(bot):
    bot.add_cog(Youtube(bot))
