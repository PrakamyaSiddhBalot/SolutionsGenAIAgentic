"""
Build 1: Command Execution
============================
A sandboxed run_command tool: search, inspect history, run tests — and,
once a human approves, make real changes to the repo.

Tasks:
  1. paths_within_sandbox(command, workspace_root) -> bool
  2. classify_command(command) -> "read_only" | "ask"
  3. run_command(command, cwd=WORKSPACE_ROOT, timeout=10) -> dict
  4. Wire run_command into the OpenAI tool schema (TOOLS)

Run directly: a read-only command should run immediately; a destructive
one should print a warning and wait for y/n before doing anything.
"""

import os
import shlex
import subprocess

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
TIMEOUT_DEFAULT = 10
MAX_OUTPUT_CHARS = 8_000

# Known-safe: run immediately once the path check passes.
READ_ONLY_PREFIXES = (
    "grep", "find", "ls", "cat", "head", "tail", "wc",
    "git log", "git diff", "git status", "git blame", "git show",
    "pytest", "python -m pytest", "ruff", "flake8", "mypy",
)
# If I add dir to the tuple of prefixes, then I'll successfully get the command to execute seamlessly, as expected.

# Known-destructive: always ask, even if they'd otherwise look harmless.
DESTRUCTIVE_PATTERNS = (
    "rm ", "mv ", ">", ">>", "git commit", "git push", "git checkout --",
    "pip install", "npm install", "curl ", "sudo ", "chmod ",
)


def paths_within_sandbox(
    command: str,
    workspace_root: str
) -> bool:

    try:

        tokens = shlex.split(command)

    except ValueError:

        return False

    for token in tokens:

        if (
            "/" in token
            or "\\" in token
            or token.startswith(".")
        ):

            abs_path = os.path.abspath(
                os.path.join(
                    workspace_root,
                    token
                )
            )

            if not abs_path.startswith(
                workspace_root
            ):
                return False

    return True


def classify_command(command: str) -> str:

    command = command.strip()

    for pattern in DESTRUCTIVE_PATTERNS:

        if pattern in command:
            return "ask"

    for prefix in READ_ONLY_PREFIXES:

        if command.startswith(prefix):
            return "read_only"

    return "ask"


def run_command(
    command: str,
    cwd: str = WORKSPACE_ROOT,
    timeout: int = TIMEOUT_DEFAULT
) -> dict:

    if not paths_within_sandbox(
        command,
        cwd
    ):

        return {
            "error":
            "blocked: command escapes workspace"
        }

    command_type = classify_command(
        command
    )

    if command_type == "ask":

        print("\nWARNING!")

        print(
            f"The agent wants to run:\n"
            f"{command}"
        )

        approved = (
            input(
                "Allow? [y/N]: "
            )
            .strip()
            .lower()
        )

        if approved != "y":

            return {
                "error":
                "blocked: user did not approve command"
            }

    try:

        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            timeout=timeout,
            capture_output=True,
            text=True
        )

        stdout = result.stdout
        stderr = result.stderr

        if len(stdout) > MAX_OUTPUT_CHARS:

            stdout = (
                stdout[:MAX_OUTPUT_CHARS]
                + "\n\n[...truncated]"
            )

        if len(stderr) > MAX_OUTPUT_CHARS:

            stderr = (
                stderr[:MAX_OUTPUT_CHARS]
                + "\n\n[...truncated]"
            )

        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code":
            result.returncode
        }

    except subprocess.TimeoutExpired:

        return {
            "error":
            f"command timed out after "
            f"{timeout} seconds"
        }

    except Exception as e:

        return {
            "error": str(e)
        }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": (
                "Run a shell command in the workspace and return its output. "
                "Use this to search (grep/find), inspect history (git log/diff), "
                "run tests, or make a change. Read-only commands run immediately. "
                "Anything that writes, deletes, or installs will pause and ask the "
                "human operator for approval — expect that pause, it's not a failure."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to run.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": f"Seconds before the command is killed. Default {TIMEOUT_DEFAULT}.",
                    },
                },
                "required": ["command"],
            },
        },
    }
]


if __name__ == "__main__":
    print("Read-only command (should run immediately):")
    print(run_command("git log --oneline -5"))

    print("\nDestructive command (should pause and ask for approval):")
    print(run_command("rm -rf /tmp/does-not-exist-example"))
    print(run_command("dir"))
    print(
        run_command(
            "del fakefile.txt"
        )
    )
