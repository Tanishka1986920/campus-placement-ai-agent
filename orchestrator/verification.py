import asyncio
import sys
from pathlib import Path

# --------------------------------------------------
# Add project root to Python path
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.foundry_agents import get_bug_agent


# --------------------------------------------------
# Bug / Issue Agent Verification
# --------------------------------------------------

async def verify_work(issue_number, issue_title, work_result):

    bug_agent = get_bug_agent()

    print("\n===== BUG/ISSUE AGENT STARTED =====\n")

    prompt = f"""
You are verifying work for this GitHub issue.

Issue number:
{issue_number}

Issue title:
{issue_title}

Work/evidence available:

------------------------------
{work_result}
------------------------------

Verify whether the supplied evidence actually proves that
the requested work is complete.

IMPORTANT RULES:

- Do not modify GitHub.
- Do not mark any checkbox yourself.
- Do not assume something was completed without evidence.
- If evidence is insufficient, return FAIL.
- If the work is correct and sufficiently verified, return PASS.
- Mention exactly what was verified.
- Mention what is still missing, if anything.

Your response MUST end with exactly one of:

VERIFICATION: PASS

or

VERIFICATION: FAIL
"""

    result = await bug_agent.run(prompt)

    print(result.text)

    return result.text


# --------------------------------------------------
# Test verification
# --------------------------------------------------

async def main():

    print("\n========================================")
    print("      BUG AGENT VERIFICATION TEST")
    print("========================================\n")

    # Evidence from the tests we actually performed
    evidence = """
Architecture Agent evidence:

1. architecture-agent already exists in Microsoft Foundry.

2. The local Python application successfully connected to
   architecture-agent using Microsoft Agent Framework.

3. Azure CLI authentication succeeded.

4. The Foundry project endpoint connection succeeded.

5. architecture-agent successfully invoked the connected
   GitHub MCP tool named 'list_issues'.

6. The tool successfully read open issues from:
   Tanishka1986920/campus-placement-ai-agent

7. architecture-agent successfully analyzed GitHub issue #2.

8. architecture-agent returned:
   ROUTE: ARCHITECTURE

9. The local orchestrator successfully detected this route
   and did not incorrectly send the task to Backend or UI.

Important:
Only verify claims supported by this evidence.
Do not assume untested functionality works.
"""

    verification = await verify_work(
        issue_number=2,
        issue_title="Create Architecture Agent",
        work_result=evidence
    )

    print("\n===== FINAL VERIFICATION =====\n")

    if verification and "VERIFICATION: PASS" in verification.upper():

        print("PASS")

        print(
            "\nBug Agent verified the supplied evidence."
        )

        print(
            "GitHub has NOT been modified yet."
        )

    else:

        print("FAIL")

        print(
            "\nNothing will be marked complete."
        )

    print("\n========================================")


if __name__ == "__main__":
    asyncio.run(main())