import os
import glob
from dotenv import load_dotenv

load_dotenv()

WORKSPACE_ROOT = os.path.abspath(
    os.environ.get("WORKSPACE_ROOT", ".")
)

MAX_READ_CHARS = 12_000
def resolve_path(path: str) -> str:

    full_path = os.path.abspath(
        os.path.join(
            WORKSPACE_ROOT,
            path
        )
    )

    if not full_path.startswith(WORKSPACE_ROOT):
        raise ValueError(
            "Path escapes workspace"
        )

    return full_path
def write_file(
    path: str,
    content: str
) -> dict:

    try:

        full_path = resolve_path(path)

        os.makedirs(
            os.path.dirname(full_path),
            exist_ok=True
        )

        with open(
            full_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(content)

        return {
            "content":
            (
                f"Wrote "
                f"{len(content)} characters "
                f"to {path}"
            )
        }

    except Exception as e:

        return {
            "error": str(e)
        }
def read_file(
    path: str,
    start_line: int = 1,
    read_lines: int = 200
) -> dict:

    try:

        full_path = resolve_path(path)

        with open(
            full_path,
            "r",
            encoding="utf-8"
        ) as f:

            lines = f.readlines()

        start_index = max(
            start_line - 1,
            0
        )

        end_index = start_index + read_lines

        selected_lines = lines[
            start_index:end_index
        ]

        numbered_lines = []

        for i, line in enumerate(
            selected_lines,
            start=start_line
        ):

            numbered_lines.append(
                f"{i:4}| {line.rstrip()}"
            )

        content = "\n".join(
            numbered_lines
        )

        if len(content) > MAX_READ_CHARS:

            content = (
                content[:MAX_READ_CHARS]
                + "\n\n[...truncated]"
            )

        return {
            "content": content,
            "has_more": end_index < len(lines)
        }

    except Exception as e:

        return {
            "error": str(e)
        }
def list_files(
    path: str = ".",
    pattern: str = "*"
) -> dict:

    try:

        base_path = resolve_path(path)

        matches = glob.glob(
            os.path.join(
                base_path,
                pattern
            ),
            recursive=True
        )

        results = []

        for match in matches:

            rel_path = os.path.relpath(
                match,
                WORKSPACE_ROOT
            )

            results.append(rel_path)

        results.sort()

        return {
            "content": results
        }

    except Exception as e:

        return {
            "error": str(e)
        }
def edit_file(
    path: str,
    operation: str,
    start_line: int,
    end_line: int | None = None,
    content: str | None = None,
) -> dict:

    try:

        full_path = resolve_path(path)

        with open(
            full_path,
            "r",
            encoding="utf-8"
        ) as f:

            lines = f.readlines()

        start_idx = start_line - 1

        preview = ""

        if operation == "replace":

            if end_line is None:
                return {
                    "error":
                    "replace requires end_line"
                }

            end_idx = end_line

            old_lines = lines[
                start_idx:end_idx
            ]

            new_lines = [
                line + "\n"
                for line in content.splitlines()
            ]

            lines[
                start_idx:end_idx
            ] = new_lines

            preview = (
                "REPLACED\n"
                f"- {''.join(old_lines)}\n"
                f"+ {content}"
            )

        elif operation == "delete":

            if end_line is None:
                return {
                    "error":
                    "delete requires end_line"
                }

            end_idx = end_line

            old_lines = lines[
                start_idx:end_idx
            ]

            del lines[
                start_idx:end_idx
            ]

            preview = (
                "DELETED\n"
                f"- {''.join(old_lines)}"
            )

        elif operation == "append":

            new_lines = [
                line + "\n"
                for line in content.splitlines()
            ]

            lines[
                start_idx:start_idx
            ] = new_lines

            preview = (
                "APPENDED\n"
                f"+ {content}"
            )

        else:

            return {
                "error":
                f"Unknown operation: {operation}"
            }

        with open(
            full_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.writelines(lines)

        return {
            "content": preview
        }

    except Exception as e:

        return {
            "error": str(e)
        }
