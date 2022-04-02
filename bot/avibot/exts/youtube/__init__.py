from .youtube_cog import Youtube


async def setup(bot):
    await bot.add_cog(Youtube(bot))
