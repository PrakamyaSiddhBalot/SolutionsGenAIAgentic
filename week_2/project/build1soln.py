import os
import re
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "openrouter/free"
# I used the openrouter/free model because the deepseek free model is no longer available. Instead, we can use "deepseek/deepseek-v4-flash".

SYSTEM_PROMPT = """You are a helpful file assistant with access to the following tools:

- read_file(path: str): reads a file from disk and returns its content
- write_file(path: str, content: str): writes content to a file on disk

When you need to use a tool, emit EXACTLY this format:

<tool_call>
{"name": "TOOL_NAME", "arguments": {"arg1": "value1"}}
</tool_call>

After you receive a <tool_response> block, use the information inside it to answer the user's request.

Do not call the same tool repeatedly unless necessary.

If the user asks you to summarize, explain, rewrite, or analyze a file, first call read_file, then perform the task yourself after receiving the file contents.
"""

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def read_file(path: str) -> dict:
    try:
        with open(path, "r") as f:
            content = f.read()

        return {
            "content": content,
            "path": path
        }

    except Exception as e:
        return {
            "error": str(e)
        }


def write_file(path: str, content: str) -> dict:
    try:
        with open(path, "w") as f:
            bytes_written = f.write(content)

        return {
            "success": True,
            "path": path,
            "bytes_written": bytes_written
        }

    except Exception as e:
        return {
            "error": str(e)
        }


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def parse_tool_call(response_text: str) -> dict | None:

    if response_text is None:
        return None

    match = re.search(
        r"<tool_call>\s*(.*?)\s*(?:</tool_call>|$)",
        response_text,
        re.DOTALL
    )

    if not match:
        return None

    try:
        return json.loads(match.group(1).strip())

    except json.JSONDecodeError:
        return None


def strip_tool_call(response_text: str) -> str:

    if response_text is None:
        return ""

    return re.sub(
        r"<tool_call>.*?(</tool_call>|$)",
        "",
        response_text,
        flags=re.DOTALL
    ).strip()


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

TOOL_REGISTRY = {
    "read_file": read_file,
    "write_file": write_file,
}


def dispatch(name: str, arguments: dict) -> str:

    tool_fn = TOOL_REGISTRY.get(name)

    if tool_fn is None:
        return json.dumps(
            {
                "error": f"Unknown tool: {name}"
            }
        )

    try:
        result = tool_fn(**arguments)
        return json.dumps(result)

    except Exception as e:
        return json.dumps(
            {
                "error": str(e)
            }
        )


# ---------------------------------------------------------------------------
# Agent Loop
# ---------------------------------------------------------------------------

MAX_ITERATIONS = 6


def run_agent(user_message: str) -> str:

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for iteration in range(MAX_ITERATIONS):

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        response_text = response.choices[0].message.content

        if response_text is None:
            print("Model returned None")
            return "[Model returned no text]"

        print(f"\nITERATION {iteration + 1}")
        print("RAW MODEL OUTPUT:")
        print(response_text)
        print()

        tool_call = parse_tool_call(response_text)

        if tool_call is None:
            return strip_tool_call(response_text)

        tool_result = dispatch(
            tool_call["name"],
            tool_call["arguments"]
        )

        print(
            f"[Tool] {tool_call['name']} {tool_call['arguments']}"
        )

        print("TOOL RESULT:")
        print(tool_result)
        print()

        tool_response = (
            "<tool_response>\n"
            f"{tool_result}\n"
            "</tool_response>"
        )

        messages.append(
            {
                "role": "assistant",
                "content": response_text
            }
        )

        messages.append(
            {
                "role": "user",
                "content": tool_response
            }
        )

    return f"[Agent stopped after {MAX_ITERATIONS} iterations]"


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    with open("sample.txt", "w") as f:
        f.write(
            "IIT Delhi was established in 1961. "
            "It is one of the premier engineering institutions in India.\n"
        )
        f.write(
            "The campus spans 325 acres in Hauz Khas, New Delhi.\n"
        )

    test_queries = [
        "Read sample.txt and summarise what it says.",
        "Read sample.txt and write a one-sentence version of its content to summary.txt.",
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print(f"{'=' * 60}")

        result = run_agent(query)

        print(f"Answer: {result}")
