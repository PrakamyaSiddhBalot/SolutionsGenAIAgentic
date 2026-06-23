import json
import os

TODO_FILE = ".agent/todos.json"

VALID_STATUSES = {
    "pending",
    "in_progress",
    "completed",
    "blocked"
}

def load_todos():

    os.makedirs(
        ".agent",
        exist_ok=True
    )

    if not os.path.exists(
        TODO_FILE
    ):

        return []

    with open(
        TODO_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)

def save_todos(todos):

    os.makedirs(
        ".agent",
        exist_ok=True
    )

    with open(
        TODO_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            todos,
            f,
            indent=2
        )

def add_todos(items):

    todos = load_todos()

    next_id = 1

    if todos:

        next_id = (
            max(
                todo["id"]
                for todo in todos
            )
            + 1
        )

    for item in items:

        todos.append(
            {
                "id": next_id,
                "title":
                item["title"],
                "description":
                item["description"],
                "verification":
                item["verification"],
                "status":
                "pending",
                "block_reason":
                None,
                "evidence":
                None
            }
        )

        next_id += 1

    save_todos(todos)

    return {
        "todos": todos
    }

def get_todos(status=None):

    todos = load_todos()

    if status is None:

        return {
            "todos": todos
        }

    return {
        "todos": [
            todo
            for todo in todos
            if todo["status"] == status
        ]
    }

def mark_todo(
    todo_id,
    status,
    evidence=None,
    block_reason=None
):

    if status not in VALID_STATUSES:

        return {
            "error":
            f"invalid status: {status}"
        }

    todos = load_todos()

    for todo in todos:

        if todo["id"] == todo_id:

            if (
                status == "completed"
                and not evidence
            ):

                return {
                    "error":
                    "cannot mark completed without evidence"
                }

            todo["status"] = status

            if evidence:
                todo["evidence"] = evidence

            if status == "blocked":

                todo["block_reason"] = block_reason

            else:

                todo["block_reason"] = None

            save_todos(todos)

            return {
                "todo": todo
            }

    return {
        "error":
        f"todo {todo_id} not found"
    }

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_todos",
            "description": (
                "Create one or more todo items for a task plan. "
                "Use this before starting multi-step work so progress "
                "can be tracked and verified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "description": "List of todos to add.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "Short todo title."
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Description of the work."
                                },
                                "verification": {
                                    "type": "string",
                                    "description": (
                                        "How completion will be verified."
                                    )
                                }
                            },
                            "required": [
                                "title",
                                "description",
                                "verification"
                            ]
                        }
                    }
                },
                "required": ["items"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_todos",
            "description": (
                "Retrieve the current todo list. "
                "Use this to inspect progress or find remaining work."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": [
                            "pending",
                            "in_progress",
                            "completed",
                            "blocked"
                        ],
                        "description": (
                            "Optional status filter."
                        )
                    }
                }
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "mark_todo",
            "description": (
                "Update a todo item's status. "
                "Completed todos require verification evidence. "
                "Blocked todos should include a block reason."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "todo_id": {
                        "type": "integer",
                        "description": "ID of the todo to update."
                    },

                    "status": {
                        "type": "string",
                        "enum": [
                            "pending",
                            "in_progress",
                            "completed",
                            "blocked"
                        ],
                        "description": (
                            "New status for the todo."
                        )
                    },

                    "evidence": {
                        "type": "string",
                        "description": (
                            "Verification evidence required when "
                            "marking a todo completed."
                        )
                    },

                    "block_reason": {
                        "type": "string",
                        "description": (
                            "Reason the todo is blocked."
                        )
                    }
                },
                "required": [
                    "todo_id",
                    "status"
                ]
            }
        }
    }
]


if __name__ == "__main__":
    print(
        add_todos(
            [
                {
                    "title":
                    "Find failing tests",

                    "description":
                    "Locate failing tests in the repository",

                    "verification":
                    "pytest exits 0"
                },
                {
                    "title":
                    "Fix authentication",

                    "description":
                    "Repair auth module",

                    "verification":
                    "test_auth.py passes"
                }
            ]
        )
    )
    print(
        get_todos()
    )
    print(
        get_todos(
            "pending"
        )
    )
    print(
        get_todos(
            "completed"
        )
    )
    print(
        mark_todo(
            2,
            "completed"
        )
    )
    print(
        mark_todo(
            2,
            "in_progress"
        )
    )
    print(
        mark_todo(
            2,
            "blocked",
            block_reason=
            "user declined write approval"
        )
    )
    print(
        mark_todo(
            2,
            "completed",
            evidence=
            "pytest exited 0"
        )
    )
