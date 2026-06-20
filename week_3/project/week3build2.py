"""
Build 2: Agent + REPLAgent
===========================
Agent = brain (loop, tools, sessions). REPLAgent = terminal UI.

Before running:
  mkdir -p notes

Tasks:
  1. Agent — chat(), run_once(), _run_loop(), dispatch(), _emit(), session I/O
  2. REPLAgent(Agent) — run() interactive loop
  3. resolve_path, read_file, write_file, list_files, edit_file
  4. main() — one-shot: python build2_agent_class.py "hello"

TUIAgent comes in the project (tui.py). No Textual imports here.
"""

import os
import sys
import json
import glob as glob_module
from openai import OpenAI
from dotenv import load_dotenv
from files import (
    resolve_path,
    read_file,
    write_file,
    edit_file,
    list_files,
)
from week3build1 import (
    create_session,
    save_session,
    load_session,
)
from papers import (
    paper_search,
    read_paper,
)

load_dotenv()

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_ITERATIONS = 10
MAX_READ_CHARS = 12_000

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)
MODEL = "deepseek/deepseek-v4-flash"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description":
            "Read a file with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "start_line": {
                        "type": "integer"
                    },
                    "read_lines": {
                        "type": "integer"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description":
            "Create or overwrite a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    }
                },
                "required": [
                    "path",
                    "content"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description":
            "List files in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "pattern": {
                        "type": "string"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description":
            "Append, replace or delete lines in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string"
                    },
                    "operation": {
                        "type": "string"
                    },
                    "start_line": {
                        "type": "integer"
                    },
                    "end_line": {
                        "type": "integer"
                    },
                    "content": {
                        "type": "string"
                    }
                },
                "required": [
                    "path",
                    "operation",
                    "start_line"
                ]
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "paper_search",
            "description":
                "Search research papers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "limit": {
                        "type": "integer"
                    }
                },
                "required": ["query"]
            }
        }
    },
        {
        "type": "function",
        "function": {
            "name": "read_paper",
            "description":
                "Read a paper by arXiv ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "arxiv_id": {
                        "type": "string"
                    }
                },
                "required": [
                    "arxiv_id"
                ]
            }
        }
    }
]


class Agent:
    """Core agent: loop, tools, sessions. No UI."""

    def __init__(
        self,
        workspace: str = ".",
        session_id: str | None = None
    ):

        self.workspace = os.path.abspath(
            workspace
        )

        if session_id:

            session = load_session(
                session_id
            )

            self.session_id = (
                session_id
            )

            self.messages = (
                session["messages"]
            )

        else:

            self.session_id = (
                create_session()
            )

            self.messages = [
                {
                    "role": "system",
                    "content":
                    build_system_prompt()
                }
            ]

    def chat(
        self,
        user_message: str
    ) -> str:

        self.messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        answer = self._run_loop()

        save_session(
            self.session_id,
            self.messages
        )

        return answer

    def run_once(self, prompt: str) -> str:
        return self.chat(prompt)

    def _run_loop(self) -> str:

        for _ in range(MAX_ITERATIONS):

            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
            )

            message = response.choices[0].message
            finish_reason = response.choices[0].finish_reason

            if finish_reason == "tool_calls":

                self.messages.append(
                    {
                        "role": message.role,
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ]
                    }
                )

                for tool_call in message.tool_calls:

                    self._emit(
                        "tool_call",
                        name=tool_call.function.name
                    )

                    tool_result = self.dispatch(
                        tool_call
                    )

                    self._emit(
                        "tool_result",
                        result=tool_result
                    )

                    self.messages.append(
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

                self.messages.append(
                    {
                        "role": "assistant",
                        "content": message.content
                    }
                )

                return message.content

        return (
            f"[Agent stopped after "
            f"{MAX_ITERATIONS} iterations]"
        )

    def dispatch(self, tool_call) -> str:

        name = tool_call.function.name

        arguments = json.loads(
            tool_call.function.arguments
        )

        tool_registry = {
            "read_file": read_file,
            "write_file": write_file,
            "list_files": list_files,
            "edit_file": edit_file,
            "paper_search": paper_search,
            "read_paper": read_paper,
        }

        tool_fn = tool_registry.get(name)

        if tool_fn is None:

            return json.dumps(
                {
                    "error":
                    f"Unknown tool: {name}"
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

    def _emit(self, event: str, **data) -> None:
        """Override in REPLAgent/TUIAgent for tool logging."""
        pass


class REPLAgent(Agent):
    """Terminal REPL + one-shot CLI."""

    def run(self) -> None:
        print(f"Research Desk [{self.session_id}] — /quit to exit")
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not user_input or user_input in ("/quit", "/exit"):
                break
            print(self.chat(user_input))
            print()

    def _emit(self, event: str, **data) -> None:
        if event == "tool_call":
            print(f"  [tool] {data.get('name')}", file=sys.stderr)


def build_system_prompt() -> str:

    base_prompt = """
        You are Research Desk.

        Use tools when necessary.

        After receiving enough information from tools,
        stop calling tools and answer the user.

        Do not repeatedly call the same tool for the
        same information.

        Do not explore directories repeatedly.

        When a tool returns the requested information,
        provide the answer immediately.
        """
    

    for path in (
        "AGENTS.md",
        ".agent/AGENTS.md"
    ):

        if os.path.isfile(path):

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                rules = f.read()

            return (
                base_prompt
                + "\n\n"
                + rules
            )

    return base_prompt


def main():
    agent = REPLAgent()
    if len(sys.argv) > 1:
        print(agent.run_once(" ".join(sys.argv[1:])))
        return
    agent.run()


if __name__ == "__main__":
    main()
