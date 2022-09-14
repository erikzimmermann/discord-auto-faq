import math
from typing import Optional

import nextcord
from nextcord.ext.commands import Bot

import core.log as log
from core.classifier import BertClassifier
from core.files import Config, Data, LinkedFaqEntry
from core.ui import AutoResponseView


class Store:
    def __init__(self, bot: nextcord.ext.commands.Bot):
        self.classifiers: dict = {}
        self.config = Config()
        self.bot = bot

    def load_classifiers(self) -> None:
        self.classifiers = {}

        for topic in self.config.topics():
            self.classifiers[topic] = AutoFaq(
                self.bot,
                topic,
                min_threshold=self.config.min_threshold(),
                max_threshold=self.config.max_threshold()
            )


class AutoFaq:
    def __init__(self, bot: Bot, topic: str, min_threshold: float = 0.3,
                 max_threshold: float = 0.7, random_state: int = None):
        self.bot = bot
        self.topic = topic
        self.min_threshold = min_threshold
        self.max_threshold = max_threshold
        self.random_state = random_state

        self.data = Data(topic)
        self.data.repair_messages()

        self.classifier: Optional[BertClassifier] = None
        self.__load__()

    def refit(self) -> None:
        self.data = Data(self.topic)
        self.__load__()

    def __load__(self):
        self.classifier = BertClassifier(self.data)

    async def check_message(self, content: str, reply_on: nextcord.Message) -> bool:
        answer_id, p = self.classifier.predict(content)

        if answer_id is None:
            # message classified as nonsense
            log.info("Incoming message:", content, "(nonsense" + (f", {round(p, 4)}" if p else "") + ")")
            return False

        # change class index to answer_id
        entry = self.data.faq_entry(answer_id)
        threshold = self.calculate_threshold(answer_id)

        log.info("Incoming message:", content,
                 f"({entry.short()}, p={round(p, 4)}, threshold={threshold}, {p >= threshold})")

        if p >= threshold:
            await self.send_faq(reply_on, answer_id, entry.answer(), True)
            return True
        else:
            return False

    async def send_faq(self, reply_on: nextcord.Message, answer_id: int, answer: str, allow_feedback: bool) -> None:
        if allow_feedback:
            view = AutoResponseView(reply_on.author, lambda vote: self.apply_vote(answer_id, vote))
            response = await reply_on.reply(answer, view=view, mention_author=False)
            view.apply_context(response)
        else:
            await reply_on.reply(answer)

    def apply_vote(self, answer_id: int, vote: int) -> None:
        if vote > 0:
            self.data.faq_entry(answer_id).vote_up()
        elif vote < 0:
            self.data.faq_entry(answer_id).vote_down()

    async def add_message_by_short(self, command: nextcord.Message, referenced: nextcord.Message,
                                   answer_abbreviation: str) -> None:
        content = self.data.clean_message(referenced.content)
        if len(content) == 0:
            await command.add_reaction("🤔")
            return

        answer_abbreviation = answer_abbreviation.lower()

        if answer_abbreviation == "ignore":
            await self.add_message_to_nonsense(command, content, referenced)
            return

        message_id = 0
        entry = self.data.faq_entry_by_short(answer_abbreviation)

        if entry:
            if entry.add_message(content):
                log.info(f"The message '{referenced.content}' was added to the '{entry.short()}' dataset",
                         f"by {command.author.name}#{command.author.discriminator}.")
            await self.send_faq(referenced, message_id, entry.answer(), False)
            self.refit()
            return

        await command.add_reaction("🤔")

    async def delete_old_response(self, reference: nextcord.Message, message_range: int = 20) -> None:
        async for old in reference.channel.history(limit=message_range):
            member: nextcord.Member = old.author
            if member.id == self.bot.user.id and old.reference:
                if old.reference.message_id == reference.id:
                    await old.delete()
                    break

    async def add_message_to_nonsense(self, command: nextcord.Message, content: str, referenced: nextcord.Message):
        self.data.add_nonsense(content)
        self.refit()

        log.info(f"The message '{referenced.content}' was added to the nonsense dataset",
                 f"by {command.author.name}#{command.author.discriminator}.")

        await self.delete_old_response(referenced)

        await command.add_reaction("✅")

    async def create_answer(self, answer: str, short: str, interaction: nextcord.Interaction) -> bool:
        if short == "ignore":
            await interaction.send(f"The short *{short}* is reserved. Please choose another one. 😕", ephemeral=True)
            return False

        entry: LinkedFaqEntry = self.data.faq_entry_by_short(short)
        if entry:
            await interaction.send(f"The short '{short}' is already registered. 👀\n"
                                   f"It's answer is '{entry.answer()}'",
                                   ephemeral=True)
            return False

        entry: LinkedFaqEntry = self.data.faq_entry_by_answer(answer)
        if entry:
            await interaction.send(f"The answer '{answer}' is already registered. 👀\n"
                                   f"It's short is '{entry.short()}'",
                                   ephemeral=True)
            return False

        self.data.add_faq_entry(answer, short)
        return True

    def calculate_threshold(self, answer_id: int) -> Optional[float]:
        entry = self.data.faq_entry(answer_id)

        if entry.votes() == 0:
            return 0.5 * self.min_threshold + 0.5 * self.max_threshold

        # ratings gain importance over the default value until 10 votes are reached
        importance = min(math.log(entry.votes()), 1)

        ratio = importance * entry.up_votes() / entry.votes() + (1 - importance) * 0.5  # bad 0 - good 1
        return ratio * self.min_threshold + (1 - ratio) * self.max_threshold


store: Optional[Store] = None


def setup(s: Store) -> Store:
    global store
    store = s
    return s
