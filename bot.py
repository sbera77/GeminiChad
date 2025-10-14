"""
GeminiChad
Copyright (c) 2024 @notV3NOM

This work is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

See the README.md file for licensing and disclaimer information.
"""

import asyncio
import discord

from discord import app_commands

from components.config import GUILD, DISCORD_BOT_TOKEN
from components.reminder import ReminderManager
from components.commands import setup_commands
from components.events import setup_event_handlers

reminder_manager = ReminderManager()


class GeminiChadBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # self.tree.copy_global_to(guild=GUILD)
        # await self.tree.sync(guild=GUILD)
        await self.tree.sync()
        self.loop.create_task(self.check_reminders())

    async def check_reminders(self):
        await client.wait_until_ready()
        while not client.is_closed():
            await reminder_manager.check_reminders(client)
            await asyncio.sleep(60)


intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.typing = True

client = GeminiChadBot(intents=intents)
setup_commands(client, reminder_manager)
setup_event_handlers(client)

client.run(DISCORD_BOT_TOKEN)
