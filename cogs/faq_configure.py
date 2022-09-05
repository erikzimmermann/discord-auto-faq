import nextcord
from nextcord import SlashOption
from nextcord.ext.commands import Cog, Bot

import core.classifier
from core.classifier import Store, AutoFaq


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.classifier.store.config.topics())


class FaqConfig(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(description="Reloads the FAQ from its files.", dm_permission=False)
    async def faq_reload(self, interaction: nextcord.Interaction):
        self.store.load_classifiers()
        await interaction.send("The FAQ has been reloaded.", ephemeral=True)

    @nextcord.slash_command(description="Adds an automated answer to the FAQ.",
                            dm_permission=False)
    async def faq_add(self, interaction: nextcord.Interaction,
                      abbreviation: str = SlashOption(
                          description="This abbreviation will be used to add more message to "
                                      "the dataset and print FAQ answers for users.",
                          min_length=2,
                          max_length=15,
                          required=True),
                      answer: str = SlashOption(description="The formatted answer that will be send to users.",
                                                min_length=10,
                                                max_length=500,
                                                required=True),
                      topic: str = SlashOption(description="This defines the topic this FAQ entry will be created in.",
                                               required=True,
                                               autocomplete=True,
                                               autocomplete_callback=autocomplete_topic)):
        abbreviation = abbreviation.lower().strip()
        word_count = len(abbreviation.split(" "))
        if word_count != 1:
            await interaction.send(f"Your abbreviation cannot be longer than one word.", ephemeral=True)
            return

        classifier: AutoFaq = self.store.classifiers.get(topic)

        if not classifier:
            await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                                   ephemeral=True)
            return

        if await classifier.create_answer(answer, abbreviation, interaction):
            await interaction.send(f"Your answer *{answer}* was created. Short: *{abbreviation}*", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(FaqConfig(bot, core.classifier.store))