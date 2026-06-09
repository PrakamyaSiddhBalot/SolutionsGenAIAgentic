"""
ResearchBot: Week 2 Project 
======================================
This file currently makes a basic single-turn call to OpenRouter.
The job is to evolve it into a full research agent with:
  - Web search and web fetch tools (using OpenAI SDK tool calling)
  - An agent loop that iterates until the model stops requesting tools
  - A Textual TUI with a chat panel and a tool activity log
  - Keyboard shortcuts: Ctrl+L (clear display), Ctrl+K (clear history), Ctrl+Q (quit),
    and at least one more of your choice

Start by getting this file working, then add tools, then add the TUI.
Don't try to build everything at once.
"""

import os
import requests
import trafilatura
import json
import asyncio
import httpx

from mcp import ClientSession
from mcp.client.streamable_http import (
    streamable_http_client
)
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "deepseek/deepseek-v4-flash"

SERPER_API_KEY = os.environ["SERPER_API_KEY"]

MAX_CHARS = 8000

TOOL_LOGGER = None

MCP_SERVER_URL = (
    "https://api.alphaxiv.org/mcp/v1"
)

AUTH_FILE = (
    r"C:\Users\chefs\.alphaxiv\auth.json"
)


def web_search(query: str, num_results: int = 5) -> list[dict]:

    response = requests.post(
        "https://google.serper.dev/search",
        headers={
            "X-API-KEY": SERPER_API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "q": query,
            "num": num_results
        },
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    results = []

    for item in data.get("organic", []):

        results.append(
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
            }
        )

    return results


def web_fetch(url: str) -> str:

    headers = {
        "User-Agent":
        "Mozilla/5.0 (compatible; ResearchBot/1.0)"
    }

    response = requests.get(
        url,
        headers=headers,
        allow_redirects=True,
        timeout=10
    )

    response.raise_for_status()

    html = response.text

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True
    )

    if text is None:
        return ""

    if len(text) > MAX_CHARS:

        text = (
            text[:MAX_CHARS]
            + "\n\n[...truncated]"
        )

    return text

async def get_alphaxiv_tools():

    with open(
        AUTH_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        auth = json.load(f)

    token = auth["access_token"]

    http_client = httpx.AsyncClient(
        headers={
            "Authorization":
            f"Bearer {token}"
        }
    )

    async with streamable_http_client(
        MCP_SERVER_URL,
        http_client=http_client
    ) as (read, write, _):

        async with ClientSession(
            read,
            write
        ) as session:

            await session.initialize()

            return await session.list_tools()


def convert_mcp_tools(
    tools_result
):

    openai_tools = []

    for tool in tools_result.tools:

        openai_tools.append(
            {
                "type": "function",
                "function": {
                    "name":
                    tool.name,

                    "description":
                    tool.description,

                    "parameters":
                    tool.inputSchema
                }
            }
        )

    return openai_tools
MCP_TOOL_NAMES = set()
MCP_TOOLS = []
LOCAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information. "
                "Use this when the user asks about recent events, "
                "specific facts, people, companies, places, or anything "
                "that requires external information."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "The search query to send to the search engine."
                        )
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "web_fetch",
            "description": (
                "Fetch and read the contents of a webpage. "
                "Use this after web_search when you need to inspect "
                "a specific page in detail."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": (
                            "The full URL of the webpage to fetch."
                        )
                    }
                },
                "required": ["url"]
            }
        }
    }
]


TOOL_REGISTRY = {
    "web_search": web_search,
    "web_fetch": web_fetch
}
async def call_mcp_tool(
    tool_name: str,
    arguments: dict
):

    with open(
        AUTH_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        auth = json.load(f)

    token = auth["access_token"]

    http_client = httpx.AsyncClient(
        headers={
            "Authorization":
            f"Bearer {token}"
        }
    )

    async with streamable_http_client(
        MCP_SERVER_URL,
        http_client=http_client
    ) as (read, write, _):

        async with ClientSession(
            read,
            write
        ) as session:

            await session.initialize()

            result = await session.call_tool(
                tool_name,
                arguments
            )

            if not result.content:

                return ""

            return result.content[0].text
def dispatch(tool_call) -> str:

    name = tool_call.function.name

    arguments = json.loads(
        tool_call.function.arguments
    )

    if name in MCP_TOOL_NAMES:

        try:

            return asyncio.run(
                call_mcp_tool(
                    name,
                    arguments
                )
            )

        except Exception as e:

            return json.dumps(
                {
                    "error": str(e)
                }
            )

    tool_fn = TOOL_REGISTRY.get(name)

    if tool_fn is None:

        return json.dumps(
            {
                "error":
                f"Unknown tool: {name}"
            }
        )

    try:

        result = tool_fn(
            **arguments
        )

        return json.dumps(
            result
        )

    except Exception as e:

        return json.dumps(
            {
                "error":
                str(e)
            }
        )

MAX_ITERATIONS = 10

def run_agent(user_message: str) -> str:

    messages = [
        {
            "role": "system",
            "content": (
                "You are a research assistant."
                "Use tools only when necessary."
                "Prefer discover_papers first when the user asks for research papers."
                "Do not repeatedly call the same tool unless additional information is required."
                "After gathering enough evidence, stop using tools and provide a concise answer."
                "Avoid excessive tool use."
            )
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    for _ in range(MAX_ITERATIONS):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=LOCAL_TOOLS + MCP_TOOLS,
        )

        message = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":

            messages.append(message)

            for tool_call in message.tool_calls:

                if TOOL_LOGGER:
                    TOOL_LOGGER(
                        f"[Tool] {tool_call.function.name}"
                    )

                tool_result = dispatch(tool_call)

                if TOOL_LOGGER:
                    TOOL_LOGGER(
                        f"[Tool Result]"
                    )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    }
                )

            continue

        if finish_reason == "stop":

            if message.content is None:
                return "[Model returned no text]"

            return message.content

    return (
        f"[Agent stopped after "
        f"{MAX_ITERATIONS} iterations]"
    )





def call_model(prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


if __name__ == "__main__":

    tools_result = asyncio.run(
        get_alphaxiv_tools()
    )

    MCP_TOOLS = convert_mcp_tools(
        tools_result
    )

    MCP_TOOL_NAMES = {
        tool["function"]["name"]
        for tool in MCP_TOOLS
    }

    print(
        f"Loaded {len(MCP_TOOLS)} MCP tools."
    )

    print(
        run_agent(
            "Find recent papers on LLM agents."
        )
    )
