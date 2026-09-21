import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent_framework import Message
from agents.foundry_agents import get_architecture_agent


OWNER = "Tanishka1986920"
REPO = "campus-placement-ai-agent"
ISSUE_NUMBER = 4
NEW_TITLE = "Create UI Agent and Stitch Interface"


async def main():
    print("\n========================================")
    print("        FIX ISSUE #4 TITLE")
    print("========================================\n")

    agent = get_architecture_agent()
    session = agent.create_session()

    prompt = f"""
Access this GitHub repository:

Owner: {OWNER}
Repository: {REPO}

Update ONLY the title of GitHub issue #{ISSUE_NUMBER}.

Current issue: #{ISSUE_NUMBER}
New title: {NEW_TITLE}

IMPORTANT RULES:
1. First read issue #{ISSUE_NUMBER}.
2. Change ONLY the title to exactly:
   {NEW_TITLE}
3. Keep the entire issue body unchanged.
4. Keep all checklist states unchanged.
5. Do not close the issue.
6. Do not modify any other issue.
7. Do not modify repository files.
8. After updating, read issue #{ISSUE_NUMBER} again and confirm the title.
"""

    result = await agent.run(
        prompt,
        session=session
    )

    while result.user_input_requests:
        approval_responses = []

        for request in result.user_input_requests:
            if request.function_call is None:
                approval_responses.append(
                    request.to_function_approval_response(
                        approved=False
                    )
                )
                continue

            tool_name = request.function_call.name
            arguments = request.function_call.arguments
            arguments_text = str(arguments)

            print("\n----------------------------------------")
            print("GitHub tool requested:")
            print("Tool:", tool_name)
            print("Arguments:", arguments)
            print("----------------------------------------")

            # Allow safe reads
            if tool_name in {
                "issue_read",
                "get_issue",
                "list_issues",
            }:
                print("READ operation approved.")

                approval_responses.append(
                    request.to_function_approval_response(
                        approved=True
                    )
                )
                continue

            # Allow write ONLY for Issue #4
            if tool_name in {
                "issue_write",
                "update_issue",
            }:
                correct_owner = OWNER in arguments_text
                correct_repo = REPO in arguments_text

                correct_issue = (
                    f'"issue_number":{ISSUE_NUMBER}'
                    in arguments_text
                    or
                    f'"issue_number": {ISSUE_NUMBER}'
                    in arguments_text
                    or
                    f"'issue_number': {ISSUE_NUMBER}"
                    in arguments_text
                )

                correct_title = (
                    NEW_TITLE in arguments_text
                )

                if (
                    correct_owner
                    and correct_repo
                    and correct_issue
                    and correct_title
                ):
                    print(
                        f"WRITE approved for Issue "
                        f"#{ISSUE_NUMBER} title."
                    )

                    approval_responses.append(
                        request.to_function_approval_response(
                            approved=True
                        )
                    )
                else:
                    print(
                        "WRITE operation REJECTED."
                    )

                    approval_responses.append(
                        request.to_function_approval_response(
                            approved=False
                        )
                    )

                continue

            print(
                "Unexpected operation REJECTED."
            )

            approval_responses.append(
                request.to_function_approval_response(
                    approved=False
                )
            )

        result = await agent.run(
            Message(
                role="user",
                contents=approval_responses
            ),
            session=session
        )

    print("\n===== RESULT =====\n")

    if result.text:
        print(result.text)
    else:
        print(
            "No final response returned."
        )

    print("\n========================================")
    print("          TITLE FIX FINISHED")
    print("========================================")


if __name__ == "__main__":
    asyncio.run(main())