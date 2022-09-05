import os

import nextcord
from nextcord.ext import commands

import core.classifier
from core.classifier import Store
from core.files import Config

config: Config = Config()

intents = nextcord.Intents.default()
intents.message_content = True

activity = nextcord.Activity(type=nextcord.ActivityType.playing, name="Support Buddy (BETA)")
bot = commands.Bot(intents=intents, activity=activity)
store = core.classifier.setup(Store(bot))

# load extensions
for fn in os.listdir("./cogs"):
    if fn.endswith(".py"):
        bot.load_extension(f"cogs.{fn[:-3]}")

print("starting")
store.load_classifiers()
bot.run(config.token())
