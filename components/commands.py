"""
GeminiChad
Copyright (c) 2024 @notV3NOM

See the README.md file for licensing and disclaimer information.
"""

import os
import json
import asyncio
import discord
import dateparser
import datetime as dt

from typing import Literal
from slugify import slugify
from discord import app_commands

from .tools import web_search
from .prompts import PROMPT_EXPAND_TEMPLATE, FIND_TIME_TEMPLATE, PROMPT_TEMPLATE
from .session import SESSIONS, SYSTEM_MESSAGE, CHAT_SESSION, TOOLS, TOOL_OPTIONS
from .config import BOT_TIMING, DEFAULT_SYSTEM_MESSAGE, BOT_NAME, REMINDER_ICON_URL, LLM
from .llm import (
    chat,
    new_session,
    temp_session,
    json_model,
    IMAGE_GENERATORS,
    IMAGE_MODELS,
    personas,
)

persona_choices = [
    app_commands.Choice(name=persona, value=persona) for persona in personas.keys()
]


class PersonaSelect(discord.ui.Select):
    def __init__(self, current_page=0):
        self.current_page = current_page
        personas_list = list(personas.keys())
        start = current_page * 25
        end = start + 25
        options = [
            discord.SelectOption(label=persona, value=persona)
            for persona in personas_list[start:end]
        ]
        super().__init__(
            placeholder="Choose a persona...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        selected_persona = self.values[0]
        system = personas[selected_persona]
        SESSIONS[interaction.channel.id][SYSTEM_MESSAGE] = system
        tools = SESSIONS[interaction.channel.id][TOOLS]
        SESSIONS[interaction.channel.id][CHAT_SESSION] = new_session(
            system, tools=tools
        )

        embed = discord.Embed(title=BOT_NAME)
        embed.set_thumbnail(url=interaction.client.user.avatar.url)
        embed.add_field(name="Persona", value=selected_persona, inline=False)
        embed.add_field(name="System Message", value=system, inline=False)
        await interaction.response.send_message(embed=embed)


class PaginationView(discord.ui.View):
    def __init__(self, current_page=0):
        super().__init__()
        self.current_page = current_page
        self.add_item(PersonaSelect(current_page))

        total_pages = (len(personas) - 1) // 25

        self.previous_button = discord.ui.Button(
            label="Previous", style=discord.ButtonStyle.primary
        )
        self.previous_button.callback = self.previous_page
        self.previous_button.disabled = self.current_page == 0
        self.add_item(self.previous_button)

        self.next_button = discord.ui.Button(
            label="Next", style=discord.ButtonStyle.primary
        )
        self.next_button.callback = self.next_page
        self.next_button.disabled = self.current_page >= total_pages
        self.add_item(self.next_button)

    async def previous_page(self, interaction: discord.Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(
                view=PaginationView(self.current_page)
            )

    async def next_page(self, interaction: discord.Interaction):
        total_pages = (len(personas) - 1) // 25
        if self.current_page < total_pages:
            self.current_page += 1
            await interaction.response.edit_message(
                view=PaginationView(self.current_page)
            )


class ToolSelect(discord.ui.Select):
    def __init__(self, channel_id):
        options = []
        for tool, tool_fn in TOOL_OPTIONS.items():
            selected = True if tool_fn in SESSIONS[channel_id][TOOLS] else False
            option = discord.SelectOption(label=tool, default=selected)
            options.append(option)
        super().__init__(
            placeholder="Select Tools",
            options=options,
            min_values=0,
            max_values=len(options),
        )

    async def callback(self, interaction: discord.Interaction):
        tools = [TOOL_OPTIONS[value] for value in self.values]
        system = SESSIONS[interaction.channel.id][SYSTEM_MESSAGE]
        SESSIONS[interaction.channel.id][TOOLS] = tools
        SESSIONS[interaction.channel.id][CHAT_SESSION] = new_session(
            system_message=system, tools=tools
        )
        if len(SESSIONS[interaction.channel.id][TOOLS]):
            tools_string = ", ".join(
                [
                    fn.__name__.replace("_", " ").title()
                    for fn in SESSIONS[interaction.channel.id][TOOLS]
                ]
            )
        else:
            tools_string = "None"
        embed = discord.Embed(title=BOT_NAME)
        embed.add_field(name="Tools", value=tools_string, inline=True)
        await interaction.response.send_message(embed=embed)


class ToolSelectView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__()
        self.add_item(ToolSelect(channel_id=channel_id))


def setup_commands(client: discord.Client, reminder_manager):
    @client.tree.command(name="forget", description="Clear chat history")
    async def forget_command(interaction: discord.Interaction):
        system = SESSIONS[interaction.channel.id][SYSTEM_MESSAGE]
        tools = SESSIONS[interaction.channel.id][TOOLS]
        SESSIONS[interaction.channel.id][CHAT_SESSION] = new_session(
            system, tools=tools
        )
        hist_length = len(SESSIONS[interaction.channel.id][CHAT_SESSION].history)
        embed = discord.Embed(title=BOT_NAME)
        embed.add_field(
            name="History ", value=str(hist_length) + " message(s)", inline=False
        )
        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="info", description="Show essential information")
    async def info_command(interaction: discord.Interaction):
        system = SESSIONS[interaction.channel.id][SYSTEM_MESSAGE]
        latency = await asyncio.to_thread(round, client.latency * 1000)
        delta_uptime = dt.datetime.now(dt.timezone.utc) - BOT_TIMING["start_time"]
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        uptime = f"{days} days {hours} hours {minutes} minutes {seconds} seconds"
        hist_length = (
            len(SESSIONS[interaction.channel.id][CHAT_SESSION].history)
            if interaction.channel.id in SESSIONS
            else 0
        )
        if len(SESSIONS[interaction.channel.id][TOOLS]):
            tools = ", ".join(
                [
                    fn.__name__.replace("_", " ").title()
                    for fn in SESSIONS[interaction.channel.id][TOOLS]
                ]
            )
        else:
            tools = "None"
        embed = discord.Embed(title=BOT_NAME)
        embed.set_thumbnail(url=client.user.avatar.url)
        embed.add_field(name="Model", value=LLM.replace("-", " "), inline=True)
        embed.add_field(
            name="History ", value=str(hist_length) + " message(s)", inline=True
        )
        embed.add_field(name="Latency", value=str(latency) + " ms", inline=True)
        embed.add_field(name="Tools", value=tools, inline=False)
        embed.add_field(name="Uptime ", value=uptime, inline=False)
        embed.add_field(name="System Message", value=system, inline=False)
        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="system", description="Change the system message")
    @app_commands.describe(message="Enter `default` for default system message.")
    @app_commands.describe(forget="Clear chat history")
    async def settings_command(
        interaction: discord.Interaction, message: str, forget: bool = True
    ):
        system = DEFAULT_SYSTEM_MESSAGE if message == "default" else message
        SESSIONS[interaction.channel.id][SYSTEM_MESSAGE] = system
        tools = SESSIONS[interaction.channel.id][TOOLS]
        if forget:
            SESSIONS[interaction.channel.id][CHAT_SESSION] = new_session(
                system, tools=tools
            )
        else:
            previous_history = SESSIONS[interaction.channel.id][CHAT_SESSION].history
            SESSIONS[interaction.channel.id][CHAT_SESSION] = new_session(
                system, previous_history, tools
            )
        embed = discord.Embed(title=BOT_NAME)
        embed.set_thumbnail(url=client.user.avatar.url)
        embed.add_field(name="System Message", value=system, inline=False)
        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="persona", description="Switch the persona")
    async def persona_command(interaction: discord.Interaction):
        await interaction.response.send_message(view=PaginationView())

    @client.tree.command(name="tools", description="Adjust available tools")
    async def tools_command(interaction: discord.Interaction):
        view = ToolSelectView(channel_id=interaction.channel.id)
        await interaction.response.send_message(view=view)

    @client.tree.command(name="reminder", description="Set a reminder")
    @app_commands.describe(message="Reminder message with relative time")
    async def reminder_command(interaction: discord.Interaction, message: str):
        try:
            await interaction.response.defer()
            response = await asyncio.to_thread(
                json_model.generate_content, FIND_TIME_TEMPLATE + message
            )
            time_json = json.loads(response.text.strip())
            reminder_time = dateparser.parse(time_json["time"])
            if reminder_time is None:
                raise ValueError("Failed to parse time")

            reminder_manager.add_reminder(
                interaction.user.id,
                message,
                reminder_time.isoformat(),
                interaction.channel.id,
            )
            embed = discord.Embed(
                title=time_json["title"],
                description=f"<t:{int(reminder_time.timestamp())}:R>",
            )
            embed.set_thumbnail(url=REMINDER_ICON_URL)
            await interaction.followup.send(embed=embed)
        except ValueError as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @client.tree.command(name="web", description="Search the web to answer a question")
    @app_commands.describe(question="The question to be answered")
    async def web_command(interaction: discord.Interaction, question: str):
        try:
            await interaction.response.defer()
            search_results = web_search(question)
            answer = await asyncio.to_thread(
                chat,
                PROMPT_TEMPLATE.format(
                    context=search_results, question=question
                ),
                temp_session(),
            )
            embed = discord.Embed(title=question, description=answer)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)

    @client.tree.command(name="art", description="Generate Image")
    @app_commands.describe(prompt="Prompt to generate the Image")
    @app_commands.describe(expand_prompt="Improve prompt automatically")
    async def art_command(
        interaction: discord.Interaction,
        prompt: str,
        model: IMAGE_MODELS = IMAGE_MODELS.SCHNELL,
        expand_prompt: Literal["true", "false"] = "false",
    ):
        try:
            await interaction.response.defer()
            if expand_prompt == "true":
                response = await asyncio.to_thread(
                    chat, PROMPT_EXPAND_TEMPLATE.format(prompt=prompt), temp_session()
                )
                prompt = response.strip()
            filename = slugify(prompt, max_length=100)
            generated_image_path = await asyncio.to_thread(
                IMAGE_GENERATORS[model], prompt
            )
            extension = os.path.splitext(generated_image_path)[1]
            image = discord.File(generated_image_path, filename=filename + extension)
            ix = max(prompt.find("", 225), 225)
            embed_title = prompt if len(prompt) < 250 else prompt[:ix] + " ..."
            embed = discord.Embed(title=embed_title)
            embed.set_image(url="attachment://" + filename + extension)
            await interaction.followup.send(file=image, embed=embed)

            if os.path.exists(generated_image_path):
                os.remove(generated_image_path)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
