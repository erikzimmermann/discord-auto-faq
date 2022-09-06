import os

import nextcord
from nextcord.ext import commands

import core.classifier
import core.log as log
from core.classifier import Store
from core.files import Config

config: Config = Config()

intents = nextcord.Intents.default()
intents.message_content = True

activity = nextcord.Activity(type=config.activity_type(), name=config.activity())
bot = commands.Bot(intents=intents, activity=activity)
store = core.classifier.setup(Store(bot))


def load_extensions():
    for fn in os.listdir("./cogs"):
        if fn.endswith(".py"):
            log.info(f"Loading extension: {fn}")
            bot.load_extension(f"cogs.{fn[:-3]}")


def start():
    log.load_logging_handlers()
    load_extensions()

    print("Bot is ready! - @Pterodactyl")
    log.info("Starting bot...")
    store.load_classifiers()
    bot.run(config.token())


start()
