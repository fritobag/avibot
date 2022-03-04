import asyncio
import base64
import math
import random

from avibot import Cog, command


class Complaint(Cog):

    USER_AGENT_LIST = (
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:77.0) Gecko/20190101 Firefox/77.0",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Mozilla/5.0 (X11; Linux ppc64le; rv:75.0) Gecko/20100101 Firefox/75.0",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/75.0",
        "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.10; rv:75.0) Gecko/20100101 Firefox/75.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2919.83 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2866.71 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
    )
    URL = "http://anonymouse.org/cgi-bin/anon-email.cgi"
    MESSAGE_SENT = "```Your complaint was successfully scheduled. Status: {}```"

    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.email = bot.config.bot.complaint_email

    @command()
    async def complaint(self, ctx, *, msg):
        """Sends a complaint to Avilo"""
        if not self.email:
            self.logger.error("Error: Empty email.")
            return

        headers = {"User-Agent": random.choice(self.USER_AGENT_LIST)}
        n = 0xA ** (0xA - 0x1) + math.floor(random.random() * 0xA**0xA)
        v = base64.b64encode(hex(n)[2:].encode("utf-8")).decode("utf-8")

        payload = {
            "to": self.email,
            "subject": hex(random.getrandbits(42)).upper(),
            "text": msg,
            "n": n,
            "v": v,
        }
        msg_sent = await ctx.send(self.MESSAGE_SENT.format("Pending \u23F0"))

        async with self.lock:
            try:
                async with self.bot.session.post(
                    self.URL, data=payload, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    resp_text = await resp.text()
                    await asyncio.sleep(5)
                    if "The e-mail has been sent anonymously!" in resp_text:
                        await msg_sent.edit(
                            content=self.MESSAGE_SENT.format("Sent \u2705")
                        )
                    else:
                        await msg_sent.edit(
                            content=self.MESSAGE_SENT.format("Failed \u274C")
                        )
            except Exception:
                await msg_sent.edit(content=self.MESSAGE_SENT.format("Error \u2757"))
            finally:
                await ctx.message.delete(delay=5)
            await asyncio.sleep(60)
