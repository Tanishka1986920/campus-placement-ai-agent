import sys
from pathlib import Path

# --------------------------------------------------
# Project root
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from agent_framework import Message
from agents.foundry_agents import get_architecture_agent


OWNER = "Tanishka1986920"
REPO = "campus-placement-ai-agent"


# ==================================================
# GitHub Checklist Updater
# ==================================================

async def update_github_checklist(
    issue_number,
    verified_items
):
    """
    Mark ONLY Bug/Issue-Agent-verified checklist items
    as complete in the selected GitHub issue.

    Nothing is updated when verified_items is empty.
    """

    if not verified_items:

        print(
            "\nNo verified checklist items. "
            "GitHub will not be modified."
        )

        return False

    print(
        "\n========================================"
    )

    print(
        f" UPDATING GITHUB ISSUE #{issue_number}"
    )

    print(
        "========================================\n"
    )

    agent = get_architecture_agent()
    session = agent.create_session()

    checklist_text = "\n".join(
        f"- {item}"
        for item in verified_items
    )

    prompt = f"""
Access this GitHub repository:

Owner: {OWNER}
Repository: {REPO}

Update GitHub issue #{issue_number}.

The Bug/Issue Agent has VERIFIED the following
exact checklist items:

{checklist_text}

IMPORTANT:

These items have already passed verification.

Update ONLY these exact checklist items.

INSTRUCTIONS:

1. First read GitHub issue #{issue_number} completely.

2. Keep the issue title unchanged.

3. Keep all existing issue description text unchanged.

4. Keep every checklist item and its wording unchanged.

5. For ONLY the exact verified checklist items listed
   above, change:

   - [ ] item

   to:

   - [x] item

6. If one of those items is already [x], leave it [x].

7. Do NOT mark any other checklist item complete.

8. Do NOT add checklist items.

9. Do NOT delete checklist items.

10. Do NOT rewrite or summarize the issue body.

11. Do NOT close the issue.

12. Do NOT modify repository files.

13. Do NOT modify another GitHub issue.

14. After the update, read issue #{issue_number}
    again.

15. Confirm which exact checklist items are now [x].

Do not make any other GitHub changes.
"""

    result = await agent.run(
        prompt,
        session=session
    )

    # ==================================================
    # GitHub MCP approval handling
    # ==================================================

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

            print(
                "\n----------------------------------------"
            )

            print(
                "GitHub tool requested:"
            )

            print(
                "Tool:",
                tool_name
            )

            print(
                "Arguments:",
                arguments
            )

            print(
                "----------------------------------------"
            )

            # ==========================================
            # READ OPERATIONS
            # ==========================================

            allowed_read_tools = {
                "issue_read",
                "get_issue",
                "list_issues",
            }

            if tool_name in allowed_read_tools:

                print(
                    "READ operation approved."
                )

                approval_responses.append(
                    request.to_function_approval_response(
                        approved=True
                    )
                )

                continue

            # ==========================================
            # WRITE OPERATIONS
            # ==========================================

            allowed_write_tools = {
                "issue_write",
                "update_issue",
            }

            if tool_name in allowed_write_tools:

                arguments_text = str(
                    arguments
                )

                correct_owner = (
                    OWNER in arguments_text
                )

                correct_repo = (
                    REPO in arguments_text
                )

                issue_patterns = [
                    f'"issue_number":{issue_number}',
                    f'"issue_number": {issue_number}',
                    f"'issue_number': {issue_number}",
                    f'"issueNumber":{issue_number}',
                    f'"issueNumber": {issue_number}',
                    f"'issueNumber': {issue_number}",
                ]

                correct_issue = any(
                    pattern in arguments_text
                    for pattern in issue_patterns
                )

                # Only allow update operations.
                #
                # Reject obvious create/delete/close
                # operations.

                arguments_lower = (
                    arguments_text.lower()
                )

                dangerous_operation = any(
                    word in arguments_lower
                    for word in [
                        '"method":"create"',
                        '"method": "create"',
                        "'method': 'create'",
                        '"method":"delete"',
                        '"method": "delete"',
                        "'method': 'delete'",
                        '"state":"closed"',
                        '"state": "closed"',
                        "'state': 'closed'",
                    ]
                )

                if (
                    correct_owner
                    and correct_repo
                    and correct_issue
                    and not dangerous_operation
                ):

                    print(
                        "WRITE operation approved "
                        f"for Issue #{issue_number}."
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

            # ==========================================
            # UNKNOWN OPERATION
            # ==========================================

            print(
                "Operation REJECTED because "
                "the tool was not expected."
            )

            approval_responses.append(
                request.to_function_approval_response(
                    approved=False
                )
            )

        # Continue the SAME Foundry session
        result = await agent.run(
            Message(
                role="user",
                contents=approval_responses
            ),
            session=session
        )

    # ==================================================
    # Result
    # ==================================================

    print(
        "\n===== GITHUB UPDATE RESULT =====\n"
    )

    if result.text:

        print(
            result.text
        )

    else:

        print(
            "No final response returned."
        )

    print(
        "\n========================================"
    )

    print(
        " GITHUB CHECKBOX UPDATE FINISHED"
    )

    print(
        "========================================"
    )

    return True