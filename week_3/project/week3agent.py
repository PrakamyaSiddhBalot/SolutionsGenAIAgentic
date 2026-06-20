"""
Research Desk — Week 3 Project

Usage:
  python week3agent.py
  python week3agent.py "question"
  python week3agent.py --tui
  python week3agent.py --session abc123
"""

import os
import json
import uuid
import argparse

from dotenv import load_dotenv
from openai import OpenAI

from web import web_search, web_fetch
from papers import paper_search, read_paper
from files import (
    read_file,
    write_file,
    list_files,
    edit_file
)

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

MODEL = "openrouter/free"

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
    },
        {
        "type": "function",
        "function": {
            "name": "web_search",
            "description":
                "Search the web using Serper.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    },
                    "num_results": {
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
            "name": "web_fetch",
            "description":
                "Fetch and extract readable text from a webpage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string"
                    }
                },
                "required": ["url"]
            }
        }
    }
]

class Agent:

    def __init__(self, session_id=None):

        self.session_id = (
            session_id
            or str(uuid.uuid4())[:8]
        )

        self.messages = []

        self.tools = {
            "web_search": web_search,
            "web_fetch": web_fetch,
            "paper_search": paper_search,
            "read_paper": read_paper,
            "read_file": read_file,
            "write_file": write_file,
            "list_files": list_files,
            "edit_file": edit_file,
        }

        self.load_agents_md()
        self.load_session()

    def load_agents_md(self):

        try:

            with open(
                "AGENTS.md",
                "r",
                encoding="utf-8"
            ) as f:

                agents_rules = f.read()

        except FileNotFoundError:

            agents_rules = ""

        self.messages = [
            {
                "role": "system",
                "content": agents_rules
            }
        ]

    def load_session(self):

        os.makedirs(
            ".agent/sessions",
            exist_ok=True
        )

        session_file = (
            f".agent/sessions/"
            f"{self.session_id}.json"
        )

        if os.path.exists(session_file):

            with open(
                session_file,
                "r",
                encoding="utf-8"
            ) as f:

                self.messages = json.load(f)

    def save_session(self):

        os.makedirs(
            ".agent/sessions",
            exist_ok=True
        )

        session_file = (
            f".agent/sessions/"
            f"{self.session_id}.json"
        )

        with open(
            session_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.messages,
                f,
                indent=2
            )

    def dispatch_tool(
        self,
        tool_name,
        **kwargs
    ):

        if tool_name not in self.tools:

            return {
                "error":
                f"Unknown tool: {tool_name}"
            }

        self._emit(
            f"  [tool] {tool_name}"
        )

        return self.tools[
            tool_name
        ](**kwargs)

    def _emit(
        self,
        message
    ):
        print(message)

    def _run_loop(self):

        for _ in range(10):

            response = client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=TOOLS,
            )

            message = response.choices[0].message
            finish_reason = (
                response.choices[0]
                .finish_reason
            )

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
                                    "name":
                                    tc.function.name,
                                    "arguments":
                                    tc.function.arguments,
                                },
                            }
                            for tc
                            in message.tool_calls
                        ]
                    }
                )

                for tool_call in message.tool_calls:

                    tool_result = (
                        self.dispatch_tool(
                            tool_call.function.name,
                            **json.loads(
                                tool_call.function.arguments
                            )
                        )
                    )

                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id":
                            tool_call.id,
                            "content":
                            json.dumps(
                                tool_result
                            )
                        }
                    )

                continue

            if finish_reason == "stop":

                self.messages.append(
                    {
                        "role": "assistant",
                        "content":
                        message.content
                    }
                )

                return message.content

        return "[Agent stopped]"

    def chat(
        self,
        user_message
    ):

        self.messages.append(
            {
                "role": "user",
                "content": user_message
            }
        )

        answer = self._run_loop()

        self.save_session()

        return answer


class REPLAgent(Agent):

    def run(self):

        print(
            f"Research Desk "
            f"[{self.session_id}] "
            f"— /quit to exit"
        )

        while True:

            user_input = input("> ")

            if user_input.strip() == "/quit":
                break

            answer = self.chat(
                user_input
            )

            print(answer)

    def run_once(
        self,
        question
    ):

        answer = self.chat(
            question
        )

        print(answer)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "question",
        nargs="?"
    )

    parser.add_argument(
        "--session"
    )

    parser.add_argument(
        "--tui",
        action="store_true"
    )

    args = parser.parse_args()

    if args.tui:

        from tui import ResearchDeskApp

        app = ResearchDeskApp()
        app.run()

        return

    agent = REPLAgent(
        session_id=args.session
    )

    if args.question:
        agent.run_once(
            args.question
        )
    else:
        agent.run()


if __name__ == "__main__":
    main()
