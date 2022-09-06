import nextcord
from nextcord import SlashOption
from nextcord.ext.commands import Cog, Bot

import core.classifier
from core.classifier import Store, AutoFaq
from core.files import ChatData


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.classifier.store.config.topics())


class DataInfo(Cog):
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


class FaqInfo(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(description="Shows the abbreviations of every FAQ message.",
                            dm_permission=False)
    async def faq(self, interaction: nextcord.Interaction,
                  topic: str = SlashOption(
                      description="This defines the topic this FAQ entry will be created in.",
                      required=True,
                      autocomplete=True,
                      autocomplete_callback=autocomplete_topic
                  )):
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

    @nextcord.slash_command(description="Saves the chat of the current channel to a file.",
                            default_member_permissions=nextcord.Permissions(administrator=True), dm_permission=False)
    async def save_chat(self, interaction: nextcord.Interaction, message_count: int) -> None:
        if not isinstance(interaction.channel, nextcord.TextChannel):
            return

        await interaction.send("Done", ephemeral=True)

        content = []
        count = 0
        async for message in interaction.channel.history(limit=message_count):
            content.append(message.content)

            count += 1
            if count % 250 == 0:
                print(count)

        print(content)
        data = ChatData()
        data.apply(content)


def setup(bot: Bot):
    bot.add_cog(DataInfo())
    bot.add_cog(FaqInfo(bot, core.classifier.store))
