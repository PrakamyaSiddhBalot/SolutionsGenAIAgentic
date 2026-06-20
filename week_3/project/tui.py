from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import (
    Header,
    Footer,
    Input,
    RichLog
)

from week3agent import Agent


class TUIAgent(Agent):

    def __init__(self, app):
        super().__init__()
        self.app = app

    def _emit(self, message):

        self.app.call_from_thread(
            self.app.chat_log.write,
            message
        )


class ResearchDeskApp(App):

    TITLE = "Research Desk"

    BINDINGS = [
        Binding(
            "ctrl+l",
            "clear_display",
            "Clear Display"
        ),
        Binding(
            "ctrl+k",
            "clear_history",
            "Clear History"
        ),
        Binding(
            "ctrl+q",
            "quit",
            "Quit"
        ),
    ]

    def __init__(self):
        super().__init__()

        self.agent = TUIAgent(self)

    def compose(
        self
    ) -> ComposeResult:

        yield Header()

        yield RichLog(
            id="log",
            wrap=True,
            markup=True
        )

        yield Input(
            placeholder=
            "Ask Research Desk..."
        )

        yield Footer()

    def on_mount(self):

        self.chat_log = self.query_one(
            "#log",
            RichLog
        )

        self.chat_log.write(
            f"Research Desk "
            f"[{self.agent.session_id}]"
        )

        self.query_one(
            Input
        ).focus()

    def on_input_submitted(
        self,
        event
    ):

        user_text = (
            event.value.strip()
        )

        if not user_text:
            return

        event.input.clear()

        self.chat_log.write(
            f"[You] {user_text}"
        )

        self.run_worker(
            lambda:
            self._ask_agent(
                user_text
            ),
            thread=True
        )

    def _ask_agent(
        self,
        user_text
    ):

        try:

            answer = (
                self.agent.chat(
                    user_text
                )
            )

            self.call_from_thread(
                self.chat_log.write,
                f"[Agent] {answer}"
            )

        except Exception as e:

            self.call_from_thread(
                self.chat_log.write,
                f"[Error] {e}"
            )

    def action_clear_display(
        self
    ):

        self.chat_log.clear()

    def action_clear_history(
        self
    ):

        self.agent.load_agents_md()

        self.agent.save_session()

        self.chat_log.clear()

        self.chat_log.write(
            "Conversation reset."
        )


if __name__ == "__main__":
    ResearchDeskApp().run()
