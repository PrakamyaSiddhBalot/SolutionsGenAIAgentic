"""
Build 2: Finding Code (grep + AST Outline)
=============================================
Two tools for finding the right place in a codebase you've never seen:
search file contents by pattern, and get a structural outline of a
single file without reading the whole thing.

Tasks:
  1. resolve_path(path) -> str | None
  2. grep(pattern, path=".", case_sensitive=False, max_results=50) -> dict
  3. list_definitions(path) -> dict   — AST-aware: list every function/class
     declared in a Python file, with line numbers
  4. Wire grep + list_definitions into TOOLS

Real-world reference for #3: Aider's repo map does this across an entire
multi-language repo using tree-sitter "tag" queries (see
https://aider.chat/2023/10/22/repomap.html and the implementation at
https://github.com/Aider-AI/aider/blob/main/aider/repomap.py), then ranks
files by reference count with PageRank. That's the bonus-tier "repo map"
challenge (see the README) — list_definitions here is the Python-only,
stdlib-`ast`-based version, scoped to one file at a time. See
https://docs.python.org/3/library/ast.html for the module reference;
every `ast.FunctionDef`/`ast.AsyncFunctionDef`/`ast.ClassDef` node carries
`.name`, `.lineno`, and `.end_lineno` once parsed.

Test this against a real external repo, not this file's own directory —
clone something like https://github.com/pallets/flask into ../target_repo
and point WORKSPACE_ROOT at it before running the demo below.

Run directly: grep for a common pattern, then outline the first match.
"""

import ast
import os

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
MAX_GREP_RESULTS = 50
EXCLUDE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}


def resolve_path(path: str) -> str | None:

    abs_path = os.path.abspath(
        os.path.join(
            WORKSPACE_ROOT,
            path
        )
    )

    if not abs_path.startswith(
        WORKSPACE_ROOT
    ):
        return None

    return abs_path


def grep(
    pattern: str,
    path: str = ".",
    case_sensitive: bool = False,
    max_results: int = MAX_GREP_RESULTS,
) -> dict:

    root = resolve_path(path)

    if root is None:

        return {
            "error":
            "path escapes workspace"
        }

    matches = []
    total_matches = 0

    for dirpath, dirnames, filenames in os.walk(root):

        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS
        ]

        for filename in filenames:

            file_path = os.path.join(
                dirpath,
                filename
            )

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8"
                ) as f:

                    for line_number, line in enumerate(
                        f,
                        start=1
                    ):

                        text = line.rstrip()

                        if case_sensitive:

                            found = (
                                pattern in text
                            )

                        else:

                            found = (
                                pattern.lower()
                                in text.lower()
                            )

                        if found:

                            total_matches += 1

                            if len(matches) < max_results:

                                matches.append(
                                    {
                                        "file":
                                        os.path.relpath(
                                            file_path,
                                            WORKSPACE_ROOT
                                        ),
                                        "line":
                                        line_number,
                                        "text":
                                        text
                                    }
                                )

            except (
                UnicodeDecodeError,
                PermissionError,
                OSError
            ):

                continue

    return {
        "matches": matches,
        "truncated":
        total_matches > max_results,
        "total_matches":
        total_matches
    }


def list_definitions(path: str) -> dict:

    file_path = resolve_path(path)

    if file_path is None:

        return {
            "error":
            "path escapes workspace"
        }

    if not os.path.exists(file_path):

        return {
            "error":
            "file does not exist"
        }

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            source = f.read()

        tree = ast.parse(source)

    except SyntaxError as e:

        return {
            "error":
            f"SyntaxError: {e}"
        }

    except Exception as e:

        return {
            "error": str(e)
        }

    definitions = []

    for node in tree.body:

        if isinstance(
            node,
            ast.FunctionDef
        ):

            definitions.append(
                {
                    "kind":
                    "function",
                    "name":
                    node.name,
                    "line":
                    node.lineno,
                    "end_line":
                    node.end_lineno
                }
            )

        elif isinstance(
            node,
            ast.AsyncFunctionDef
        ):

            definitions.append(
                {
                    "kind":
                    "async function",
                    "name":
                    node.name,
                    "line":
                    node.lineno,
                    "end_line":
                    node.end_lineno
                }
            )

        elif isinstance(
            node,
            ast.ClassDef
        ):

            definitions.append(
                {
                    "kind":
                    "class",
                    "name":
                    node.name,
                    "line":
                    node.lineno,
                    "end_line":
                    node.end_lineno
                }
            )

            for item in node.body:

                if isinstance(
                    item,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef
                    )
                ):

                    definitions.append(
                        {
                            "kind":
                            "method",
                            "name":
                            item.name,
                            "line":
                            item.lineno,
                            "end_line":
                            item.end_lineno
                        }
                    )

    return {
        "definitions":
        definitions
    }


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": (
                "Search file contents for a pattern across the workspace. "
                "Use this before read_file when you don't already know which "
                "file you need."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text or regex to search for."},
                    "path": {"type": "string", "description": "Subdirectory to search, default workspace root."},
                    "case_sensitive": {"type": "boolean", "description": "Default false."},
                    "max_results": {
                        "type": "integer",
                        "description": f"Cap on matches returned. Default {MAX_GREP_RESULTS}.",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_definitions",
            "description": (
                "List the functions and classes declared in a Python file, "
                "with line numbers, without reading the whole file. Use this "
                "right after grep to decide which match is worth reading in "
                "full with read_file."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to a Python file."},
                },
                "required": ["path"],
            },
        },
    },
]


if __name__ == "__main__":
    print("Searching for top-level function definitions ('def '):")
    result = grep("def ", max_results=10)
    print(result)

    if result and result.get("matches"):
        first_file = result["matches"][0]["file"]
        print(f"\nOutline of {first_file}:")
        print(list_definitions(first_file))
