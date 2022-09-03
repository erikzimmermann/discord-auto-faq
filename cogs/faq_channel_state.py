import nextcord
from nextcord import SlashOption
from nextcord.ext import commands

import core.classifier
from core.classifier import Store


class FaqChannel(commands.Cog):
    def __init__(self, bot: commands.Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(
        description="Enables the auto FAQ to listen to the channel where this command will be executed.", dm_permission=False)
    async def faq_enable(self, interaction: nextcord.Interaction,
                         topic: str = SlashOption(description="The topic name will be used to link FAQ entries to it.",
                                                  required=True)):
        if not isinstance(interaction.channel, nextcord.TextChannel):
            return

        topic = topic.lower().strip()

        no_data = self.store.classifiers.get(topic) is None

        if self.store.config.enable_channel(interaction.channel, topic):
            if no_data:
                await interaction.send(
                    f"AutoFAQ with the topic *{topic}* is now activated for this channel. "
                    f"For now, this topic has **no FAQ entries**. Fill your FAQ with `/faq_add`.",
                    ephemeral=True)
            else:
                await interaction.send(f"AutoFAQ with the topic *{topic}* is now activated for this channel.",
                                       ephemeral=True)
        else:
            await interaction.send("AutoFAQ is already activated for this channel.", ephemeral=True)

    @nextcord.slash_command(description="Disables the auto FAQ for the channel where this command will be executed.",
                            dm_permission=False)
    async def faq_disable(self, interaction: nextcord.Interaction):
        if not isinstance(interaction.channel, nextcord.TextChannel):
            return

        if self.store.config.disable_channel(interaction.channel):
            await interaction.send("AutoFAQ is now disabled for this channel.", ephemeral=True)
        else:
            await interaction.send("AutoFAQ is not activated for this channel.", ephemeral=True)


def setup(bot: commands.Bot):
    bot.add_cog(FaqChannel(bot, core.classifier.store))
