from .complaint_cog import Complaint


async def setup(bot):
    await bot.add_cog(Complaint(bot))
