import asyncio
import re
import json
import random
from aiocache import cached
import aiohttp

import discord
from discord.ext import commands
from utils import cfg


class FixSocials(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # regex for tiktok urls
        self.tiktok_pattern = re.compile(r"https:\/\/(www.)?((vm|vt).tiktok.com\/[A-Za-z0-9]+|tiktok.com\/@[\w.]+\/video\/[\d]+\/?|tiktok.com\/t\/[a-zA-Z0-9]+\/)")

        # regex for instagram urls
        self.instagram_pattern = re.compile(r"(https:\/\/(www.)?instagram\.com\/(?:p|reel)\/([^/?#&]+))\/")

        # regex for reddit urls
        self.reddit_pattern = re.compile(r"(https?://(?:www\.)?(?:old\.)?reddit\.com/r/[A-Za-z0-9_]+/(?:comments|s)/[A-Za-z0-9_]+(?:/[^/ ]+)?(?:/\w+)?)|(https?://(?:www\.)?redd\.it/[A-Za-z0-9]+)")

        # regex for twitter urls
        self.twitter_pattern = re.compile(r"(https:\/\/(www.)?(twitter|x)\.com\/[a-zA-Z0-9_]+\/status\/[0-9]+)")


    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if cfg.aaron_id is None or cfg.roles.aaron_role is None:
            return
        if not message.guild:
            return
        if message.guild.id != cfg.guild_id:
            return
        if message.author.bot:
            return
        if message.channel.id != cfg.channels.general:
            return

        message_content = message.content.strip("<>")
        if tiktok_match := self.tiktok_pattern.search(message_content):
            link = tiktok_match.group(0)
            await self.fix_tiktok(message, link) 
        elif instagram_match := self.instagram_pattern.search(message_content):
            link = instagram_match.group(0)
            await self.fix_instagram(message, link)
        elif reddit_match := self.reddit_pattern.search(message_content):
            link = reddit_match.group(0)
            await self.fix_reddit(message, link)
        elif twitter_match := self.twitter_pattern.search(message_content):
            link = twitter_match.group(0)
            await self.fix_twitter(message, link)

    @cached(ttl=3600)
    async def quickvids(self, tiktok_url):
        try:
            headers = {
                'content-type': 'application/json',
                'user-agent': 'GIR - slim.rocks/gir',
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                url = 'https://api.quickvids.win/v1/shorturl/create'
                data = {'input_text': tiktok_url}
                async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        text = await response.text()
                        data = json.loads(text)
                        quickvids_url = data['quickvids_url']
                        return quickvids_url
                    else:
                        return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    @cached(ttl=3600)
    async def is_carousel_tiktok(self, link: str):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(link, timeout=5) as response:
                    if response.status == 200:
                        text = await response.text()
                        return '>Download All Images</button>' in text
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    @cached(ttl=3600)
    async def get_tiktok_redirect(self, link: str):
        quickvids_url = await self.quickvids(link)
        if quickvids_url and not await self.is_carousel_tiktok(quickvids_url):
            return quickvids_url

        else:
            async with aiohttp.ClientSession() as session:
                async with session.get(link, allow_redirects=False) as response:
                    if response.status != 301:
                        return

                    redirected_url = str(response).split("Location': \'")[1].split("\'")[0]

            redirected_url = redirected_url.replace('www.tiktok.com', 'tnktok.com')
            if (tracking_id_index := redirected_url.index('?')) is not None:
                # remove everything after the question mark (tracking ID)
                redirected_url = redirected_url[:tracking_id_index]

            return redirected_url

    async def fix_tiktok(self, message: discord.Message, link: str):
        redirected_url = await self.get_tiktok_redirect(link)
        if redirected_url is None:
            return

        await message.reply(f"[I hate tiktok but here you go]({redirected_url})", mention_author=False)
        await asyncio.sleep(0.5)
        await message.edit(suppress=True)

    async def fix_instagram(self, message: discord.Message, link: str):
        link = link.replace("www.", "")
        link = link.replace("instagram.com", "ig.itsnebula.net")

        await message.reply(f"[I hate instagram but here you go]({link})", mention_author=False)
        await asyncio.sleep(0.5)
        await message.edit(suppress=True)

    async def fix_reddit(self, message: discord.Message, link: str):
        link = link.replace("www.", "")
        link = link.replace("old.reddit.com", "reddit.com")
        link = link.replace("reddit.com", "rxddit.com")

        await message.reply(f"[I hate reddit but here you go]({link})", mention_author=False)
        await asyncio.sleep(0.5)
        await message.edit(suppress=True)

    async def fix_twitter(self, message: discord.Message, link: str):
        link = link.replace("www.", "")
        link = link.replace('x.com', 'twitter.com')
        link = link.replace("twitter.com", "fxtwitter.com")

        # twitter embeds work for images again, only fix links with a video
        await asyncio.sleep(2)
        if message.embeds:
            embed = message.embeds[0]
            image = embed.to_dict().get('image')
            if image and 'video_thumb' in image.get('url'):
                await message.reply(f"[I hate {random.choice(['twitter', '𝕏', 'Elon Musk'])} but here you go]({link})", mention_author=False)
                await asyncio.sleep(0.5)
                await message.edit(suppress=True)
        else:
            await message.reply(f"[I hate {random.choice(['twitter', '𝕏', 'Elon Musk'])} but here you go]({link})", mention_author=False)
            await asyncio.sleep(0.5)
            await message.edit(suppress=True)



async def setup(bot):
    await bot.add_cog(FixSocials(bot))
