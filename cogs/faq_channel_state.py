import nextcord
from nextcord import SlashOption
from nextcord.ext.commands import Cog, Bot

import core.classifier
import core.log as log
from core.faq import Store


async def autocomplete_topic(parent_cog: Cog, interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(core.faq.store.config.topics())


class FaqChannel(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(
        description="Enables the auto FAQ to listen to the channel where this command will be executed.",
        dm_permission=False)
    async def faq_enable(self, interaction: nextcord.Interaction,
                         topic: str = SlashOption(
                             description="This defines the topic this FAQ entry will be created in.",
                             required=True,
                             autocomplete=True,
                             autocomplete_callback=autocomplete_topic
                         )):
        channel = interaction.channel

        if isinstance(channel, nextcord.Thread):
            thread: nextcord.Thread = channel
            channel = thread.parent

        if not isinstance(channel, nextcord.TextChannel) and not isinstance(channel, nextcord.ForumChannel):
            await interaction.send(f"The channel type {type(channel.type)} is not supported. 🤔", ephemeral=True)
            return

        old_topic = self.store.config.get_topic(channel)
        if old_topic:
            await interaction.send(
                f"AutoFAQ with the topic *{old_topic}* is already activated in this channel. 🤔"
                f"Disable it first with `/faq_disable`.",
                ephemeral=True)
            return

        topic = topic.lower().strip()

        no_data = self.store.classifiers.get(topic) is None

        if self.store.config.enable_channel(channel, topic):
            log.info("AutoFAQ enabled for channel", f"'{channel.name}'",
                     f"({channel.id}) in guild", f"'{interaction.guild.name}'",
                     f"({interaction.guild.id})", f"by {interaction.user.name}#{interaction.user.discriminator}.")

            if no_data:
                await interaction.send(
                    f"AutoFAQ with the topic *{topic}* is now activated for this channel. 🥳"
                    f"For now, this topic has **no FAQ entries**. Fill your FAQ with `/faq_add`.",
                    ephemeral=True)
            else:
                await interaction.send(f"AutoFAQ with the topic *{topic}* is now activated for this channel. 🥳",
                                       ephemeral=True)
        else:
            await interaction.send("AutoFAQ is already activated for this channel. 🤔", ephemeral=True)

    @nextcord.slash_command(description="Disables the auto FAQ for the channel where this command will be executed.",
                            dm_permission=False)
    async def faq_disable(self, interaction: nextcord.Interaction):
        if self.store.config.disable_channel(interaction.channel):
            log.info("AutoFAQ disabled for channel", f"'{interaction.channel.name}'",
                     f"({interaction.channel.id}) in guild", f"'{interaction.guild.name}'",
                     f"({interaction.guild.id})", f"by {interaction.user.name}#{interaction.user.discriminator}.")

            await interaction.send("AutoFAQ is now disabled for this channel. 🤐", ephemeral=True)
        else:
            await interaction.send("AutoFAQ is not activated for this channel. 🤔", ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(FaqChannel(bot, core.faq.store))
