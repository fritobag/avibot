from .complaint_cog import Complaint


def setup(bot):
    bot.add_cog(Complaint(bot))
