"""
GeminiChad
Copyright (c) 2024 @notV3NOM

See the README.md file for licensing and disclaimer information.
"""

import os
import json
import discord
import datetime as dt

from .config import logger
from .llm import chat, temp_session
from .prompts import PING_TEMPLATE, REMINDER_TEMPLATE


class ReminderManager:
    """
    Class to manage reminders, including adding, saving, loading, and checking reminders.
    """

    def __init__(self, filename="data/reminders.json"):
        """
        Initialize the ReminderManager with a data file path.

        Args:
            filename (str): The path to the file where reminders are stored. Defaults to 'data/reminders.json'.
        """
        self.filename = filename
        self.load_reminders()

    def load_reminders(self):
        """
        Load reminders from the data file.

        If the file does not exist, initialize an empty list of reminders.
        """
        if os.path.exists(self.filename):
            with open(self.filename, "r") as file:
                self.reminders = json.load(file)
        else:
            self.reminders = []

    def save_reminders(self):
        """
        Save the current list of reminders to the data file.
        """
        with open(self.filename, "w") as file:
            json.dump(self.reminders, file, indent=4)

    def add_reminder(self, user_id, message, time_str, channel_id):
        """
        Add a new reminder to the list and save it to the data file.

        Args:
            user_id (str): The ID of the user to be reminded.
            message (str): The reminder message.
            time_str (str): The time when the reminder should be triggered.
            channel_id (int): The ID of the channel where the reminder should be sent.
        """
        reminder_time = dt.datetime.strptime(
            time_str.split(".")[0], "%Y-%m-%dT%H:%M:%S"
        )
        self.reminders.append(
            {
                "user_id": user_id,
                "message": message,
                "time": reminder_time.isoformat(),
                "channel_id": channel_id,
            }
        )
        self.save_reminders()

    async def check_reminders(self, client):
        """
        Check for due reminders and send them to the appropriate channel.

        Updates the reminder list and saves it if required.

        Args:
            client (object): The client used to send reminder
        """
        now_utc = dt.datetime.now(dt.timezone.utc)
        due_reminders = [
            reminder
            for reminder in self.reminders
            if dt.datetime.fromisoformat(reminder["time"]).astimezone(dt.timezone.utc)
            <= now_utc
        ]
        self.reminders = [
            reminder
            for reminder in self.reminders
            if dt.datetime.fromisoformat(reminder["time"]).astimezone(dt.timezone.utc)
            > now_utc
        ]
        self.save_reminders()

        for reminder in due_reminders:
            try:
                channel = client.get_channel(reminder["channel_id"])
                ping_msg = PING_TEMPLATE.format(id=reminder["user_id"])
                response = chat(
                    REMINDER_TEMPLATE.format(reminder=reminder["message"]),
                    temp_session(),
                )
                embed = discord.Embed(title="Reminder !", description=response.strip())
                await channel.send(ping_msg, embed=embed)
            except Exception as e:
                logger.exception(f"Reminder Failed {e}")
