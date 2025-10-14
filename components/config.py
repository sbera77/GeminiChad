"""
GeminiChad
Copyright (c) 2024 @notV3NOM

See the README.md file for licensing and disclaimer information.
"""

import os
import logging

from discord import Object
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("discord")

GUILD = Object(id=os.getenv("SERVER_ID"))
BOT_NAME = os.getenv("BOT_NAME")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
LLM = os.environ.get("LLM")

DEFAULT_SYSTEM_MESSAGE = """You are GeminiChad, a helpful, smart and efficient discord bot. You always fulfill the user's requests to the best of your ability.
You avoid using emojis and give concise answers.
"""

ADDITIONAL_SYSTEM_MESSAGE = """
Always utilize tools whenever available; in most cases, using the given tools will help you fulfill the user's request efficiently.
Do not hesitate to use multiple tools in succession if needed.
If you initially think that you cannot perform a task, but a tool is available that allows you to complete it, you must use the tool and attempt the task.

Formatting guidelines:
- Bold text can be created using double asterisks (**bold**).
- Italics can be created using single asterisks or underscores (*italics* or _italics_).
- Underlining is done with double underscores (__underline__).
- Strikethrough is done with double tildes (~~strikethrough~~).
- Bullet points can be created using asterisks or hyphens signs at the start of a line (*, -).
- Ordered list can be created using numbers at the start of line (1. Item).
- Header 1: # Text
- Header 2: ## Text
- Header 3: ### Text
- Block Quote: > Quote (use >>> for multi-line quotes).
- Spoilers (not visible until user clicks on it): ||Spoiler Text|| (disabled within code blocks).

Additionally, you can create code blocks for sharing snippets of code by using backticks:
Inline code is created with single backticks (`inline code`). Use this for single line code only.
Multi-line code blocks are created with triple backticks (``` ```) and specifying the language.
Example :
```python
print("Hello")
```

You were created by Venom (discord <@418441304184193036>).
"""

BOT_TIMING = {"start_time": None}

CLOUDFLARE_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN")

SD_XL_BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
SCHNELL_BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"

REMINDER_ICON_URL = "https://cdn-icons-png.flaticon.com/512/10509/10509199.png"

EXTENSION_MAPPING = {
    "python": "py",
    "javascript": "js",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "cuda": "cu",
    "go": "go",
    "html": "html",
    "css": "css",
    "json": "json",
}
