import json
import re
from typing import Optional

import nextcord
import numpy as np
import os


class File:
    def __init__(self, file_name):
        self.file: dict = Optional[None]
        self.file_name = file_name
        self.load()

    def load(self) -> None:
        path = f"{self.file_name}.json"

        if os.path.exists(path):
            with open(path, 'r') as f:
                self.file = json.load(f)
        else:
            self.file = {}

    def save(self) -> None:
        with open(f"{self.file_name}.json", 'w') as f:
            json.dump(self.file, f, indent=2)


class ChatData(File):
    def __init__(self):
        super(ChatData, self).__init__("chat_data")

    def messages(self) -> list[str]:
        return self.file["chat"]

    def apply(self, messages: [str]):
        self.file["chat"] = messages
        self.save()


class Config(File):
    def __init__(self):
        super(Config, self).__init__("config")

    def token(self) -> str:
        return self.file["token"]

    def activated_channels(self) -> dict:
        return self.file["activated_channels"]

    def topics(self) -> list[str]:
        topics = []
        for key in self.activated_channels().keys():
            nested: dict = self.activated_channels()[key]
            for topic in nested.values():
                if topic not in topics:
                    topics.append(topic)
        return topics

    def get_topic(self, channel: nextcord.TextChannel) -> Optional[str]:
        activated_channels: dict = self.activated_channels()
        channels: dict = activated_channels.get(str(channel.guild.id))

        if not channels:
            return None

        return channels.get(str(channel.id))

    def is_channel_activated(self, channel: nextcord.TextChannel) -> bool:
        activated_channels: dict = self.activated_channels()
        channels: list = activated_channels.get(str(channel.guild.id))
        return channels is not None and channel.id in channels

    def enable_channel(self, channel: nextcord.TextChannel, topic: str) -> bool:
        activated_channels: dict = self.activated_channels()
        channels: dict = activated_channels.get(str(channel.guild.id))

        if not channels:
            channels = {}
            activated_channels[str(channel.guild.id)] = channels

        if str(channel.id) in channels:
            return False

        channels[str(channel.id)] = topic
        self.save()
        return True

    def disable_channel(self, channel: nextcord.TextChannel) -> bool:
        activated_channels: dict = self.activated_channels()
        channels: dict = activated_channels.get(str(channel.guild.id))

        if not channels or str(channel.id) not in channels:
            return False

        channels.pop(str(channel.id))
        if len(channels) == 0:
            activated_channels.pop(str(channel.guild.id))

        self.save()
        return True


class FaqEntry:
    def __init__(self, data: dict, file: File):
        self.data = data
        self.file = file

    def messages(self) -> list[str]:
        return self.data["messages"]

    def add_message(self, message: str) -> bool:
        if self.contains_message(message):
            return False

        self.messages().append(message)
        self.file.save()

    def contains_message(self, message: str) -> bool:
        return message in self.messages()

    def answer(self) -> str:
        return self.data["answer"]

    def up_votes(self) -> int:
        return self.data["up_votes"]

    def vote_up(self) -> None:
        self.data["up_votes"] += 1
        self.file.save()

    def down_votes(self) -> int:
        return self.data["down_votes"]

    def votes(self) -> int:
        return self.up_votes() + self.down_votes()

    def vote_down(self) -> None:
        self.data["down_votes"] += 1
        self.file.save()

    def short(self) -> str:
        return self.data["short"]

    def set_short(self, text: str):
        self.data["short"] = text

    def set_answer(self, text: str):
        self.data["answer"] = text


class LinkedFaqEntry(FaqEntry):
    def __init__(self, entry_id: int, data: dict, file: File):
        super().__init__(data, file)
        self.id = entry_id


class Data(File):
    def __init__(self, topic: str):
        super(Data, self).__init__("data")
        self.topic = topic
        self.__repair_messages__()

    def faq(self) -> list[dict]:
        topics: dict = self.file["faq"]
        faq = topics.get(self.topic)

        if faq:
            return faq
        else:
            return []

    def is_valid(self) -> bool:
        return len(self.faq()) > 0

    def linked_faq(self) -> list[LinkedFaqEntry]:
        entries = []
        entry_id = 0

        for e in self.faq():
            entry = LinkedFaqEntry(entry_id, e, self)
            entries.append(entry)
            entry_id += 1

        return entries

    def faq_entry(self, idx: int) -> LinkedFaqEntry:
        return LinkedFaqEntry(idx, self.faq()[idx], self)

    def faq_entry_by_short(self, short: str) -> Optional[LinkedFaqEntry]:
        short = short.lower().strip()

        entry_id = 0
        for e in self.faq():
            entry = LinkedFaqEntry(entry_id, e, self)
            if entry.short() == short:
                return entry
            entry_id += 1
        return None

    def faq_entry_by_answer(self, answer: str) -> Optional[LinkedFaqEntry]:
        entry_id = 0
        for e in self.faq():
            entry = LinkedFaqEntry(entry_id, e, self)
            if entry.answer() == answer:
                return entry
            entry_id += 1
        return None

    def add_faq_entry(self, answer: str, short: str) -> None:
        entry: dict = {
            "messages": [],
            "answer": answer,
            "up_votes": 0,
            "down_votes": 0,
            "short": short
        }

        self.faq().append(entry)
        self.save()

    def delete_faq_entry(self, entry: LinkedFaqEntry):
        self.faq().pop(entry.id)
        self.save()

    def fill_words(self) -> list[str]:
        return self.file["fill_words"]

    def nonsense(self) -> list[str]:
        return self.file["nonsense"]

    def contains_nonsense(self, text: str) -> bool:
        return text in self.nonsense()

    def add_nonsense(self, text: str) -> None:
        if self.contains_nonsense(text):
            return

        self.nonsense().append(text)
        self.save()

    def __repair_messages__(self) -> None:
        changed = False

        for e in self.faq():
            entry = FaqEntry(e, self)
            messages: list = entry.messages()
            if self.__repair_message_list__(messages):
                changed = True

        if self.__repair_message_list__(self.nonsense()):
            changed = True

        if changed:
            self.save()

    def __repair_message_list__(self, messages: [str]) -> bool:
        changed = False
        pop = []

        for i in range(len(messages)):
            new_message = self.clean_message(messages[i])

            if len(new_message) > 0:
                if messages[i] != new_message:
                    messages[i] = new_message
                    changed = True
            else:
                pop.append(i)
                changed = True

        # reverse to avoid index out of range
        for i in reversed(pop):
            messages.pop(i)

        # remove duplicates
        values, counts = np.unique(messages, return_counts=True)
        for idx in range(len(values)):
            value = values[idx]
            duplicates = counts[idx] - 1

            if duplicates > 0:
                changed = True
                for _ in range(duplicates):
                    messages.remove(value)

        return changed

    def clean_message(self, message: str) -> str:
        message = message.lower()
        message = re.sub("[^a-z0-9 ]*", "", message)  # remove illegal characters
        message = re.sub(r"\b[0-9]+\b", "", message)  # remove words only containing numbers (e.g. @ mentions)

        for fill_word in self.fill_words():
            message = re.sub(r"\b" + fill_word + r"\b", "", message)

        message = re.sub(r" +", " ", message)
        message = message.strip()
        return message
