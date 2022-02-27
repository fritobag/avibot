import re
from avibot import Cog, command


class Youtube(Cog):
    def __init__(self, bot):
        self.bot = bot

    @command()
    async def stream(self, ctx):
        """Checks if avilo is streaming."""
        headers = {
            "accept-language": "en-US,en;q=0.5",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
        }
        url = "https://www.youtube.com/avilosoamaze/live"
        async with ctx.session.get(url, headers=headers) as response:
            response_text = await response.text()

        try:
            result = re.search(
                r"\"dateText\"\:\{\"simpleText\":\"([\w\s,.]+)\"\}", response_text
            )
            info = result.group(1)
            info = info[0].lower() + info[1:]
        except Exception:
            info = "is too busy spamming his girlfriend"

        webhook = await ctx.webhook

        await webhook.send(
            (
                f"Avilo {info}!\nLinks: [youtube](<https://www.youtube.com/avilosoamaze/live>)"
                " and [mixer](<https://mixer.com/avilo>)"
            ),
            username=self.bot.name,
            avatar_url=self.bot.avatar,
        )
