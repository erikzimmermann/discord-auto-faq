import nextcord
from nextcord import SlashOption
from nextcord.ext.commands import Cog, Bot

import core.classifier
from core.faq import Store, AutoFaq
from core.files import LinkedFaqEntry
from core.ui import FaqEditModal, FaqDeleteModal
import core.log as log


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.faq.store.config.topics())


async def faq_edit_callback(modal: FaqEditModal, interaction: nextcord.Interaction):
    entry: LinkedFaqEntry = modal.entry
    response = f"Following changes in topic *{modal.topic}* were saved:\n"
    changed = False
    old_short = entry.short()

    if modal.short.value != entry.short():
        response += f"Short: *{entry.short()}* -> *{modal.short.value}*"
        entry.set_short(modal.short.value)
        changed = True

    if modal.answer.value != entry.answer():
        response += f"Answer: \n{entry.answer()} \n-> \n{modal.answer.value}"
        entry.set_answer(modal.answer.value)
        changed = True

    if not changed:
        await interaction.send("No changes were made.", ephemeral=True)
        return
    else:
        log.info(f"The FAQ entry '{old_short}' has been edited",
                 f"by {interaction.user.name}#{interaction.user.discriminator}.", response)

        modal.data.save()
        await interaction.send(response, ephemeral=True)


async def faq_delete_callback(modal: FaqEditModal, interaction: nextcord.Interaction):
    entry: LinkedFaqEntry = modal.entry

    if entry.short().upper() != modal.short.value:
        await interaction.send(
            f"The FAQ entry was **not** deleted. (*{modal.short.value}* ≠ *{entry.short().upper()}*)",
            ephemeral=True
        )
        return

    modal.data.delete_faq_entry(entry)

    log.info(f"The FAQ entry '{entry.short()}' has been deleted",
             f"by {interaction.user.name}#{interaction.user.discriminator}. It's answer was: '{entry.answer()}'")

    await interaction.send(f"The FAQ entry *{entry.short()}* was **deleted** successfully.", ephemeral=True)


async def check_parameters(interaction: nextcord.Interaction, topic: str, abbreviation: str, store: Store) \
        -> (str, str, AutoFaq):
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

    @nextcord.slash_command(description="Reloads the FAQ from its files.", dm_permission=False)
    async def faq_reload(self, interaction: nextcord.Interaction):
        self.store.load_classifiers()
        log.info("All classifiers have been reloaded", f"by {interaction.user.name}#{interaction.user.discriminator}.")
        await interaction.send("The FAQ has been reloaded.", ephemeral=True)

    @nextcord.slash_command(description="Adds an automated answer to the FAQ.",
                            dm_permission=False)
    async def faq_add(self, interaction: nextcord.Interaction,
                      abbreviation: str = SlashOption(
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
            log.info(f"The FAQ entry '{abbreviation}' has been created",
                     f"by {interaction.user.name}#{interaction.user.discriminator}. Answer: '{answer}'")
            await interaction.send(f"Your answer *{answer}* was created. Short: *{abbreviation}*", ephemeral=True)

    @nextcord.slash_command(description="Edits an FAQ entry.",
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
            await interaction.response.send_modal(FaqEditModal(topic, entry, classifier.data, faq_edit_callback))

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
            await interaction.response.send_modal(FaqDeleteModal(topic, entry, classifier.data, faq_delete_callback))


def setup(bot: Bot):
    bot.add_cog(FaqConfig(bot, core.faq.store))
