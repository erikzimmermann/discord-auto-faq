import re

import nextcord
from nextcord import SlashOption
from nextcord.ext import commands

import core.classifier
from core.classifier import Store, AutoFaq


def get_role_position(user: nextcord.Member) -> int:
    max_pos = 0
    for role in user.roles:
        max_pos = max(max_pos, role.position)
    return max_pos


class FaqListener(commands.Cog):
    def __init__(self, bot: commands.Bot, store: Store):
        self.bot = bot
        self.store = store

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return

        topic = self.store.config.get_topic(message.channel)
        if not topic:
            return

        classifier: AutoFaq = self.store.classifiers[topic]

        if self.has_permission(message.author) and self.bot.user in message.mentions:
            content = re.sub('<@[0-9]*>', '', message.content.lower())
            short = content.strip()

            if message.reference:
                await self.process_add(topic, message, short)
            else:
                entry = classifier.data.faq_entry_by_short(short)
                if entry:
                    await message.channel.send(entry.answer())
                else:
                    await message.add_reaction("🤔")
            return

        await classifier.check_message(message)

    async def process_add(self, topic: str, message: nextcord, short: str):
        ref: nextcord.MessageReference = message.reference
        fetched: nextcord.Message = await message.channel.fetch_message(ref.message_id)
        await self.store.classifiers[topic].add_message_by_short(message, fetched, short)

    def has_permission(self, user: nextcord.Member) -> bool:
        bot_member: nextcord.Member = user.guild.get_member(self.bot.user.id)
        bot_pos = get_role_position(bot_member)
        user_pos = get_role_position(user)
        return bot_pos <= user_pos


def setup(bot: commands.Bot):
    bot.add_cog(FaqListener(bot, core.classifier.store))