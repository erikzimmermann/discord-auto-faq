import nextcord
from nextcord import SlashOption, Embed
from nextcord.ext.commands import Cog, Bot

import core.classifier
from core.faq import Store, AutoFaq
from core.files import LinkedFaqEntry


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.faq.store.config.topics())


class FaqTest(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(
        description="Allows staff to make predictions for custom messages.",
        dm_permission=False)
    async def faq_test(self, interaction: nextcord.Interaction,
                       message: str = SlashOption(
                           description="The message you want to test.",
                           required=True,
                           min_length=5,
                           max_length=200
                       ),
                       topic: str = SlashOption(
                           description="This defines the topic this FAQ entry will be created in.",
                           required=True,
                           autocomplete=True,
                           autocomplete_callback=autocomplete_topic
                       )):
        if not isinstance(interaction.channel, nextcord.TextChannel):
            return

        topic = topic.lower().strip()
        faq: AutoFaq = self.store.classifiers.get(topic)

        if not faq:
            await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                                   ephemeral=True)
            return

        class_id, p = faq.classifier.predict(message)

        if class_id is not None:
            entry: LinkedFaqEntry = faq.data.faq_entry(class_id)
            e = Embed(
                # title="AutoFAQ prediction",
                description=f"**Prediction:** '{entry.short()}'\n"
                            f"**Probability:** {round(p * 100, 4)}%\n"
                            f"**Response:** '{entry.answer()}'",
                color=0x12A498
            )
        elif p is not None:
            e = Embed(
                # title="AutoFAQ prediction",
                description=f"**Prediction:** Ignore\n"
                            f"**Probability:** {round(p * 100, 4)}%",
                color=0x12A498
            )
        else:
            e = Embed(
                # title="AutoFAQ prediction",
                description=f"**Prediction:** Ignore\n"
                            f"**Reason:** *To few or much content*",
                color=0x12A498
            )

        await interaction.send(embed=e, ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(FaqTest(bot, core.faq.store))
