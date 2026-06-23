# Code Scout Submission

## What I Built

For this project, I built **Code Scout**, a coding agent that can explore a repository, search through code, create and manage todo lists, execute commands with user approval, edit files, and verify its own work by rerunning tests.

The agent combines several tools:

* File tools (`read_file`, `write_file`, `edit_file`, `list_files`)
* Search tools (`grep`, `list_definitions`)
* Command execution (`run_command`)
* Planning tools (`add_todos`, `get_todos`, `mark_todo`)

The most important feature is that the agent does not immediately jump into editing code. Instead, it creates a plan, tracks progress through todos, gathers evidence, and only marks work as completed when verification has been performed.

I also implemented an approval gate for command execution so that potentially impactful commands require explicit user permission before running.

---

## Repository Used for Testing

I tested Code Scout against the Flask repository:

https://github.com/pallets/flask

I chose Flask because it is a real-world Python project with a substantial test suite, many modules, and enough complexity to meaningfully evaluate whether the agent could investigate problems rather than simply search for keywords.

The repository was cloned locally into `target_repo/flask` and used as a sandbox for testing.

---

## Example: Agent Investigated and Fixed a Real Issue

One of the first things I did was run the Flask test suite.

The tests failed during collection with an import error in `tests/test_cli.py`:

```python
from _pytest.monkeypatch import notset
```

The agent created a todo plan, reproduced the failure, inspected the affected files, checked the installed pytest version, investigated pytest internals, and eventually determined that newer versions of pytest had renamed `notset` to `NOTSET`.

The agent then updated the affected code and reran the tests.

After the fix:

* `tests/test_cli.py` successfully ran.
* 55 tests passed and 3 were skipped.
* The original collection failure disappeared.

The verification step was important because it demonstrated that the fix actually worked rather than merely looking plausible.

Interestingly, once that issue was fixed, a different failure deeper in the test suite became visible. This gave me confidence that the agent had genuinely removed the original blocker instead of hiding it.

---

## Example: Todo Loop and Approval Prompt Prevented Mistakes

While testing, the agent frequently wanted to execute shell commands in order to investigate the repository.

For example, before running commands such as:

```bash
python -m pytest
```

or repository search commands, the agent displayed an approval prompt and waited for confirmation.

This prevented the agent from executing commands automatically without oversight.

The todo system also proved useful. During one investigation, the agent reached its iteration limit before finishing all tasks. Instead of claiming success, it detected that outstanding todos still existed and stopped with a message indicating that work remained. This prevented it from reporting an incomplete investigation as finished.

That behavior was exactly what I wanted: the agent should be cautious about declaring success when verification has not yet happened.

---


