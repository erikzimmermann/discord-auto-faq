from typing import Optional, Callable

import nextcord.ui
from nextcord import Interaction, Embed
from nextcord.ui import View, Modal, Select, TextInput

from core import log
from core.files import LinkedFaqEntry
from core.magic import COLOR_DANGER, COLOR_WARNING


class AutoResponseView(View):
    def __init__(self, addressed: nextcord.Member, callback: Callable[[int], None]):
        super().__init__()
        self.addressed = addressed
        self.callback = callback
        self.vote: int = 0
        self.message: Optional[nextcord.Message] = None

    def apply_context(self, message: nextcord.Message) -> None:
        self.message = message

    async def __finish_feedback__(self, interaction: nextcord.Interaction) -> None:
        if self.vote > 0:
            await self.message.edit(view=None)
        elif self.vote < 0:
            await self.message.delete()

        await interaction.send("Thank you for your feedback!", ephemeral=True)

    async def __check_member__(self, member: nextcord.Member, interaction: nextcord.Interaction) -> bool:
        if member.id == self.addressed.id:
            return True

        await interaction.send("You are not the person I answered to 🤔", ephemeral=True)
        return False

    @nextcord.ui.button(label="This helped me. Thanks.", style=nextcord.ButtonStyle.gray)
    async def vote_up(self, button: nextcord.Button, interaction: nextcord.Interaction) -> None:
        if not await self.__check_member__(interaction.user, interaction):
            return

        if self.vote != 0:
            return

        self.vote = 1
        self.callback(self.vote)
        await self.__finish_feedback__(interaction)

    @nextcord.ui.button(label="This is not helpful.", style=nextcord.ButtonStyle.gray)
    async def vote_down(self, button: nextcord.Button, interaction: nextcord.Interaction) -> None:
        if not await self.__check_member__(interaction.user, interaction):
            return

        if self.vote != 0:
            return

        self.vote = -1
        self.callback(self.vote)
        await self.__finish_feedback__(interaction)


class FaqAddModal(Modal):
    def __init__(self, topics: [str], callback: Callable):
        super(FaqAddModal, self).__init__("FAQ")
        self.callback = callback

        # TODO: discord currently disabled SELECTs; might be worth trying when it's available again
        options = [nextcord.SelectOption(label=topic) for topic in topics]
        self.topic = Select(placeholder="Topic", min_values=1, max_values=1, options=options)
        # self.topic.add_option(label="test", default=True)
        self.add_item(self.topic)

        self.abbreviation = TextInput(
            label="Abbreviation",
            required=True,
            min_length=2,
            max_length=15,
            style=nextcord.TextInputStyle.short
        )
        self.add_item(self.abbreviation)

        self.answer = TextInput(
            label="Answer",
            required=True,
            min_length=10,
            max_length=500,
            style=nextcord.TextInputStyle.paragraph
        )
        self.add_item(self.answer)


class FaqExpandView(View):
    def __init__(self, callback: Callable):
        super().__init__()
        self.callback = callback

    @nextcord.ui.button(label="Add to dataset", style=nextcord.ButtonStyle.success)
    async def add(self, button: nextcord.Button, interaction: nextcord.Interaction) -> None:
        await self.callback(0, interaction)

    @nextcord.ui.button(label="Ignore", style=nextcord.ButtonStyle.gray)
    async def ignore(self, button: nextcord.Button, interaction: nextcord.Interaction) -> None:
        await self.callback(1, interaction)

    @nextcord.ui.button(label="Skip", style=nextcord.ButtonStyle.red)
    async def skip(self, button: nextcord.Button, interaction: nextcord.Interaction) -> None:
        await self.callback(2, interaction)


class FaqEditModal(Modal):
    def __init__(self, entry: LinkedFaqEntry, auto_faq, callback: Callable):
        super(FaqEditModal, self).__init__(f"FAQ Edit: {auto_faq.topic}")
        self.nested_callback = callback
        self.entry = entry
        self.faq = auto_faq

        self.short = TextInput(
            label="Abbreviation", required=True, min_length=2, max_length=15,
            style=nextcord.TextInputStyle.short,
            default_value=entry.short()
        )
        self.add_item(self.short)

        self.answer = TextInput(
            label="Answer", required=True, min_length=10, max_length=500,
            style=nextcord.TextInputStyle.paragraph,
            default_value=entry.answer()
        )
        self.add_item(self.answer)

    async def callback(self, interaction: Interaction):
        await self.nested_callback(self, interaction)


class FaqDeleteUndoView(View):
    def __init__(self, auto_faq, entry: LinkedFaqEntry):
        super().__init__()
        self.faq = auto_faq
        self.entry = entry

    @nextcord.ui.button(label="Restore", style=nextcord.ButtonStyle.gray)
    async def undo(self, button: nextcord.Button, interaction: nextcord.Interaction) -> None:
        if self.faq.data.append_faq_entry(self.entry):
            log.info(f"The FAQ entry '{self.entry.short()}' has been restored",
                     f"by {interaction.user.name}#{interaction.user.discriminator}.")

            embed = Embed(
                title="FAQ Entry Deletion",
                description=f"**Topic:** '{self.faq.data.topic}'\n"
                            f"**Short:** '{self.entry.short()}'\n"
                            f"**Answer:** '{self.entry.answer()}'\n"
                            f"\n"
                            f"*This entry has been restored.*",
                color=COLOR_WARNING
            )
            await interaction.edit(embed=embed, view=None)
            self.faq.refit()
        else:
            embed = Embed(
                title="FAQ Entry Deletion",
                description=f"**Topic:** '{self.faq.data.topic}'\n"
                            f"**Short:** '{self.entry.short()}'\n"
                            f"**Answer:** '{self.entry.answer()}'\n"
                            f"\n"
                            f"This entry could *not* be restored. "
                            f"Either it's abbreviation or answer already exist.",
                color=COLOR_DANGER
            )
            await interaction.edit(embed=embed)
