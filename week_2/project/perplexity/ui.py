from textual.app import App
from textual.app import ComposeResult

from textual.widgets import (
    Header,
    Footer,
    Input,
    RichLog
)

from textual.containers import Vertical

import asyncio

from agent import (
    run_agent,
    get_alphaxiv_tools,
    convert_mcp_tools,
    MCP_TOOLS,
    MCP_TOOL_NAMES
)


class ResearchBotApp(App):

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+l", "clear_display", "Clear Display"),
        ("ctrl+k", "clear_history", "Clear History"),
        ("ctrl+t", "test", "Test")
    ]
    #again ctrl+k doesn't work in my terminal and gets intercepted, so we can use f6 or ctrl+r instead.

    def compose(self) -> ComposeResult:

        yield Header()

        with Vertical():

            yield RichLog(
                id="chat_log"
            )

            yield RichLog(
                id="tool_log"
            )

            yield Input(
                placeholder="Ask a research question..."
            )

        yield Footer()


    def on_mount(self):

        import agent

        agent.TOOL_LOGGER = (
            lambda text:
            self.query_one(
                "#tool_log"
            ).write(text)
        )

    def action_clear_display(self):

        self.query_one(
            "#chat_log"
        ).clear()

        self.query_one(
            "#tool_log"
        ).clear()

    def action_clear_history(self):

        self.query_one(
            "#tool_log"
        ).write(
            "History cleared."
        )

    def action_test(self):

        self.query_one(
            "#tool_log"
        ).write(
            "Test shortcut works."
        )

    async def on_input_submitted(
        self,
        event
    ):

        user_text = event.value

        event.input.value = ""

        chat_log = self.query_one(
            "#chat_log"
        )

        chat_log.write(
            f"User: {user_text}"
        )

        try:

            response = await asyncio.to_thread(
                run_agent,
                user_text
            )

            chat_log.write(
                f"Bot: {response}"
            )

        except Exception as e:

            chat_log.write(
                f"ERROR: {str(e)}"
            )


if __name__ == "__main__":

    print(
        "Loading AlphaXiv MCP tools..."
    )

    tools_result = asyncio.run(
        get_alphaxiv_tools()
    )

    MCP_TOOLS[:] = convert_mcp_tools(
        tools_result
    )

    MCP_TOOL_NAMES.clear()

    MCP_TOOL_NAMES.update(
        tool["function"]["name"]
        for tool in MCP_TOOLS
    )

    print(
        f"Loaded {len(MCP_TOOLS)} MCP tools."
    )

    ResearchBotApp().run()
