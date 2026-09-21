import subprocess
import sys
from pathlib import Path


# ==================================================
# Project paths
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = (PROJECT_ROOT / "backend").resolve()


# ==================================================
# Run a safe command
# ==================================================

def run_command(command, cwd, timeout=60):
    """
    Run only commands defined by this orchestrator.
    Agent-generated commands are never executed here.
    """

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        return {
            "command": " ".join(command),
            "return_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "passed": result.returncode == 0,
        }

    except subprocess.TimeoutExpired:
        return {
            "command": " ".join(command),
            "return_code": -1,
            "stdout": "",
            "stderr": "Command timed out.",
            "passed": False,
        }

    except Exception as error:
        return {
            "command": " ".join(command),
            "return_code": -1,
            "stdout": "",
            "stderr": str(error),
            "passed": False,
        }


# ==================================================
# Python syntax / compile check
# ==================================================

def run_compile_check():

    print("\n===== PYTHON COMPILE CHECK =====\n")

    result = run_command(
        [
            sys.executable,
            "-m",
            "compileall",
            "-q",
            ".",
        ],
        cwd=BACKEND_ROOT,
    )

    if result["passed"]:
        print("PASS: Python files compiled successfully.")
    else:
        print("FAIL: Python compile check failed.")

    if result["stdout"]:
        print("\nOUTPUT:")
        print(result["stdout"])

    if result["stderr"]:
        print("\nERROR:")
        print(result["stderr"])

    return result


# ==================================================
# Pytest
# ==================================================

def run_pytest():

    print("\n===== PYTEST =====\n")

    tests_directory = BACKEND_ROOT / "tests"

    if not tests_directory.exists():
        result = {
            "command": f"{sys.executable} -m pytest -q",
            "return_code": -1,
            "stdout": "",
            "stderr": "backend/tests directory does not exist.",
            "passed": False,
        }

        print(
            "FAIL: backend/tests directory does not exist."
        )

        return result

    result = run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
        ],
        cwd=BACKEND_ROOT,
        timeout=300,
    )

    if result["passed"]:
        print("PASS: Pytest completed successfully.")
    else:
        print("FAIL: Pytest reported errors.")

    if result["stdout"]:
        print("\nOUTPUT:")
        print(result["stdout"])

    if result["stderr"]:
        print("\nERROR:")
        print(result["stderr"])

    return result


# ==================================================
# Run all backend tests
# ==================================================

def run_backend_tests():

    print("\n========================================")
    print("          BACKEND TEST RUNNER")
    print("========================================")

    compile_result = run_compile_check()

    pytest_result = run_pytest()

    overall_passed = (
        compile_result["passed"]
        and pytest_result["passed"]
    )

    print("\n========================================")

    if overall_passed:
        print("        ALL BACKEND TESTS PASSED")
    else:
        print("        BACKEND TESTS FAILED")

    print("========================================")

    return {
        "passed": overall_passed,
        "compile": compile_result,
        "pytest": pytest_result,
    }


# ==================================================
# Convert test results into evidence for Bug Agent
# ==================================================

def format_test_evidence(results):

    compile_result = results["compile"]
    pytest_result = results["pytest"]

    evidence = f"""
BACKEND TEST EXECUTION EVIDENCE

OVERALL PASSED:
{results["passed"]}

--------------------------------
PYTHON COMPILE CHECK
--------------------------------

Command:
{compile_result["command"]}

Return code:
{compile_result["return_code"]}

Passed:
{compile_result["passed"]}

STDOUT:
{compile_result["stdout"] or "(empty)"}

STDERR:
{compile_result["stderr"] or "(empty)"}

--------------------------------
PYTEST
--------------------------------

Command:
{pytest_result["command"]}

Return code:
{pytest_result["return_code"]}

Passed:
{pytest_result["passed"]}

STDOUT:
{pytest_result["stdout"] or "(empty)"}

STDERR:
{pytest_result["stderr"] or "(empty)"}
"""

    return evidence.strip()


# ==================================================
# Manual test
# ==================================================

if __name__ == "__main__":

    results = run_backend_tests()

    print(
        "\n\n===== EVIDENCE FOR BUG AGENT =====\n"
    )

    print(
        format_test_evidence(results)
    )