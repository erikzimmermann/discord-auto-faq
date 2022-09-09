import nextcord
from nextcord import Embed
from nextcord.ext.commands import Cog, Bot

import core.classifier
from core.faq import Store
from core.magic import COLOR_PRIMARY


class FaqHelp(Cog):
    def __init__(self, bot: Bot, store: Store):
        self.bot = bot
        self.store = store

    @nextcord.slash_command(description="Shows the abbreviations of every FAQ message.",
                            dm_permission=False)
    async def faq_help(self, interaction: nextcord.Interaction):
        embed = Embed(
            title="Help",
            description=f"**Corrections** 📝\n"
                        f"*Always* reference user messages if their responses should be corrected.\n"
                        f"\n"
                        f"To *ignore* a message, use: '{self.bot.user.mention} ignore'\n"
                        f"To *invoke* or *change* a response, use '{self.bot.user.mention} <abbreviation>'\n"
                        f"\n"
                        f"**Useful Commands** ⚙\n"
                        f"A *topic* represents a single category of FAQ entries.\n"
                        f"\n"
                        f"Enable/disable AutoFAQ in channels: `/faq_enable` or `/faq_disable`\n"
                        f"View abbreviations and responses: `/faq`\n"
                        f"Add new FAQ entries: `/faq_add`\n"
                        f"Edit FAQ entries: `/faq_edit`"
            ,
            color=COLOR_PRIMARY
        )
        await interaction.send(embed=embed, ephemeral=True)


def setup(bot: Bot):
    bot.add_cog(FaqHelp(bot, core.faq.store))
