import re

import nextcord
from nextcord.ext import commands

import core.classifier
from core.faq import Store, AutoFaq


def get_role_position(user: nextcord.Member) -> int:
    max_pos = 0
    for role in user.roles:
        max_pos = max(max_pos, role.position)
    return max_pos


def has_permission(user: nextcord.Member) -> bool:
    return user.guild_permissions.use_slash_commands


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
            await faq.check_message(message)

    async def process_add(self, topic: str, message: nextcord, short: str):
        ref: nextcord.MessageReference = message.reference
        fetched: nextcord.Message = await message.channel.fetch_message(ref.message_id)

        classifier: AutoFaq = self.store.classifiers[topic]

        await classifier.delete_old_response(fetched)
        await classifier.add_message_by_short(message, fetched, short)


def setup(bot: commands.Bot):
    bot.add_cog(FaqListener(bot, core.faq.store))
