# Week 1 Submission - Building a Multi-Turn Chatbot

## Overview

In this project, I built a terminal-based chatbot using the OpenRouter API and the OpenAI Python SDK. The main goal was to understand how LLM APIs work, how conversation state is managed, and how memory can be simulated even though the API itself is stateless.

The final chatbot supports:

* Multi-turn conversations
* System prompts
* Conversation history
* Conversation reset
* Token usage inspection
* Model selection
* Rolling memory buffers
* Streaming responses

---

## Build 1: Making a Single API Call

I started by setting up OpenRouter and storing my API key in a `.env` file. I used `python-dotenv` to load the key and added `.env` to `.gitignore` so that it would never be uploaded to GitHub.

The first version of the program made a single API call and returned a response. Instead of immediately extracting the text, I inspected the entire response object. This helped me understand:

* What `response.choices` contains
* What `response.usage` contains
* How the assistant's message is stored

I also experimented with system prompts to see how they affect the model's behaviour.

---

## Build 2: Creating a Multi-Turn Chatbot

The next step was creating a chatbot that could hold a conversation.

At first I assumed that the model might remember previous messages automatically. However, while implementing the chatbot I learned that the API is completely stateless. Every call starts fresh.

To maintain conversation state, I created a `messages` list containing:

* A system message
* User messages
* Assistant messages

After every user input:

1. The user message is appended.
2. The full history is sent to the API.
3. The assistant reply is appended.

This means that the model appears to have memory because it is repeatedly shown the conversation history.

---

## Additional Commands

I implemented several utility commands.

### `/reset`

This clears the conversation history while preserving the system prompt.

This was useful because it demonstrated context loss. After resetting, the chatbot could no longer remember information that had been discussed earlier.

### `/tokens`

This displays token usage information from the previous API call.

By observing token counts during longer conversations, I could see that prompt tokens increased rapidly because the full conversation history was being sent on every request.

### `/history`

This command was added mainly for debugging purposes. It prints the current message history and was useful when testing the rolling buffer implementation.

---

## Refactoring into a ChatAgent Class

After the chatbot was working, I refactored the code into a `ChatAgent` class.

The goal was not to add new functionality but to organise the code better.

The class stores:

* The selected model
* Conversation history
* Token usage information
* Memory settings

The main methods are:

* `call_model()`
* `send_message()`
* `reset()`
* `trim_history()`

This made the chatbot easier to extend and maintain.

---

## Rolling Buffer Memory

One problem I observed was that token usage kept increasing as the conversation grew.

To address this, I implemented a rolling buffer.

The chatbot keeps only the last N conversation turns. When the limit is exceeded, the oldest user-assistant pair is removed.

For example:

### Before Overflow

User 1 → Assistant 1
User 2 → Assistant 2
User 3 → Assistant 3

### After a New Turn Arrives

User 2 → Assistant 2
User 3 → Assistant 3
User 4 → Assistant 4

This keeps token usage under control.

I experimented with different values of `max_turns` and observed the tradeoff:

* Larger buffers improve memory and coherence.
* Smaller buffers reduce token usage but cause the model to forget older information.

---

## Model Selection

To keep the chatbot model-agnostic, I allowed the user to choose from a menu of models before starting a conversation.

The selected model is passed into the `ChatAgent` constructor.

This design allows the chatbot to work with different OpenRouter models without changing the rest of the code.

---

## Streaming Responses

As an optional extension, I implemented streaming.

Instead of waiting for the entire response, tokens are printed as they arrive from the API.

This creates a more interactive experience and makes the chatbot feel more responsive.

At the same time, I reconstruct the complete response internally so that it can still be stored in conversation history.

I wished to also include compaction but decided against it because the buffering was based on removing the oldest pair. So I used a new feature of history instead. It's a debugging feature that helped me to analyse whether my buffer was working correctly or not. :)

---

## Challenges Encountered

This project was also my first real experience debugging a program that interacted with an external API, and I ran into several issues along the way.

At the beginning, I encountered problems installing packages correctly and received errors such as Python being unable to find the `openai` module. I also spent time figuring out why my environment variables were not loading, eventually discovering that my `.env` file had accidentally been saved as `.env.txt`.

Later, I ran into model availability issues on OpenRouter and learned that not every model listed online is necessarily available through the endpoint I was using. This forced me to use the openrouter- free model, enabling the chatbot to use whichever free model was avaliable instead of the specific deepseek model.

The most interesting debugging experience came while testing the rolling buffer. At one point I thought the buffer was completely broken because the chatbot still remembered information that I expected it to forget. After investigating, I discovered that I had configured different `max_turns` values in different parts of the program. Once I fixed that mistake, the buffer worked exactly as intended.


---

## Key Lessons Learned

The most important lesson from this project was understanding that LLMs do not inherently remember conversations.

The model only appears to have memory because previous messages are repeatedly included in the prompt.

This led to several related insights:

* Memory is actually context management.
* Longer conversations increase token usage.
* Memory systems require tradeoffs between context retention and efficiency.
* Features such as rolling buffers and summarisation are ways of managing context rather than adding true memory.

Overall, this project gave me a much clearer understanding of how chatbot applications are built on top of stateless language model APIs and if this is just the beginning of the track, then I'm absolutely excited to see where my journey goes! :)
