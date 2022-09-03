import nextcord
from nextcord.ext import commands

import core.classifier
from core.classifier import Store, AutoFaq


class DataInfo(commands.Cog):
    @nextcord.slash_command(description="Prints the chat formatted as nonsense in the console.",
                            default_member_permissions=nextcord.Permissions(administrator=True), dm_permission=False)
    async def nonsense(self, interaction: nextcord.Interaction, message_count: int) -> None:
        """
            Useful to set up the nonsense class for the classifier.

        :param interaction: The discord interaction.
        :param message_count: The number of message that should be displayed.
        """
        if not isinstance(interaction.channel, nextcord.TextChannel):
            return

        content = []
        async for message in interaction.channel.history(limit=message_count):
            content.append(message.content)

        print(content)


class FaqInfo(commands.Cog):
    def __init__(self, bot: commands.Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(description="Shows the abbreviations of every FAQ message.",
                            default_member_permissions=nextcord.Permissions(use_slash_commands=True),
                            dm_permission=False)
    async def faq(self, interaction: nextcord.Interaction, topic: str):
        classifier: AutoFaq = self.store.classifiers.get(topic)

        if not classifier:
            await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                                   ephemeral=True)
            return

        response = ""
        for entry in classifier.data.linked_faq():
            if len(response) > 0:
                response += "\n"
            response += f"*{entry.short()}*: {entry.answer()}"
        await interaction.send(response, ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(DataInfo())
    bot.add_cog(FaqInfo(bot, core.classifier.store))
