import re
from typing import Optional

import nextcord
from nextcord import SlashOption, Embed
from nextcord.ext.commands import Cog, Bot

import core.classifier
from core.faq import Store, AutoFaq
from core.files import LinkedFaqEntry
from core.magic import COLOR_PRIMARY, COLOR_SUCCESS


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.faq.store.config.topics())


class FaqInfo(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(description="Shows the abbreviations of every FAQ message.",
                            dm_permission=False, guild_ids=[932268427333210142])
    async def faq(self, interaction: nextcord.Interaction,
                  topic: str = SlashOption(
                      description="This defines the topic this FAQ entry will be created in.",
                      required=True,
                      autocomplete=True,
                      autocomplete_callback=autocomplete_topic
                  ),
                  abbreviation: Optional[str] = SlashOption(
                      description="The abbreviation of the FAQ entry."
                  )):
        classifier: AutoFaq = self.store.classifiers.get(topic)

        if not classifier:
            await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                                   ephemeral=True)
            return

        if abbreviation:
            entry: LinkedFaqEntry = classifier.data.faq_entry_by_short(abbreviation)

            if entry:
                t = classifier.calculate_threshold(entry.id)
                embed = Embed(
                    title="FAQ Entry",
                    description=f"**Topic:** '{classifier.topic}'\n"
                                f"**Short:** '{entry.short()}'\n"
                                f"\n**Votes:** '👍 {entry.up_votes()} 👎 {entry.down_votes()}'\n"
                                f"**Threshold:** {round(t * 100, 4)}%\n"
                                f"\n**Answer:** '{entry.answer()}'",
                    color=COLOR_SUCCESS
                )
                await interaction.send(embed=embed, ephemeral=True)
            else:
                await interaction.send(f"This FAQ entry does not exist. Please try another one.", ephemeral=True)
            return

        entries = []
        for entry in classifier.data.linked_faq():
            answer = re.sub(r'[^a-zA-Z0-9.,;:äüöÄÜÖ ]*', '', entry.answer())
            short_length = len(entry.short())
            entries.append(f"**{entry.short()}**: "
                           f"'{answer if short_length + len(answer) <= 70 else answer[:70 - short_length] + '...'}'")

        response = f"To see the full answer, please use the 'abbreviation' argument for this command.\n"
        for e in sorted(entries):
            response += "\n" + e

        if len(response) == 0:
            await interaction.send("There are no FAQ entries yet. Create one with `/faq_add`.")
        else:
            embed = Embed(
                title=f"FAQs in topic *{classifier.topic}*",
                description=response,
                color=COLOR_PRIMARY
            )
            await interaction.send(embed=embed, ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(FaqInfo(bot, core.faq.store))
