import re

import nextcord
from nextcord import SlashOption
from nextcord.ext import commands

from core.classifier import AutoFaq, Store
from core.files import Config
from core.ui import FaqAddModal

config: Config = Config()

intents = nextcord.Intents.default()
intents.message_content = True

activity = nextcord.Activity(type=nextcord.ActivityType.playing, name="Support Buddy (BETA)")
bot = commands.Bot(intents=intents, activity=activity)
store = Store(bot)


@bot.event
async def on_message(message: nextcord.Message):
    if message.author.bot:
        return

    topic = config.get_topic(message.channel)
    if not topic:
        return

    classifier: AutoFaq = store.classifiers[topic]

    if has_permission(message.author) and bot.user in message.mentions:
        content = re.sub('<@[0-9]*>', '', message.content.lower())
        short = content.strip()

        if message.reference:
            await process_add(topic, message, short)
        else:
            entry = classifier.data.faq_entry_by_short(short)
            if entry:
                await message.channel.send(entry.answer())
            else:
                await message.add_reaction("🤔")
        return

    await classifier.check_message(message)


@bot.slash_command(description="Enables the auto FAQ to listen to the channel where this command will be executed.",
                   default_member_permissions=nextcord.Permissions(use_slash_commands=True), dm_permission=False)
async def faq_enable(interaction: nextcord.Interaction,
                     topic: str = SlashOption(description="The topic name will be used to link FAQ entries to it.",
                                              required=True)):
    if not isinstance(interaction.channel, nextcord.TextChannel):
        return

    topic = topic.lower().strip()

    no_data = store.classifiers.get(topic) is None

    if config.enable_channel(interaction.channel, topic):
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


@bot.slash_command(description="Disables the auto FAQ for the channel where this command will be executed.",
                   default_member_permissions=nextcord.Permissions(use_slash_commands=True), dm_permission=False)
async def faq_disable(interaction: nextcord.Interaction):
    if not isinstance(interaction.channel, nextcord.TextChannel):
        return

    if config.disable_channel(interaction.channel):
        await interaction.send("AutoFAQ is now disabled for this channel.", ephemeral=True)
    else:
        await interaction.send("AutoFAQ is not activated for this channel.", ephemeral=True)


async def check_topic(interaction: nextcord.Interaction, current_value: str, **kwargs: dict):
    await interaction.response.send_autocomplete(store.config.topics())


@bot.slash_command(description="Adds an automated answer to the FAQ.",
                   default_member_permissions=nextcord.Permissions(use_slash_commands=True), dm_permission=False,
                   guild_ids=[932268427333210142])
async def faq_add(interaction: nextcord.Interaction,
                  topic: str = SlashOption(description="This defines the topic this FAQ entry will be created in.",
                                           required=True,
                                           autocomplete=True,
                                           autocomplete_callback=check_topic),
                  abbreviation: str = SlashOption(description="This abbreviation will be used to add more message to "
                                                              "the dataset and print FAQ answers for users.",
                                                  min_length=2,
                                                  max_length=15,
                                                  required=True),
                  answer: str = SlashOption(description="The formatted answer that will be send to users.",
                                            min_length=10,
                                            max_length=500,
                                            required=True)):
    abbreviation = abbreviation.lower().strip()
    word_count = len(abbreviation.split(" "))
    if word_count != 1:
        await interaction.send(f"Your abbreviation cannot be longer than one word.", ephemeral=True)
        return

    classifier: AutoFaq = store.classifiers.get(topic)

    if not classifier:
        await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                               ephemeral=True)
        return

    if await classifier.create_answer(answer, abbreviation, interaction):
        await interaction.send(f"Your answer *{answer}* was created. Short: *{abbreviation}*", ephemeral=True)


# @bot.slash_command(description="Adds an automated answer to the FAQ.",
#                    default_member_permissions=nextcord.Permissions(use_slash_commands=True), dm_permission=False)
# async def faq_add(interaction: nextcord.Interaction):
#     await interaction.response.send_modal(FaqAddModal(config.topics(), process_faq_add))


async def process_faq_add(interaction: nextcord.Interaction, modal: FaqAddModal):
    abbreviation = modal.abbreviation.value.lower().strip()
    word_count = len(abbreviation.split(" "))
    if word_count != 1:
        await interaction.send(f"Your abbreviation cannot be longer than one word.", ephemeral=True)
        return

    topic = modal.topic.values[0]  # we made sure that we exactly have to select one option
    classifier: AutoFaq = store.classifiers.get(topic)

    if not classifier:
        await interaction.send(f"This topic does not exist. You have to enable a topic by using `/faq_enable`.",
                               ephemeral=True)
        return

    answer = modal.answer.value
    if await classifier.create_answer(answer, abbreviation, interaction):
        await interaction.send(f"Your answer *{answer}* was created. Short: *{abbreviation}*", ephemeral=True)


@bot.slash_command(description="Reloads the FAQ from its files.",
                   default_member_permissions=nextcord.Permissions(administrator=True), dm_permission=False)
async def faq_reload(interaction: nextcord.Interaction):
    store.load_classifiers()
    await interaction.send("The FAQ has been reloaded.", ephemeral=True)


@bot.slash_command(description="Shows the abbreviations of every FAQ message.",
                   default_member_permissions=nextcord.Permissions(use_slash_commands=True), dm_permission=False)
async def faq(interaction: nextcord.Interaction, topic: str):
    classifier: AutoFaq = store.classifiers.get(topic)

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


@bot.slash_command(description="Prints the chat formatted as nonsense in the console.",
                   default_member_permissions=nextcord.Permissions(administrator=True), dm_permission=False)
async def nonsense(interaction: nextcord.Interaction, message_count: int):
    if not isinstance(interaction.channel, nextcord.TextChannel):
        return

    content = []
    async for message in interaction.channel.history(limit=message_count):
        content.append(message.content)

    print(content)


async def process_add(topic: str, message: nextcord, short: str):
    ref: nextcord.MessageReference = message.reference
    fetched: nextcord.Message = await message.channel.fetch_message(ref.message_id)
    await store.classifiers[topic].add_message_by_short(message, fetched, short)


def get_role_position(user: nextcord.Member) -> int:
    max_pos = 0
    for role in user.roles:
        max_pos = max(max_pos, role.position)
    return max_pos


def has_permission(user: nextcord.Member) -> bool:
    bot_member: nextcord.Member = user.guild.get_member(bot.user.id)
    bot_pos = get_role_position(bot_member)
    user_pos = get_role_position(user)
    return bot_pos <= user_pos


print("starting")
store.load_classifiers()
bot.run(config.token())
