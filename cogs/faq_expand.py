import asyncio
from typing import Optional

import nextcord
from nextcord import SlashOption
from nextcord.ext.commands import Cog, Bot
from nextcord.interactions import PartialInteractionMessage

import core.classifier
from core.classifier import Store, AutoFaq
from core.files import LinkedFaqEntry
from core.ui import FaqExpandView
import core.log as log


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.classifier.store.config.topics())


class FaqExpand(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

        self.classifier: Optional[AutoFaq] = None
        self.done: int = 0
        self.max_count: int = 0
        self.predictions: Optional[dict] = None
        self.current_message = 0
        self.current_key = None
        self.response: Optional[PartialInteractionMessage] = None

    @nextcord.slash_command(description="Allows easy dataset expanding for the current FAQ.",
                            dm_permission=False)
    async def faq_expand(self, interaction: nextcord.Interaction,
                         chat_history_size: int = SlashOption(
                             description="The number of messages that should be loaded and read.",
                             min_value=1,
                             max_value=50000,
                             required=True
                         ),
                         topic: str = SlashOption(
                             description="This defines the topic this FAQ entry will be created in.",
                             required=True,
                             autocomplete=True,
                             autocomplete_callback=autocomplete_topic
                         )):
        if self.classifier is not None:
            await interaction.send(f"Someone is already expanding the FAQ. Please wait until the process is finished.",
                                   ephemeral=True)
            return

        self.classifier: AutoFaq = self.store.classifiers.get(topic)

        if not self.classifier:
            await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                                   ephemeral=True)
            return

        self.response = await interaction.send(f"Loading chat history 0/{chat_history_size}...",
                                               ephemeral=True)

        content = []
        count = 0
        async for message in interaction.channel.history(limit=chat_history_size):
            content.append(message.content)

            count += 1
            if count % 250 == 0:
                await self.response.edit(f"Loading chat history {count}/{chat_history_size}...")

        await self.response.edit(f"Loading chat history {chat_history_size}/{chat_history_size}. Done.")

        for c in reversed(content):
            cleaned = self.classifier.data.clean_message(c)
            for faq in self.classifier.data.linked_faq():
                if faq.contains_message(cleaned):
                    content.remove(c)

            if self.classifier.data.contains_nonsense(cleaned):
                content.remove(c)

        self.predictions = {}
        self.max_count = 0
        for c in content:
            answer, p = self.classifier.predict(c)
            if answer is not None:
                cat = self.predictions.get(str(answer))
                if not cat:
                    cat = []
                    self.predictions[str(answer)] = cat
                cat.append(c)
                self.max_count += 1

        await self.response.edit(f"Got {self.max_count} possible message(s).")
        await asyncio.sleep(1)

        await self.next()

    async def finish(self):
        await self.response.edit(f"Done. You processed {self.done} message(s).", view=None)

        # apply processed messages
        self.classifier.refit()

        self.classifier = None
        self.done = 0
        self.max_count = 0
        self.predictions = None
        self.current_message = 0
        self.current_key = None
        self.response = None

    async def next(self):
        if self.current_key is None:
            for key in self.predictions.keys():
                self.current_key = key
                break

        if self.current_key is None:
            await self.finish()
            return

        messages = self.predictions[self.current_key]

        if len(messages) <= self.current_message:
            next_key = False
            new_key = None
            for key in self.predictions.keys():
                if next_key:
                    new_key = key
                    break

                if key == self.current_key:
                    next_key = True

            if new_key is None:
                await self.finish()
                return

            self.current_key = new_key
            self.current_message = 0
            messages = self.predictions[self.current_key]

        message = messages[self.current_message]

        await self.provide_message(self.classifier, int(self.current_key), message)

    async def provide_message(self, classifier: AutoFaq, category: int, message: str):
        await self.response.edit(f"**Progress:** {self.done + 1}/{self.max_count}\n"
                                 f"**Current topic:** *{classifier.data.faq_entry(category).short()}*\n\n"
                                 f"{message}", view=FaqExpandView(self.callback))

    async def callback(self, decision: int, interaction: nextcord.Interaction) -> None:
        messages = self.predictions[self.current_key]
        message = messages[self.current_message]
        cleaned = self.classifier.data.clean_message(message)

        if decision == 0:
            # add to dataset
            entry: LinkedFaqEntry = self.classifier.data.faq_entry(int(self.current_key))
            entry.add_message(cleaned)
            log.info(f"The message '{message}' was added to the '{entry.short()}' dataset",
                     f"by {interaction.user.name}#{interaction.user.discriminator}.")
        elif decision == 1:
            # add to ignored dataset
            self.classifier.data.add_nonsense(cleaned)
            log.info(f"The message '{message}' was added to the nonsense dataset",
                     f"by {interaction.user.name}#{interaction.user.discriminator}.")

        self.current_message += 1
        self.done += 1
        await self.next()


def setup(bot: Bot):
    bot.add_cog(FaqExpand(bot, core.classifier.store))
