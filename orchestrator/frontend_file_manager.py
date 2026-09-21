import json
from pathlib import Path


# ==================================================
# Project paths
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = (PROJECT_ROOT / "frontend").resolve()


# ==================================================
# Security settings
# ==================================================

BLOCKED_NAMES = {
    ".env",
    ".git",
    ".gitignore",
}

MAX_FILES = 30
MAX_FILE_SIZE = 500_000


# ==================================================
# Validate frontend path
# ==================================================

def get_safe_frontend_path(relative_path: str) -> Path:
    """
    Convert an agent-provided path into a safe path
    inside frontend/.

    Accepted examples:

        index.html
        css/style.css
        js/app.js

    Also accepts:

        frontend/index.html

    because the "frontend/" prefix will be removed.
    """

    if not relative_path:
        raise ValueError("File path cannot be empty.")

    relative_path = relative_path.replace("\\", "/").strip()

    # UI Agent may return:
    # frontend/index.html
    #
    # FRONTEND_ROOT already points to frontend/,
    # therefore remove duplicate prefix.
    if relative_path.lower().startswith("frontend/"):
        relative_path = relative_path[len("frontend/"):]

    supplied_path = Path(relative_path)

    # Do not allow absolute paths
    if supplied_path.is_absolute():
        raise ValueError(
            f"Absolute paths are not allowed: {relative_path}"
        )

    # Do not allow ../ traversal
    if ".." in supplied_path.parts:
        raise ValueError(
            f"Parent directory traversal is not allowed: "
            f"{relative_path}"
        )

    # Block sensitive files/folders
    for part in supplied_path.parts:
        if part.lower() in BLOCKED_NAMES:
            raise ValueError(
                f"Protected path cannot be modified: "
                f"{relative_path}"
            )

    final_path = (
        FRONTEND_ROOT / supplied_path
    ).resolve()

    # Final containment check
    try:
        final_path.relative_to(FRONTEND_ROOT)
    except ValueError:
        raise ValueError(
            f"Path escaped frontend directory: "
            f"{relative_path}"
        )

    return final_path


# ==================================================
# Write one frontend file
# ==================================================

def write_frontend_file(
    relative_path: str,
    content: str
):
    """
    Safely create or overwrite one file inside
    frontend/.
    """

    if not isinstance(content, str):
        raise ValueError(
            "Frontend file content must be text."
        )

    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ValueError(
            f"Frontend file is too large: "
            f"{relative_path}"
        )

    file_path = get_safe_frontend_path(
        relative_path
    )

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path.write_text(
        content,
        encoding="utf-8"
    )

    relative_written_path = (
        file_path.relative_to(PROJECT_ROOT)
    )

    print(
        "[FILE CREATED/UPDATED]",
        relative_written_path
    )

    return str(relative_written_path)


# ==================================================
# Apply multiple frontend changes
# ==================================================

def apply_frontend_changes(files):
    """
    Expected format:

    [
        {
            "path": "index.html",
            "content": "..."
        }
    ]
    """

    if not isinstance(files, list):
        raise ValueError(
            "Frontend changes must be a list."
        )

    if not files:
        raise ValueError(
            "No frontend files were provided."
        )

    if len(files) > MAX_FILES:
        raise ValueError(
            f"Too many frontend files. "
            f"Maximum allowed is {MAX_FILES}."
        )

    # Validate EVERYTHING before writing anything.
    validated_files = []

    for item in files:

        if not isinstance(item, dict):
            raise ValueError(
                "Each frontend file must be an object."
            )

        path = item.get("path")
        content = item.get("content")

        if not path:
            raise ValueError(
                "Frontend file is missing 'path'."
            )

        if content is None:
            raise ValueError(
                f"Frontend file '{path}' "
                f"is missing 'content'."
            )

        safe_path = get_safe_frontend_path(path)

        if not isinstance(content, str):
            raise ValueError(
                f"Content for '{path}' must be text."
            )

        if len(content.encode("utf-8")) > MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {path}"
            )

        validated_files.append(
            (safe_path, content)
        )

    written_files = []

    for safe_path, content in validated_files:

        safe_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        safe_path.write_text(
            content,
            encoding="utf-8"
        )

        relative_written_path = (
            safe_path.relative_to(PROJECT_ROOT)
        )

        print(
            "[FILE CREATED/UPDATED]",
            relative_written_path
        )

        written_files.append(
            str(relative_written_path)
        )

    return written_files


# ==================================================
# Parse UI Agent JSON
# ==================================================

def parse_ui_agent_output(agent_output: str):
    """
    UI Agent must return:

    {
        "files": [
            {
                "path": "index.html",
                "content": "..."
            }
        ]
    }
    """

    if not agent_output:
        raise ValueError(
            "UI Agent returned empty output."
        )

    text = agent_output.strip()

    # Remove accidental Markdown fences
    if text.startswith("```"):
        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:
        data = json.loads(text)

    except json.JSONDecodeError as error:
        raise ValueError(
            "UI Agent did not return valid JSON.\n"
            f"JSON error: {error}"
        )

    if not isinstance(data, dict):
        raise ValueError(
            "UI Agent response must be a JSON object."
        )

    files = data.get("files")

    if not isinstance(files, list):
        raise ValueError(
            "UI Agent JSON must contain a 'files' list."
        )

    return files


# ==================================================
# Apply UI Agent output
# ==================================================

def apply_ui_agent_output(agent_output: str):

    files = parse_ui_agent_output(
        agent_output
    )

    return apply_frontend_changes(
        files
    )


# ==================================================
# Safety test
# ==================================================

if __name__ == "__main__":

    print("\n========================================")
    print("     FRONTEND FILE MANAGER TEST")
    print("========================================\n")

    test_files = [
        {
            "path": "frontend/test_frontend_manager.txt",
            "content": (
                "This file was created safely "
                "inside frontend/."
            ),
        }
    ]

    try:

        written = apply_frontend_changes(
            test_files
        )

        print("\nSUCCESS\n")

        print("Files written:")

        for file in written:
            print("-", file)

    except Exception as error:

        print("\nFAILED\n")
        print(error)

    print("\n========================================")