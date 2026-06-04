import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def call_model(prompt: str) -> str:
    """
    Make a single chat completion call.
    Print the full response object first and understand its structure.
    Then return just the assistant's text.
    """
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    print("FULL RESPONSE:")
    print(response)

    print("\nUSAGE:")
    print(response.usage)

    print("\nCHOICES:")
    print(response.choices)

    return response.choices[0].message.content

if __name__ == "__main__":
    print(call_model("What is the capital of Australia?"))
