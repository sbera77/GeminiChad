"""
GeminiChad
Copyright (c) 2024 @notV3NOM

See the README.md file for licensing and disclaimer information.
"""

from collections import defaultdict

from .llm import new_session
from .config import DEFAULT_SYSTEM_MESSAGE
from .tools import web_search, code_execution, calculator, image_generation, clock

TOOLS = "TOOLS"
CHAT_SESSION = "CHAT_SESSION"
SYSTEM_MESSAGE = "SYSTEM_MESSAGE"

TOOL_OPTIONS = {
    "Clock": clock,
    "Calculate": calculator,
    "Web Search": web_search,
    "Image Generation": image_generation,
    "Code Execution": code_execution,
}

default_tools = [TOOL_OPTIONS[tool] for tool in TOOL_OPTIONS]


def session_default_factory():
    return {
        SYSTEM_MESSAGE: DEFAULT_SYSTEM_MESSAGE,
        CHAT_SESSION: new_session(tools=default_tools),
        TOOLS: default_tools,
    }


SESSIONS = defaultdict(session_default_factory)
