from typing import Optional, Callable
import nextcord.ui
from nextcord.ui import View


class AutoResponseView(View):
    def __init__(self, addressed: nextcord.Member, callback: Callable[[int], None]):
        super().__init__()
        self.addressed = addressed
        self.callback = callback
        self.vote: int = 0
        self.message: Optional[nextcord.Message] = None

    def apply_context(self, message: nextcord.Message):
        self.message = message

    async def __finish_feedback__(self, interaction: nextcord.Interaction):
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
    async def vote_up(self, button: nextcord.Button, interaction: nextcord.Interaction):
        if not await self.__check_member__(interaction.user, interaction):
            return

        if self.vote != 0:
            return

        self.vote = 1
        self.callback(self.vote)
        await self.__finish_feedback__(interaction)

    @nextcord.ui.button(label="This is not helpful.", style=nextcord.ButtonStyle.gray)
    async def vote_down(self, button: nextcord.Button, interaction: nextcord.Interaction):
        if not await self.__check_member__(interaction.user, interaction):
            return

        if self.vote != 0:
            return

        self.vote = -1
        self.callback(self.vote)
        await self.__finish_feedback__(interaction)
