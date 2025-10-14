"""
GeminiChad
Copyright (c) 2024 @notV3NOM

See the README.md file for licensing and disclaimer information.
"""

import sympy as sp

from typing import List
from datetime import datetime
from gradio_client import Client

from .config import logger
from .prompts import CALC_TEMPLATE
from .llm import calc_model, IMAGE_MODELS, IMAGE_GENERATORS

websearch_client = Client("victor/websearch")

def web_search(query: str) -> List[str]:
    """
    Perform a web search and get the search results.
    With this tool, you have full access to the internet.
    Always utilize this tool to find accurate and up-to-date information, such as current events, prices, or any other missing details.
    Do not instruct the user to perform the search themselves.
    Instead, conduct the web search and provide the relevant information directly to the user.
    Make sure to leverage this capability whenever additional or current information is needed to answer the user's query.

    Args:
        query: The search query string.

    Returns:
        A List containing the search results.
    """
    logger.info(f"SEARCH {query}")
    search_results = websearch_client.predict(
        query=query,
        search_type="search",
        num_results=4,
        api_name="/search_web"
    )
    return search_results


def code_execution(code: str) -> str:
    """
    Execute python code safely.
    Always use this tool to execute any python code asked by the user.
    Do not predict the results of any python code, instead use this tool and actually run the program to the results.
    You can also you this tool to execute any python code you need.

    Args:
        expression (str):  Code to be executed

    Returns:
        result (str): Result of the python code
    """
    logger.info(f"CODE EXECUTION {code}")
    result = calc_model.generate_content(CALC_TEMPLATE.format(problem=code))
    return result.text


def calculator(expression: str) -> str:
    """
    Calculate the result of an expression safely using sympy.
    Use this tool to perform any calculation required.

    Args:
        expression: The expression to be calculated

    Returns:
        The expression and its result

    """
    logger.info(f"CALCULATION {expression}")
    try:
        expr = sp.sympify(expression)
        result = expr.evalf()
        return f"{expression} = {result}"
    except (sp.SympifyError, ValueError) as e:
        logger.error(e)
        return "Calculation failed"


def image_generation(prompt: str) -> str:
    """
    Generate an Image and return the path of the generated image.
    Use this tool to draw any kind of image like poster, album art or book covers etc.
    With this tool, you have the capability to generate and display images to the user.
    When you use this tool, it is mandatory to respond by displaying the exact result directly to the user.
    The user will not be able to see the image unless you respond with the exact result directly.

    Args:
        prompt: image prompt

    Returns:
        image_path: path of the generated image enclosed in image tags

    """
    logger.info(f"IMAGE GENERATION {prompt}")
    return (
        "<IMAGE>"
        + IMAGE_GENERATORS[IMAGE_MODELS.SCHNELL](prompt)
        + "||"
        + prompt
        + "</IMAGE>"
    )


def clock() -> str:
    """
    Returns the current date and time as a string in 12-hour format with AM/PM.
    Use this tool to get the current date/time.

    Returns:
        str: A string representing the current date and time in 12-hour format with AM/PM.
    """
    logger.info(f"CLOCK")
    return datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
