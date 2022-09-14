import re
from typing import Optional

import nextcord
from nextcord.ext import commands

import core.classifier
from core import magic
from core.faq import Store, AutoFaq
import time
import datetime


def get_role_position(user: nextcord.Member) -> int:
    max_pos = 0
    for role in user.roles:
        max_pos = max(max_pos, role.position)
    return max_pos


def has_permission(user: nextcord.Member) -> bool:
    return user.guild_permissions.use_slash_commands


class ResponseLimiter:
    def __init__(self, limit_in_sec: int = 10):
        self.replies = dict()
        self.limit_in_sec = limit_in_sec

    def __remove_unnecessary__(self):
        t = time.time()

        discarding = []
        for key in self.replies.keys():
            last = self.replies[key]
            if t - last >= self.limit_in_sec:
                discarding.append(key)

        for key in discarding:
            self.replies.pop(key)

    def check(self, user_id: int) -> bool:
        self.__remove_unnecessary__()

        last = self.replies.get(user_id)
        t = time.time()

        return last is None or t - last >= self.limit_in_sec

    def add(self, user_id: int) -> None:
        self.replies[user_id] = time.time()


class FaqListener(commands.Cog):
    def __init__(self, bot: commands.Bot, store: Store):
        self.bot = bot
        self.store = store
        self.limiter = ResponseLimiter()

    @commands.Cog.listener()
    async def on_thread_join(self, thread: nextcord.Thread):
        parent = thread.parent

        topic = self.store.config.get_topic(parent)
        if not topic:
            return

        faq: AutoFaq = self.store.classifiers[topic]

        message = None
        async for m in thread.history(limit=2, oldest_first=True):
            if message is not None:
                # This thread is not recently created -> ignore
                return
            message = m

        author: nextcord.Member = await thread.guild.fetch_member(message.author.id)

        if message.author.bot or has_permission(author):
            return

        if not self.limiter.check(author.id):
            return

        if await faq.check_message(thread.name, message):
            self.limiter.add(author.id)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        channel = message.channel
        if isinstance(channel, nextcord.Thread):
            thread: nextcord.Thread = channel

            created_at: Optional[datetime.datetime] = thread.created_at
            if created_at is not None and time.time() - created_at.timestamp() <= magic.THREAD_MESSAGE_IGNORE_TIME:
                return

            channel = thread.parent

        topic = self.store.config.get_topic(channel)
        if not topic:
            return

        if not self.limiter.check(message.author.id):
            return

        faq: AutoFaq = self.store.classifiers[topic]

        if has_permission(message.author):
            if self.bot.user in message.mentions:
                content = re.sub('<@[0-9]*>', '', message.content.lower())
                short = content.strip()

                if message.reference:
                    await self.process_add(topic, message, short)
                else:
                    entry = faq.data.faq_entry_by_short(short)
                    if entry:
                        await message.channel.send(entry.answer())
                    else:
                        await message.add_reaction("🤔")
            else:
                # just ignore message from staff members
                pass
        else:
            if await faq.check_message(message.content, message):
                self.limiter.add(message.author.id)

    async def process_add(self, topic: str, message: nextcord, short: str):
        ref: nextcord.MessageReference = message.reference
        fetched: nextcord.Message = await message.channel.fetch_message(ref.message_id)

        classifier: AutoFaq = self.store.classifiers[topic]

        await classifier.delete_old_response(fetched)
        await classifier.add_message_by_short(message, fetched, short)


def setup(bot: commands.Bot):
    bot.add_cog(FaqListener(bot, core.faq.store))
