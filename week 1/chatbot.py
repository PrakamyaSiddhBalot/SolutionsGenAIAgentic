import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


class ChatAgent:
    def __init__(
        self,
        model,
        system_prompt="You are a helpful assistant.",
        max_turns=3
    ):
        self.model = model
        self.system_prompt = system_prompt
        self.max_turns = max_turns

        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

        self.last_usage = None

    def call_model(self):
        """
        Stream tokens as they arrive.
        Reconstruct the full reply so it can be stored in memory.
        """

        stream = client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True
        )

        full_reply = ""

        print("[MODEL] ", end="", flush=True)

        for chunk in stream:
            try:
                delta = chunk.choices[0].delta.content

                if delta:
                    full_reply += delta
                    print(delta, end="", flush=True)

            except (AttributeError, IndexError):
                pass

        print()

        return full_reply

    def trim_history(self):
        """
        Keep only the most recent max_turns.
        One turn = user + assistant pair.
        """

        max_messages = self.max_turns * 2

        while len(self.messages) - 1 > max_messages:
            self.messages.pop(1)
            self.messages.pop(1)

    def send_message(self, user_input):
        self.messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        assistant_reply = self.call_model()

        self.messages.append(
            {
                "role": "assistant",
                "content": assistant_reply
            }
        )

        self.trim_history()

        return assistant_reply

    def reset(self):
        self.messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

    def show_history(self):
        for msg in self.messages:
            print(msg)


def run_chatbot():

    models = {
        "1": "openrouter/free",
        "2": "google/gemma-4-31b-it:free",
        "3": "google/gemma-4-27b-it:free"
    }

    print("Choose a model:")
    print("1. OpenRouter Free")
    print("2. Gemma 4 31B")
    print("3. Gemma 4 27B")

    choice = input("Enter choice: ")

    selected_model = models.get(
        choice,
        "openrouter/free"
    )

    print(f"\nUsing model: {selected_model}")

    agent = ChatAgent(
        model=selected_model,
        max_turns=3
    )

    print("\nChat started. Type 'exit' to quit.\n")

    while True:
        user_input = input("[YOU] ")

        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break

        if user_input.strip().lower() == "/reset":
            agent.reset()
            print("Conversation history cleared.")
            continue

        if user_input.strip().lower() == "/tokens":
            if agent.last_usage:
                print(agent.last_usage)
            else:
                print(
                    "Usage information may not be available "
                    "for streamed responses."
                )
            continue

        if user_input.strip().lower() == "/history":
            print("\n=== HISTORY ===")

            for msg in agent.messages:
                print(msg)

            print("================\n")
            continue

        agent.send_message(user_input)


if __name__ == "__main__":
    run_chatbot()
