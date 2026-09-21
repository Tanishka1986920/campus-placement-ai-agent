import json
from pathlib import Path


# ==================================================
# Project paths
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = (PROJECT_ROOT / "backend").resolve()


# Files that agents must NEVER modify
BLOCKED_NAMES = {
    ".env",
    ".git",
    ".gitignore",
}


# ==================================================
# Validate backend path
# ==================================================

def get_safe_backend_path(relative_path: str) -> Path:
    """
    Convert an agent-provided relative path into a safe
    path inside the backend/ directory.

    Example:
        app/main.py
            ->
        backend/app/main.py
    """

    if not relative_path:
        raise ValueError("File path cannot be empty.")

    relative_path = relative_path.replace("\\", "/").strip()

    # Backend Agent may return paths like "backend/app/main.py".
    # BACKEND_ROOT already points to backend/, so remove this prefix.
    if relative_path.lower().startswith("backend/"):
        relative_path = relative_path[len("backend/"):]

    # Do not allow absolute paths
    supplied_path = Path(relative_path)

    if supplied_path.is_absolute():
        raise ValueError(
            f"Absolute paths are not allowed: {relative_path}"
        )

    # Do not allow traversal such as ../../
    if ".." in supplied_path.parts:
        raise ValueError(
            f"Parent directory traversal is not allowed: "
            f"{relative_path}"
        )

    # Block sensitive names anywhere in the path
    for part in supplied_path.parts:
        if part.lower() in BLOCKED_NAMES:
            raise ValueError(
                f"Protected path cannot be modified: "
                f"{relative_path}"
            )

    final_path = (BACKEND_ROOT / supplied_path).resolve()

    # Final safety check:
    # resulting file MUST remain inside backend/
    try:
        final_path.relative_to(BACKEND_ROOT)
    except ValueError:
        raise ValueError(
            f"Path escaped backend directory: {relative_path}"
        )

    return final_path


# ==================================================
# Write one file
# ==================================================

def write_backend_file(relative_path: str, content: str):
    """
    Safely create or overwrite one file inside backend/.
    """

    file_path = get_safe_backend_path(relative_path)

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path.write_text(
        content,
        encoding="utf-8"
    )

    return file_path


# ==================================================
# Write multiple files
# ==================================================

def apply_backend_changes(files):
    """
    Expected format:

    [
        {
            "path": "app/main.py",
            "content": "..."
        },
        {
            "path": "requirements.txt",
            "content": "..."
        }
    ]
    """

    if not isinstance(files, list):
        raise ValueError(
            "Backend changes must be a list."
        )

    if len(files) == 0:
        raise ValueError(
            "No backend files were provided."
        )

    # Prevent an agent from unexpectedly creating
    # a huge number of files in one run.
    if len(files) > 30:
        raise ValueError(
            "Maximum 30 files can be changed in one run."
        )

    # ----------------------------------------------
    # Validate EVERYTHING before writing anything
    # ----------------------------------------------

    validated_files = []

    for item in files:

        if not isinstance(item, dict):
            raise ValueError(
                "Every file entry must be an object."
            )

        relative_path = item.get("path")
        content = item.get("content")

        if not isinstance(relative_path, str):
            raise ValueError(
                "Each file must contain a string path."
            )

        if not isinstance(content, str):
            raise ValueError(
                f"File content must be text: "
                f"{relative_path}"
            )

        safe_path = get_safe_backend_path(
            relative_path
        )

        validated_files.append(
            (
                relative_path,
                safe_path,
                content
            )
        )

    # ----------------------------------------------
    # All paths are safe -> write files
    # ----------------------------------------------

    written_files = []

    for relative_path, safe_path, content in validated_files:

        safe_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        safe_path.write_text(
            content,
            encoding="utf-8"
        )

        written_files.append(
            str(safe_path.relative_to(PROJECT_ROOT))
        )

        print(
            f"[FILE CREATED/UPDATED] "
            f"{safe_path.relative_to(PROJECT_ROOT)}"
        )

    return written_files


# ==================================================
# Parse Backend Agent JSON
# ==================================================

def parse_backend_agent_output(agent_output: str):
    """
    Backend Agent will eventually return JSON:

    {
        "files": [
            {
                "path": "app/main.py",
                "content": "..."
            }
        ]
    }
    """

    if not agent_output:
        raise ValueError(
            "Backend Agent returned empty output."
        )

    text = agent_output.strip()

    # Remove Markdown ```json ... ``` wrapper
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
            "Backend Agent did not return valid JSON.\n"
            f"JSON error: {error}"
        )

    if not isinstance(data, dict):
        raise ValueError(
            "Backend Agent response must be a JSON object."
        )

    files = data.get("files")

    if not isinstance(files, list):
        raise ValueError(
            "Backend Agent JSON must contain a 'files' list."
        )

    return files


# ==================================================
# Apply Backend Agent output
# ==================================================

def apply_backend_agent_output(agent_output: str):

    files = parse_backend_agent_output(
        agent_output
    )

    written_files = apply_backend_changes(
        files
    )

    return written_files


# ==================================================
# Manual safety test
# ==================================================

if __name__ == "__main__":

    print("\n========================================")
    print("       FILE MANAGER SAFETY TEST")
    print("========================================\n")

    # This creates only a harmless test file
    # inside backend/
    test_files = [
        {
            "path": "test_file_manager.txt",
            "content": (
                "File Manager is working correctly.\n"
                "This file was created safely inside backend/."
            ),
        }
    ]

    try:

        written = apply_backend_changes(
            test_files
        )

        print("\nSUCCESS")

        print("\nFiles written:")

        for file in written:
            print("-", file)

    except Exception as error:

        print("\nERROR:")
        print(error)

    print("\n========================================")