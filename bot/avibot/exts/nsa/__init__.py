from .nsa_cog import Nsa


async def setup(bot):
    await bot.add_cog(Nsa(bot))
