"""
GeminiChad
Copyright (c) 2024 @notV3NOM

See the README.md file for licensing and disclaimer information.
"""

import csv
import base64
import requests
import google.generativeai as genai

from enum import Enum
from typing import List
from collections.abc import Iterable

from gradio_client import Client
from better_profanity import profanity
from google.generativeai.types import HarmCategory, HarmBlockThreshold, content_types

from .picker import RandomPicker
from .prompts import DEFAULT_NEGATIVE_PROMPT
from .config import (
    SD_XL_BASE_URL,
    SCHNELL_BASE_URL,
    CLOUDFLARE_API_TOKEN,
    GOOGLE_API_KEY,
    DEFAULT_SYSTEM_MESSAGE,
    ADDITIONAL_SYSTEM_MESSAGE,
    LLM,
    logger,
)

genai.configure(api_key=GOOGLE_API_KEY)

model_name = "models/" + LLM

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

calc_model = genai.GenerativeModel(
    model_name=model_name, safety_settings=SAFETY_SETTINGS, tools="code_execution"
)

json_model = genai.GenerativeModel(
    model_name=model_name,
    safety_settings=SAFETY_SETTINGS,
    generation_config={"response_mime_type": "application/json", "temperature": 0},
)


def new_session(
    system_message: str = DEFAULT_SYSTEM_MESSAGE,
    history: Iterable[content_types.StrictContentType] = [],
    tools: content_types.FunctionLibraryType | None = None,
):
    """
    Start a new chat session with a custom system message

    Args:
        system_message: custom system message for this session
        history: resume session from given history
        tools: tools that can be used in this session

    Returns:
        chat_session: New chat session
    """
    model = genai.GenerativeModel(
        model_name=model_name,
        safety_settings=SAFETY_SETTINGS,
        system_instruction=system_message + ADDITIONAL_SYSTEM_MESSAGE,
        tools=tools,
    )
    chat_session = model.start_chat(
        enable_automatic_function_calling=True, history=history
    )
    return chat_session


def temp_session():
    model = genai.GenerativeModel(
        model_name=model_name, safety_settings=SAFETY_SETTINGS
    )
    chat_session = model.start_chat()
    return chat_session


def chat(
    prompt: str, chat_session: genai.ChatSession, file_path_list: List[str] = []
) -> str:
    """
    Chat with the LLM

    Args:
        prompt: input prompt
        chat_session: Chat session
        file_path: path of the input file (Optional)

    Returns:
        image_path: path of the generated image
    """
    inputs = [prompt]

    if len(file_path_list):
        for file_path in file_path_list:
            file = genai.upload_file(path=file_path)
            inputs.append(file)

    try:
        response = chat_session.send_message(inputs)
        return response.text
    except Exception as e:
        logger.exception(e)
        return "Sorry, I could not process your request."


def generate_image_sdxl(prompt: str) -> str:
    """Generates an Image using Stable Diffusion XL 1.0 (Cloudflare)

    Args:
        prompt: image prompt

    Returns:
        image_path: path of the generated image

    """
    data = {"prompt": prompt}
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    response = requests.post(SD_XL_BASE_URL, headers=headers, json=data)

    image_path = "data/image.png"
    with open(image_path, "wb") as f:
        f.write(response.content)

    return image_path


def generate_image_schnell(prompt: str) -> str:
    """Generates an Image using FLUX.1 Schnell (Cloudflare)

    Args:
        prompt: image prompt

    Returns:
        image_path: path of the generated image

    """
    data = {"prompt": prompt}
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    response = requests.post(SCHNELL_BASE_URL, headers=headers, json=data)
    response_json = response.json()
    base64_image = response_json["result"]["image"]
    image_data = base64.b64decode(base64_image)

    image_path = "data/image.png"
    with open(image_path, "wb") as f:
        f.write(image_data)

    return image_path


sd3_client = Client("stabilityai/stable-diffusion-3-medium", verbose=False)


def generate_image_sd3(prompt: str) -> str:
    """Generates an Image using Stable Diffusion 3.0 Medium (Huggingface)

    Args:
        prompt: image prompt

    Returns:
        image_path: path of the generated image

    """
    path, _ = sd3_client.predict(
        prompt=prompt,
        negative_prompt=DEFAULT_NEGATIVE_PROMPT,
        seed=0,
        randomize_seed=True,
        width=1024,
        height=1024,
        guidance_scale=9 if len(prompt) > 100 else 5,
        num_inference_steps=28,
        api_name="/infer",
    )
    return path


# Fallback responses to be used when user input contains profanity
with open("static/fallback_responses.txt", "r") as file:
    fallback_responses = [line.strip() for line in file if line.strip()]

fallback_picker = RandomPicker(fallback_responses)

# Custom censor words to trigger fallback responses
with open("static/censor_words.txt", "r") as file:
    custom_censor_words = [line.strip() for line in file if line.strip()]

profanity.add_censor_words(custom_censor_words)

# Personas
personas = {}

with open("static/personas.csv", "r") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        personas[row["Persona"]] = row["Prompt"]


# Image Generation
class IMAGE_MODELS(Enum):
    SDXL = "sdxl"
    SD3 = "sd3"
    SCHNELL = "schnell"


IMAGE_GENERATORS = {
    IMAGE_MODELS.SDXL: generate_image_sdxl,
    IMAGE_MODELS.SD3: generate_image_sd3,
    IMAGE_MODELS.SCHNELL: generate_image_schnell,
}
