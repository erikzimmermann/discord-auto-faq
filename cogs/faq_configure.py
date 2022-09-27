import nextcord
from nextcord import SlashOption, Embed
from nextcord.ext.commands import Cog, Bot

import core.classifier
import core.log as log
from core.faq import Store, AutoFaq
from core.files import LinkedFaqEntry
from core.magic import COLOR_SUCCESS, COLOR_DANGER
from core.ui import FaqEditModal, FaqDeleteUndoView


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.faq.store.config.topics())


async def faq_edit_callback(modal: FaqEditModal, interaction: nextcord.Interaction):
    entry: LinkedFaqEntry = modal.entry
    response = f"Following changes in topic {modal.faq.topic} were saved:"
    changed = False
    old_short = entry.short()

    short_input = modal.short.value.lower().strip()
    if short_input != entry.short():
        response += f"\n\n**Short**\n" \
                    f"*before:* '{entry.short()}'\n" \
                    f"*after:* '{short_input}'"
        entry.set_short(short_input)
        changed = True

    if modal.answer.value != entry.answer():
        response += f"\n\n**Answer**\n" \
                    f"*before:* '{entry.answer()}'\n" \
                    f"*after:* '{modal.answer.value}'"
        entry.set_answer(modal.answer.value)
        changed = True

    if not changed:
        await interaction.send("No changes were made.", ephemeral=True)
        return
    else:
        embed = Embed(
            title="FAQ Edit",
            description=response,
            color=COLOR_SUCCESS
        )
        await interaction.send(embed=embed, ephemeral=True)

        log.info(f"The FAQ entry '{old_short}' has been edited",
                 f"by {interaction.user.name}#{interaction.user.discriminator}.",
                 response.replace('*', ''))

        modal.faq.data.save()
        modal.faq.refit()


async def check_parameters(interaction: nextcord.Interaction, topic: str, abbreviation: str, store: Store) \
        -> (str, AutoFaq, AutoFaq):
    abbreviation = abbreviation.lower().strip()
    classifier: AutoFaq = store.classifiers.get(topic)

    if not classifier:
        await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                               ephemeral=True)
        return None, None, None

    entry: LinkedFaqEntry = classifier.data.faq_entry_by_short(abbreviation)

    if not entry:
        await interaction.send(f"This FAQ entry does not exist. You can create an FAQ entry by using `/faq_add`.",
                               ephemeral=True)
        return None, None, None
    return abbreviation, classifier, entry


class FaqConfig(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(
        description="Reloads the FAQ from its files.",
        default_member_permissions=nextcord.Permissions(moderate_members=True),
        dm_permission=False)
    async def faq_reload(self, interaction: nextcord.Interaction):
        self.store.load_classifiers()
        log.info("All classifiers have been reloaded", f"by {interaction.user.name}#{interaction.user.discriminator}.")
        await interaction.send("The FAQ has been reloaded.", ephemeral=True)

    @nextcord.slash_command(description="Adds an automated answer to the FAQ.",
                            default_member_permissions=nextcord.Permissions(moderate_members=True),
                            dm_permission=False)
    async def faq_add(self, interaction: nextcord.Interaction,
                      short: str = SlashOption(
                          description="This abbreviation will be used to add more message to "
                                      "the dataset and print FAQ answers for users.",
                          min_length=2,
                          max_length=15,
                          required=True
                      ),
                      answer: str = SlashOption(
                          description="The formatted answer that will be send to users.",
                          min_length=10,
                          max_length=500,
                          required=True
                      ),
                      topic: str = SlashOption(
                          description="This defines the topic this FAQ entry will be created in.",
                          required=True,
                          autocomplete=True,
                          autocomplete_callback=autocomplete_topic
                      )):
        short = short.lower().strip()
        word_count = len(short.split(" "))
        if word_count != 1:
            await interaction.send(f"Your abbreviation cannot be longer than one word. 😧", ephemeral=True)
            return

        classifier: AutoFaq = self.store.classifiers.get(topic)

        if not classifier:
            await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`. 🤔",
                                   ephemeral=True)
            return

        if await classifier.create_answer(answer, short, interaction):
            log.info(f"The FAQ entry '{short}' has been created",
                     f"by {interaction.user.name}#{interaction.user.discriminator}. Answer: '{answer}'")

            embed = Embed(
                title="FAQ Entry Creation",
                description=f"Your FAQ entry was created successfully. 👌\n"
                            f"\n"
                            f"**Topic:** '{classifier.topic}'\n"
                            f"**Short:** '{short}'\n"
                            f"**Answer:** '{answer}'",
                color=COLOR_SUCCESS
            )
            await interaction.send(embed=embed, ephemeral=True)

    @nextcord.slash_command(description="Edits an FAQ entry.",
                            default_member_permissions=nextcord.Permissions(moderate_members=True),
                            dm_permission=False)
    async def faq_edit(self, interaction: nextcord.Interaction,
                       topic: str = SlashOption(
                           description="The FAQ topic which should be altered.",
                           required=True,
                           autocomplete=True,
                           autocomplete_callback=autocomplete_topic
                       ),
                       abbreviation: str = SlashOption(
                           description="The abbreviation of the FAQ entry.",
                           required=True)
                       ):
        abbreviation, classifier, entry = await check_parameters(interaction, topic, abbreviation, self.store)

        if abbreviation and classifier and entry:
            await interaction.response.send_modal(FaqEditModal(entry, classifier, faq_edit_callback))

    @nextcord.slash_command(description="Deletes an FAQ entry.",
                            default_member_permissions=nextcord.Permissions(administrator=True),
                            dm_permission=False)
    async def faq_delete(self, interaction: nextcord.Interaction,
                         topic: str = SlashOption(
                             description="The FAQ topic which should be altered.",
                             required=True,
                             autocomplete=True,
                             autocomplete_callback=autocomplete_topic
                         ),
                         abbreviation: str = SlashOption(
                             description="The abbreviation of the FAQ entry.",
                             required=True)
                         ):
        abbreviation, classifier, entry = await check_parameters(interaction, topic, abbreviation, self.store)

        if abbreviation and classifier and entry:
            classifier.data.delete_faq_entry(entry)

            log.info(f"The FAQ entry '{entry.short()}' has been deleted",
                     f"by {interaction.user.name}#{interaction.user.discriminator}. It's answer was: '{entry.answer()}'")

            embed = Embed(
                title="FAQ Entry Deletion",
                description=f"Your FAQ entry was deleted successfully. 🗑️\n"
                            f"\n"
                            f"**Topic:** '{classifier.topic}'\n"
                            f"**Short:** '{entry.short()}'\n"
                            f"**Answer:** '{entry.answer()}'\n"
                            f"\n"
                            f"*Click on 'restore' to undo your action.*",
                color=COLOR_DANGER
            )
            await interaction.send(embed=embed, view=FaqDeleteUndoView(classifier, entry), ephemeral=True)

            classifier.refit()


def setup(bot: Bot):
    bot.add_cog(FaqConfig(bot, core.faq.store))
