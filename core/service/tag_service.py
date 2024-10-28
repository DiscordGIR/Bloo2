import re
from typing import Optional, List

import discord
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.tag import TagResult
from core.model import TagButton, Tag
from core.repository import TagRepository
from utils import format_number


class TagService:
    def __init__(self, session: AsyncSession):
        self.tag_repository = TagRepository(session)

    @staticmethod
    def prepare_tag_embed(tag: Tag):
        embed = discord.Embed(title=tag.phrase)
        embed.description = tag.content
        embed.timestamp = tag.updated_at
        embed.color = discord.Color.blue()

        if tag.image:
            embed.set_image(url=tag.image)

        embed.set_footer(
            text=f"Added by {tag.creator_tag} | Used {format_number(tag.uses)} times")

        return embed

    async def get_tag(self, name: str) -> Optional[TagResult]:
        return await self.tag_repository.get_tag(name)

    @staticmethod
    def prepare_tag_button_view(buttons: List[TagButton]):
        if not buttons:
            return discord.utils.MISSING

        view = discord.ui.View()
        for button in buttons:
            label = button.label
            link = button.link

            # regex match emoji in label
            custom_emojis = re.search(
                r'<:\d+>|<:.+?:\d+>|<a:.+:\d+>|[\U00010000-\U0010ffff]', label)
            if custom_emojis is not None:
                emoji = custom_emojis.group(0).strip()
                label = label.replace(emoji, '')
                label = label.strip()
            else:
                emoji = None
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.link, label=label, url=link, emoji=emoji))

        return view

    async def get_all_tags(self) -> List[Tag]:
        return await self.tag_repository.get_all_tags()
