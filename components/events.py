"""
GeminiChad
Copyright (c) 2024 @notV3NOM

See the README.md file for licensing and disclaimer information.
"""

import os
import re
import uuid
import discord
import asyncio
import requests
import datetime as dt

from .session import SESSIONS, CHAT_SESSION
from .llm import chat, profanity, fallback_picker
from .config import BOT_TIMING, BOT_NAME, EXTENSION_MAPPING, logger


def extract_artifacts(llm_reponse: str):
    pattern = r"```(\S+)\n(.*?)\n```"
    matches = re.findall(pattern, llm_reponse, re.DOTALL)
    artifacts = []
    artifact_path_list = []
    artifacts_count = 0

    if matches:
        logger.info(f"Extracting {len(matches)} Artifacts")
        for language, content in matches:
            extension = (
                EXTENSION_MAPPING[language.lower()]
                if language.lower() in EXTENSION_MAPPING
                else "txt"
            )
            temp_file_path = temp_file_path = (
                f"data/temp-{str(uuid.uuid4())}.{extension}"
            )
            with open(temp_file_path, "wb") as f:
                f.write(content.strip().encode())
            artifacts.append(
                discord.File(
                    temp_file_path, filename=f"temp-{str(uuid.uuid4())}.{extension}"
                )
            )
            artifact_path_list.append(temp_file_path)
            llm_reponse = llm_reponse.replace(
                f"```{language}\n{content}\n```", f"<<artifact_{artifacts_count}>>"
            )
            artifacts_count += 1

    cleaned_text = re.sub(r"\n\s*\n", "\n\n", llm_reponse.strip())
    cleaned_text = re.sub(r" +", " ", cleaned_text)

    return artifacts, artifact_path_list, cleaned_text


def extract_images(llm_response: str):
    image_pattern = r"<IMAGE>(.*?)<\/IMAGE>"
    image_matches = re.findall(image_pattern, llm_response)
    embeds = []
    files = []
    images_count = 0

    if image_matches:
        logger.info(f"Extracting {len(image_matches)} Images")
        for image_match in image_matches:
            generated_image_path = image_match.split("||")[0]
            image_prompt = image_match.split("||")[1]
            filename = os.path.basename(generated_image_path)
            image = discord.File(generated_image_path, filename=filename)
            embed = discord.Embed(title=image_prompt[:256])
            embed.set_image(url="attachment://" + filename)
            embeds.append(embed)
            files.append(image)
            llm_response = llm_response.replace(
                f"<IMAGE>{image_match}</IMAGE>", f"<<image_{images_count}>>"
            )
            images_count += 1

    return files, embeds, llm_response


async def send_message(message, llm_response: str):
    image_files, image_embeds, llm_response = extract_images(llm_response)
    artifacts, artifact_path_list, llm_response = extract_artifacts(llm_response)
    final_chunks = []

    chunks = re.split(r"(<<artifact_\d+>>|<<image_\d+>>)", llm_response)

    for chunk in chunks:
        if chunk.startswith("<<artifact") or chunk.startswith("<<image"):
            final_chunks.append(chunk)
        else:
            while chunk:
                if len(chunk) > 2000:
                    split_index = chunk.rfind("\n", 0, 2000)
                    if split_index == -1:
                        split_index = 2000
                    final_chunks.append(chunk[:split_index])
                    chunk = chunk[split_index:]
                else:
                    final_chunks.append(chunk)
                    chunk = ""

    for chunk in final_chunks:
        if chunk.startswith("<<artifact_"):
            index = int(chunk.split("_")[1].replace(">>", ""))
            file = artifacts[index]
            await message.channel.send(" ", file=file)
        elif chunk.startswith("<<image_"):
            index = int(chunk.split("_")[1].replace(">>", ""))
            file = image_files[index]
            embed = image_embeds[index]
            await message.channel.send(" ", file=file, embed=embed)
        else:
            if chunk.strip():
                await message.channel.send(chunk)

    for temp_file_path in artifact_path_list:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def setup_event_handlers(client: discord.Client):
    @client.event
    async def on_ready():
        BOT_TIMING["start_time"] = dt.datetime.now(dt.timezone.utc)
        logger.info(f"{BOT_NAME} is ready")

    @client.event
    async def on_message(message: discord.Message):
        if message.author == client.user or message.author.bot:
            return

        is_reply = message.reference
        is_reply_to_bot = (
            message.reference and message.reference.resolved.author == client.user
        )
        mentions_bot_name = (
            BOT_NAME.lower() in message.content.lower()
            or client.user.mention in message.content
        )

        if not is_reply_to_bot and not mentions_bot_name:
            return

        prompt = message.content

        if is_reply and not is_reply_to_bot:
            prompt = message.reference.resolved.content + prompt

        if mentions_bot_name:
            prompt = prompt.replace(BOT_NAME, "")
            prompt = prompt.replace(BOT_NAME.lower(), "")
            prompt = prompt.replace(client.user.mention, "").strip()

        if profanity.contains_profanity(prompt):
            async with message.channel.typing():
                llm_response = fallback_picker.pick()
                await message.channel.send(llm_response)
            return

        file_path_list = []

        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type.startswith(
                    "image/"
                ) or attachment.filename.endswith(
                    (".txt", ".py", ".js", ".tsx", ".pdf")
                ):
                    resp = requests.get(attachment.url)
                    if resp.status_code == 200:
                        file_data = resp.content
                        temp_file_path = (
                            f"data/temp-{str(uuid.uuid4())}-{attachment.filename}"
                        )

                        with open(temp_file_path, "wb") as f:
                            f.write(file_data)

                        file_path_list.append(temp_file_path)

        async with message.channel.typing():
            response = await asyncio.to_thread(
                chat, prompt, SESSIONS[message.channel.id][CHAT_SESSION], file_path_list
            )
            llm_response = response.strip()
            await send_message(message, llm_response)

        for temp_file_path in file_path_list:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
