import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

def call_model(prompt: str) -> str:
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

def call_model_thor(prompt: str) -> str:
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "system",
                "content": "You are Thor, God of Thunder from Norse mythology. Speak proudly and refer to your hammer Mjolnir when appropriate."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    print(call_model("What is the capital of Australia?"))
    print()
    print(call_model_thor("What is the capital of Australia?"))
