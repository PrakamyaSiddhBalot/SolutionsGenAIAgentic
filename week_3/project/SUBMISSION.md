# Week 3 Submission – Research Desk

This week's project felt like the point where everything from the previous weeks started coming together.

In Week 1, I built a chatbot. In Week 2, I gave it tools and a UI. In Week 3, I turned it into something that actually feels like an agent. It can search the web, search papers, read papers, work with files, save notes, and most importantly, remember previous conversations.

The biggest architectural change was creating a proper `Agent` class. Instead of putting logic directly inside the REPL or the Textual UI, I moved all the actual agent behavior into a shared class. The REPL and TUI are now just different interfaces sitting on top of the same brain. Once I got that structure working, everything else became much easier to reason about.

One feature I particularly liked was session persistence. Previous versions of the chatbot forgot everything as soon as the terminal closed. Now conversations are saved to disk and can be resumed later. It sounds simple, but it makes the agent feel much more real because it actually has a past.

The paper tools took far more time than I expected. On paper, implementing `paper_search` and `read_paper` looked straightforward. In practice, I spent a lot of time fighting connection errors from Hugging Face. At one point I had tiny test scripts returning HTTP 200 successfully while the exact same requests inside my project were throwing connection resets. That led me down a rabbit hole of certificate verification, certifi, retries, timeouts, and several rounds of testing before I finally got things working consistently enough.

I also lost more time than I would like to admit to a simple indentation mistake while integrating the paper tools into Build 2. The bug itself wasn't complicated, but because it sat inside the tool-calling loop it caused behavior that looked much more serious than it actually was. That was a good reminder that sometimes the smallest bugs create the biggest headaches.

The file tools were more straightforward. I implemented reading, writing, listing, and editing files. Together with the paper and web tools, this allows the agent to actually build and maintain research notes instead of just answering questions.

For the UI, I reused my Week 2 Textual interface and connected it to the new agent architecture. Most of the work was wiring the UI into the agent correctly. One funny issue I ran into was that Textual already has a built-in property called `log`, so when I tried assigning my own `self.log`, the application immediately crashed. Renaming it to `self.chat_log` fixed the problem. I also reused the workaround from Week 2 where I had to replace `Ctrl+K` because my terminal intercepted it before Textual could receive the key press.

The thing I learned most this week wasn't a specific library or API. It was the value of separating responsibilities. Having one class responsible for reasoning, tools, and memory while keeping the interfaces separate made the code much easier to extend. The final project ended up being significantly larger than anything I built in the earlier weeks, but it stayed manageable because of that structure.

By the end, I had a research agent that can:

* Search the web
* Read webpages
* Search academic papers
* Read and summarize papers
* Create and edit research notes
* Save and resume conversations
* Run in both a REPL and a full-screen TUI

This was definitely the most debugging-heavy week so far, mostly because of the Hugging Face API issues, but it was also the most satisfying one because the final result feels like an actual tool that I could continue improving rather than a small course exercise.

