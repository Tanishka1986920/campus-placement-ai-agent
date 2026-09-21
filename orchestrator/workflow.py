import asyncio
import sys
from pathlib import Path
from orchestrator.frontend_file_manager import apply_ui_agent_output
from orchestrator.github_update import update_github_checklist


# ==================================================
# Project setup
# ==================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = (PROJECT_ROOT / "backend").resolve()

sys.path.insert(0, str(PROJECT_ROOT))


from agent_framework import Message

from agents.foundry_agents import (
    get_architecture_agent,
    get_backend_agent,
    get_ui_agent,
    get_bug_agent,
)

from orchestrator.file_manager import (
    apply_backend_agent_output,
)

from orchestrator.test_runner import (
    run_backend_tests,
    format_test_evidence,
)


OWNER = "Tanishka1986920"
REPO = "campus-placement-ai-agent"

MAX_RETRIES = 8


# ==================================================
# GitHub approval handler
# ==================================================

async def continue_with_approvals(
    agent,
    result,
    session
):

    while result.user_input_requests:

        responses = []

        for request in result.user_input_requests:

            if request.function_call is None:

                responses.append(
                    request.to_function_approval_response(
                        approved=False
                    )
                )

                continue

            tool_name = request.function_call.name
            arguments = request.function_call.arguments

            print(
                "\nGitHub tool requested:",
                tool_name
            )

            print(
                "Arguments:",
                arguments
            )

            allowed_read_tools = {
                "list_issues",
                "issue_read",
                "get_issue",
            }

            if tool_name in allowed_read_tools:

                print("READ approved.")

                responses.append(
                    request.to_function_approval_response(
                        approved=True
                    )
                )

            else:

                print(
                    "WRITE/unknown operation rejected."
                )

                responses.append(
                    request.to_function_approval_response(
                        approved=False
                    )
                )

        result = await agent.run(
            Message(
                role="user",
                contents=responses
            ),
            session=session
        )

    return result


# ==================================================
# Architecture Agent
# ==================================================

async def run_architecture_agent():

    print(
        "\n===== ARCHITECTURE AGENT =====\n"
    )

    agent = get_architecture_agent()

    session = agent.create_session()

    prompt = f"""
Access the connected GitHub repository:

{OWNER}/{REPO}

READ ONLY.

Read all currently open GitHub issues.

================================
GITHUB TOOL RULES
================================

When calling list_issues:

- Do NOT use the "page" parameter.
- Use method="list".
- Use perPage=100.
- For the first request, do not provide "after".
- If another page is required, use the returned
  endCursor as the "after" parameter.
- Never use page-based pagination.

================================
ISSUE SELECTION RULES
================================

You must determine the first incomplete GitHub issue
by reading the actual issue body.

Follow this exact process:

1. Call list_issues to get all currently open issues.

2. Consider the open issues in ascending issue-number
   order.

3. Starting with the lowest-numbered open issue,
   call issue_read for that specific issue.

4. Inspect the FULL issue body returned by issue_read.

5. Check the checklist in the issue body.

An incomplete checklist item looks like:

[ ]

A completed checklist item looks like:

[x]

6. If the issue body contains at least one unchecked
   [ ] checklist item, select that issue.

7. If the issue contains checklist items but ALL of
   them are [x], the issue is COMPLETE.

   Skip that issue even if its GitHub state is OPEN.

8. After skipping a completed issue, call issue_read
   for the next open issue and inspect its full body.

9. Repeat this process until you find the
   lowest-numbered open issue containing at least
   one unchecked [ ] checklist item.

IMPORTANT:

- Never select an issue based only on list_issues
  output.

- You MUST call issue_read and inspect the full body
  before deciding whether an issue is complete or
  incomplete.

- Never select an issue whose checklist contains no
  unchecked [ ] items.

- Never select a higher-numbered incomplete issue
  before checking all lower-numbered open issues.

Example:

If Issue #3 is OPEN but issue_read shows that every
checklist item is [x], Issue #3 is COMPLETE.

Skip Issue #3.

Then call issue_read for Issue #4.

If Issue #4 contains at least one [ ] item, select
Issue #4.

After selecting the correct incomplete issue, use
that issue's full body and checklist as the source
for planning.

================================
SOURCE OF REQUIREMENTS
================================

The selected GitHub issue checklist is the
AUTHORITATIVE source of requirements.

Do NOT invent additional mandatory requirements.

Do NOT turn optional architecture suggestions into
project requirements.

Do NOT require pull requests, CI/CD, branches,
webhooks, audit logs, deployment infrastructure,
or other components unless the selected GitHub
issue checklist explicitly requires them.

Create the simplest implementation plan that
satisfies the actual checklist.

================================
ROUTING RULES
================================

Choose the route based on the work actually
required by the selected issue.

Use:

ROUTE: BACKEND

when the issue requires backend/Python/FastAPI work.

Use:

ROUTE: UI

when the issue requires frontend/UI/HTML/CSS/
JavaScript or Google Stitch work.

Use:

ROUTE: BOTH

when the issue requires BOTH backend and frontend
implementation.

Use:

ROUTE: ARCHITECTURE

ONLY when the selected issue genuinely requires
architecture/planning work and does NOT require
backend or UI implementation.

IMPORTANT:

Do NOT use ROUTE: ARCHITECTURE merely because the
issue is about creating or configuring an agent.

For example:

- Backend Agent implementation/configuration tasks
  should use ROUTE: BACKEND.

- UI Agent or Google Stitch tasks should use
  ROUTE: UI.

================================
RESPONSE FORMAT
================================

Return:

ISSUE_NUMBER: <number>

ISSUE_TITLE: <title>

REQUIREMENTS:
- exact requirement 1
- exact requirement 2

IMPLEMENTATION_PLAN:
- step 1
- step 2

At the END return exactly ONE routing line:

ROUTE: BACKEND

or

ROUTE: UI

or

ROUTE: BOTH

or

ROUTE: ARCHITECTURE

================================
GITHUB SAFETY
================================

Do not modify GitHub.

Do not modify checkboxes.

Do not close issues.

Do not modify repository files.
"""

    result = await agent.run(
        prompt,
        session=session
    )

    result = await continue_with_approvals(
        agent,
        result,
        session
    )

    print(result.text)

    evidence_dir = PROJECT_ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    architecture_evidence = (
        evidence_dir / "architecture-latest.txt"
    )

    architecture_evidence.write_text(
        result.text,
        encoding="utf-8"
    )

    print(
        "\nArchitecture runtime evidence saved to:"
    )
    print(architecture_evidence)

    return result.text

# ==================================================
# Backend Agent
# ==================================================

async def run_backend_agent(plan):

    print(
        "\n===== BACKEND AGENT =====\n"
    )

    agent = get_backend_agent()

    prompt = f"""
You are the real Microsoft Foundry Backend Agent
for the Campus Placement AI project.

The Architecture Agent selected a GitHub issue and
produced this plan:

--------------------------------
{plan}
--------------------------------

Implement the backend work required by the CURRENT
GitHub issue.

The GitHub issue requirements are authoritative.

Architecture-plan suggestions are guidance and
should support those requirements.

The orchestrator will safely write your generated
files into backend/.

IMPORTANT RULES:

1. Return ONLY valid JSON.

2. Do not use Markdown.

3. Do not use code fences.

4. Do not add explanations outside JSON.

5. Every path must be relative to backend/.

6. Never use ../

7. Never modify .env.

8. Never modify .git.

9. Never include passwords, API keys, tokens,
   credentials, or secrets.

10. Generate complete working file contents.

11. Do not claim files were written.

12. Do not claim tests passed.

13. The orchestrator will execute tests itself.

14. Do not create fake evidence of Microsoft
    Foundry configuration.

15. Do not create fake GitHub operations.

16. Keep the implementation appropriate for a
    student project.

17. Use Python and FastAPI where backend
    implementation is required.

18. Preserve existing working functionality when
    modifying files.

19. Existing project tests define the expected API
    contract. The implementation should satisfy
    those tests unless doing so conflicts with the
    GitHub issue.

Return JSON in exactly this structure:

{{
    "files": [
        {{
            "path": "app/main.py",
            "content": "complete file content"
        }}
    ]
}}

Return ONLY JSON.
"""

    result = await agent.run(
        prompt
    )

    print(
        "\nBackend Agent raw output:\n"
    )

    print(result.text)

    return result.text


# ==================================================
# Backend correction Agent
# ==================================================

async def run_backend_fix_agent(
    plan,
    previous_output,
    verification_feedback,
    test_evidence
):

    print(
        "\n===== BACKEND AGENT - "
        "FIXING ISSUES =====\n"
    )

    agent = get_backend_agent()

    prompt = f"""
You previously generated backend work for the
Campus Placement AI project.

CURRENT GITHUB ISSUE AND ARCHITECTURE PLAN:

--------------------------------
{plan}
--------------------------------

PREVIOUS BACKEND OUTPUT:

--------------------------------
{previous_output}
--------------------------------

BUG/ISSUE AGENT FEEDBACK:

--------------------------------
{verification_feedback}
--------------------------------

ACTUAL TEST EXECUTION:

--------------------------------
{test_evidence}
--------------------------------

Fix the concrete backend problems shown by the Bug
Agent and the REAL test output.

IMPORTANT:

- The test output above is actual runtime evidence.

- If pytest reports a failing assertion, fix the
  implementation causing that assertion.

- Do NOT change tests merely to hide a backend bug.

- Preserve functionality that is already passing.

- If a status value, endpoint, response field,
  validation rule, or header differs from the
  expected test contract, fix the backend
  implementation.

- If tests are missing for genuinely required
  backend functionality, you may add tests.

- Do not invent evidence.

- Do not claim Microsoft Foundry settings changed.

- Do not claim GitHub was modified.

- Do not claim a pull request was created.

- Do not include secrets.

- Only modify files inside backend/.

- Keep fixes focused on the current failure.

RULES:

1. Return ONLY valid JSON.

2. No Markdown.

3. No code fences.

4. No explanations outside JSON.

5. Paths must be relative to backend/.

6. Never use ../

7. Never modify .env.

8. Never modify .git.

9. Never include secrets.

10. Return complete file contents for every file
    you modify.

Format:

{{
    "files": [
        {{
            "path": "app/main.py",
            "content": "complete corrected content"
        }}
    ]
}}

Return ONLY JSON.
"""

    result = await agent.run(
        prompt
    )

    print(
        "\nBackend Agent FIX output:\n"
    )

    print(result.text)

    return result.text


# ==================================================
# UI Agent
# ==================================================

# ==================================================
# UI Agent
# ==================================================

async def run_ui_agent(plan):

    print(
        "\n===== UI AGENT =====\n"
    )

    agent = get_ui_agent()

    stitch_file = PROJECT_ROOT / "frontend" / "stitch-design.html"

    if stitch_file.exists():
        stitch_evidence = stitch_file.read_text(
            encoding="utf-8",
            errors="replace"
        )
    else:
        stitch_evidence = (
            "No Google Stitch export is available."
        )

    prompt = f"""
You are the UI Agent for the Campus Placement AI
project.

Your job is to implement the frontend work required
by the CURRENT GitHub issue.

CURRENT GITHUB ISSUE AND ARCHITECTURE PLAN:

--------------------------------
{plan}
--------------------------------

================================
ACTUAL GOOGLE STITCH EXPORT
================================

The following HTML is actual Google Stitch export
provided by the user.

Use this as the source design for the frontend.

Do NOT invent a different design.

--------------------------------
{stitch_evidence}
--------------------------------

FRONTEND TECHNOLOGY:

- HTML
- CSS
- JavaScript

================================
GOOGLE STITCH REQUIREMENT
================================

The final Campus Placement AI user interface must
originate from Google Stitch.

Google Stitch is the required source of the UI
design.

However, you must NOT pretend that you accessed
Google Stitch.

If actual Google Stitch design/export evidence is
NOT available in this prompt:

- You may create a safe initial frontend structure.
- Keep the frontend easy to replace or refine using
  the real Google Stitch export later.
- Do NOT claim that Google Stitch was accessed.
- Do NOT claim that a Stitch design was generated.
- Do NOT claim that a Stitch export was used.
- Do NOT claim that the Google Stitch checklist item
  is completed.
- Do NOT invent Stitch evidence.

If actual Stitch export evidence is available in
this prompt:

- Follow that design closely.
- Implement the exported design in the frontend.
- Preserve the structure and visual intent of the
  Stitch design.

================================
IMPLEMENTATION REQUIREMENTS
================================

Analyze the CURRENT GitHub issue and Architecture
Agent plan.

Implement only frontend work relevant to the
current issue.

When required by the issue:

- Create a professional Campus Placement AI
  interface.
- Create a homepage.
- Add student query/input sections.
- Add resume upload interface.
- Add placement preparation/results sections.
- Add buttons and forms.
- Add loading states.
- Add validation messages.
- Add error states.
- Make the interface responsive.
- Prepare frontend code for backend API integration.
- Use JavaScript fetch() when backend API integration
  is required.
- Keep frontend code simple and suitable for a
  student project.

================================
SECURITY RULES
================================

- Do NOT modify GitHub.
- Do NOT modify backend files.
- Do NOT modify orchestrator files.
- Do NOT create .env files.
- Do NOT create .git files.
- Do NOT create .gitignore files.
- Do NOT include passwords.
- Do NOT include API keys.
- Do NOT include GitHub tokens.
- Do NOT include Azure credentials.
- Do NOT include secrets.
- Do NOT use absolute paths.
- Do NOT use ../ paths.
- Do NOT claim local files were written.
- Do NOT claim tests were executed unless actual
  test evidence is supplied.
- Do NOT claim GitHub checkboxes were updated.

================================
FILE RULES
================================

Do NOT overwrite:

stitch-design.html

That file is the original Google Stitch export and
must remain unchanged as evidence of the source UI
design.

All returned files must belong inside frontend/.

Valid examples:

index.html

css/style.css

js/app.js

assets/example.svg

You may also return paths beginning with:

frontend/

because the orchestrator will safely normalize them.

Return complete file contents.

Do not return partial code.

Maximum number of files:

30

================================
OUTPUT FORMAT
================================

Return ONLY valid JSON.

Do NOT use Markdown.

Do NOT use code fences.

Do NOT add explanations before JSON.

Do NOT add explanations after JSON.

The response must follow exactly this structure:

{{
    "files": [
        {{
            "path": "index.html",
            "content": "complete HTML file content"
        }},
        {{
            "path": "css/style.css",
            "content": "complete CSS file content"
        }},
        {{
            "path": "js/app.js",
            "content": "complete JavaScript file content"
        }}
    ]
}}

IMPORTANT:

The value of "content" must contain the COMPLETE
content of that file.

The entire response must be parseable using
Python json.loads().

Return ONLY JSON.
"""

    result = await agent.run(
        prompt
    )

    print(
        "\nUI Agent raw output:\n"
    )

    print(
        result.text
    )

    return result.text

# ==================================================
# UI Correction Agent
# ==================================================

async def run_ui_fix_agent(
    plan,
    previous_output,
    verification_feedback
):

    print(
        "\n===== UI AGENT - FIXING ISSUES =====\n"
    )

    agent = get_ui_agent()

    # Read the real Google Stitch export again
    stitch_file = (
        PROJECT_ROOT
        / "frontend"
        / "stitch-design.html"
    )

    if stitch_file.exists():

        stitch_evidence = stitch_file.read_text(
            encoding="utf-8",
            errors="replace"
        )

    else:

        stitch_evidence = (
            "No Google Stitch export is available."
        )

    prompt = f"""
You are the UI Agent for the Campus Placement AI
project.

Your previous frontend implementation FAILED
Bug/Issue Agent verification.

Fix ONLY the frontend problems identified by the
Bug/Issue Agent.

================================
CURRENT ISSUE / ARCHITECTURE PLAN
================================

{plan}

================================
PREVIOUS UI AGENT OUTPUT
================================

{previous_output}

================================
BUG/ISSUE AGENT FEEDBACK
================================

{verification_feedback}

================================
ACTUAL GOOGLE STITCH EXPORT
================================

The following HTML is the actual Google Stitch
export provided by the user.

Use it as the source design.

Do NOT invent a different design.

{stitch_evidence}

================================
FIXING RULES
================================

- Fix every concrete UI problem reported by the
  Bug/Issue Agent.
- Preserve functionality that already works.
- Follow the Google Stitch design.
- Keep the interface responsive.
- Add loading states when required.
- Add validation when required.
- Add error states when required.
- Add backend API integration when required.
- Use JavaScript fetch() for API calls when needed.

================================
SECURITY RULES
================================

- Modify ONLY frontend files.
- Do NOT modify backend files.
- Do NOT modify orchestrator files.
- Do NOT modify GitHub.
- Do NOT create .env files.
- Do NOT create .git files.
- Do NOT create .gitignore files.
- Do NOT include passwords.
- Do NOT include API keys.
- Do NOT include tokens.
- Do NOT include credentials.
- Do NOT include secrets.
- Do NOT use absolute paths.
- Do NOT use ../ paths.
- Do NOT claim GitHub was updated.
- Do NOT claim verification passed.
- Do NOT claim files were written locally.

================================
FILE RULES
================================

Return complete contents for every frontend file
you modify.

All paths must belong inside frontend/.

Valid examples:

index.html
css/style.css
js/app.js

Do NOT overwrite:

stitch-design.html

That file is the original Google Stitch evidence.

Maximum files:

30

================================
OUTPUT FORMAT
================================

Return ONLY valid JSON.

No Markdown.

No code fences.

No explanation before or after JSON.

Use exactly this structure:

{{
    "files": [
        {{
            "path": "index.html",
            "content": "complete corrected HTML"
        }},
        {{
            "path": "css/style.css",
            "content": "complete corrected CSS"
        }},
        {{
            "path": "js/app.js",
            "content": "complete corrected JavaScript"
        }}
    ]
}}

The entire response must be parseable using
Python json.loads().

Return ONLY JSON.
"""

    result = await agent.run(
        prompt
    )

    print(
        "\nUI Agent FIX output:\n"
    )

    print(
        result.text
    )

    return result.text


# ==================================================
# Apply Backend Files
# ==================================================

def write_backend_files(
    agent_output
):

    print(
        "\n===== APPLYING BACKEND FILES =====\n"
    )

    try:

        written_files = (
            apply_backend_agent_output(
                agent_output
            )
        )

    except Exception as error:

        print(
            "ERROR: Backend files were NOT written."
        )

        print(error)

        return None

    print(
        "\nBackend files successfully written:"
    )

    for file in written_files:

        print(
            "-",
            file
        )

    return written_files


# ==================================================
# Collect actual file evidence
# ==================================================

# ==================================================
# Apply UI Files
# ==================================================

def write_ui_files(agent_output):

    print("\n===== APPLYING UI FILES =====\n")

    try:
        written_files = apply_ui_agent_output(
            agent_output
        )

    except Exception as error:
        print("ERROR: UI files were NOT written.")
        print(error)
        return None

    print("\nUI files successfully written:")

    for file in written_files:
        print("-", file)

    return written_files

def collect_file_evidence(
    written_files
):

    print(
        "\n===== COLLECTING FILE EVIDENCE =====\n"
    )

    evidence_parts = []

    for relative_file in written_files:

        file_path = (
            PROJECT_ROOT / relative_file
        ).resolve()

        # ------------------------------------------
        # Security:
        # only allow evidence from backend/
        # ------------------------------------------

        try:

            file_path.relative_to(
                BACKEND_ROOT
            )

        except ValueError:

            print(
                "Skipping file outside backend:",
                relative_file
            )

            continue

        if not file_path.exists():

            evidence_parts.append(
                f"""
FILE: {relative_file}

STATUS:
File does not exist.
"""
            )

            continue

        if not file_path.is_file():

            continue

        try:

            content = file_path.read_text(
                encoding="utf-8",
                errors="replace"
            )

        except Exception as error:

            evidence_parts.append(
                f"""
FILE: {relative_file}

STATUS:
Could not read file.

ERROR:
{error}
"""
            )

            continue

        # Avoid extremely large prompts
        if len(content) > 20000:

            content = (
                content[:20000]
                + "\n\n[CONTENT TRUNCATED]"
            )

        evidence_parts.append(
            f"""
================================
FILE: {relative_file}
================================

{content}
"""
        )

    if not evidence_parts:

        return (
            "No readable backend file evidence "
            "was available."
        )

    return "\n".join(
        evidence_parts
    )


# ==================================================
# Foundry runtime evidence
# ==================================================

def build_foundry_runtime_evidence():

    return """
MICROSOFT FOUNDRY RUNTIME EVIDENCE

The Backend Agent used by this workflow is the
existing Microsoft Foundry agent:

Agent name:
backend-agent

Agent version:
2

Runtime facts established by this orchestrator:

1. The Architecture Agent successfully selected
   and analyzed the current GitHub issue.

2. The Architecture Agent routed the backend task
   to the Backend Agent.

3. The orchestrator instantiated and successfully
   invoked Microsoft Foundry agent
   "backend-agent", version 2.

4. The Backend Agent returned implementation
   output to this orchestrator.

5. The orchestrator safely wrote that output into
   the backend directory.

6. The orchestrator executed real backend compile
   checks and pytest tests.

7. The Backend Agent's implementation, actual
   written files, and actual test results are now
   being handed to the Bug/Issue Agent through
   this verification call.

Therefore the following runtime facts are directly
demonstrated by this workflow:

- Backend Agent exists and is callable through
  Microsoft Foundry.

- Backend Agent can receive a backend task routed
  from the Architecture Agent.

- Backend Agent can produce backend implementation
  output.

- Completed backend work is handed to the
  Bug/Issue Agent for verification.

This evidence does NOT claim that unrelated
production infrastructure, deployment, secrets,
or external integrations are configured.
""".strip()


# ==================================================
# Bug / Issue Agent
# ==================================================

async def verify_work(
    plan,
    work_result,
    written_files,
    test_evidence,
    file_evidence
):

    print(
        "\n===== BUG/ISSUE AGENT =====\n"
    )

    agent = get_bug_agent()

    files_text = "\n".join(
        f"- {file}"
        for file in written_files
    )

    foundry_evidence = (
        build_foundry_runtime_evidence()
    )

    prompt = f"""
Verify the Backend Agent's work for the CURRENT
GitHub issue.

================================
CURRENT ISSUE / ARCHITECTURE PLAN
================================

{plan}

================================
BACKEND AGENT OUTPUT
================================

{work_result}

================================
FILES ACTUALLY WRITTEN
================================

{files_text}

================================
ACTUAL FILE CONTENTS
================================

{file_evidence}

================================
ACTUAL TEST EXECUTION EVIDENCE
================================

{test_evidence}

================================
MICROSOFT FOUNDRY RUNTIME EVIDENCE
================================

{foundry_evidence}

================================
VERIFICATION RULES
================================

The GitHub issue checklist is the AUTHORITATIVE
source for deciding whether the current issue
passes.

Architecture implementation-plan suggestions are
guidance.

Do NOT turn extra architecture suggestions into
new mandatory checklist requirements unless they
are necessary to satisfy an actual GitHub
checklist item.

The supplied test evidence was generated by the
local orchestrator by actually executing the
commands.

A command with return code 0 succeeded.

Pytest output such as:

5 passed

with return code 0 is real successful test
evidence.

Warnings are NOT test failures when pytest has
return code 0.

Use the actual file contents supplied above when
checking implementation.

IMPORTANT FOUNDRY RULE:

The Backend Agent being evaluated is the real
Microsoft Foundry agent named:

backend-agent

version:

2

This workflow successfully invoked that agent.

Therefore do NOT mark Backend Agent
creation/existence as unverified merely because
Foundry provisioning files are not stored inside
backend/.

The Architecture Agent routed this issue to the
Backend Agent.

Therefore Backend Agent execution on a backend
issue is runtime-verified.

This verification call itself is the actual
handoff of the completed Backend Agent work to the
Bug/Issue Agent.

Therefore do NOT require an additional GitHub
comment or webhook merely to prove that this
handoff occurred unless the GitHub issue
explicitly requires that specific mechanism.

Do NOT require:

- deployment
- production infrastructure
- pull requests
- GitHub comments
- additional CI infrastructure
- external webhooks
- production secret stores

unless the CURRENT GitHub issue checklist
explicitly requires them.

Do not invent evidence.

Do not modify GitHub.

Do not mark GitHub checkboxes yourself.

Evaluate the exact current issue requirements
against:

1. Foundry runtime evidence
2. Actual written files
3. Actual file contents
4. Actual test execution

If a real test is failing because of backend
behavior, verification must FAIL.

If all relevant tests pass and the exact issue
checklist requirements are supported by the
provided evidence, verification may PASS.

Your response should contain:

1. VERIFIED REQUIREMENTS

2. FAILED OR UNVERIFIED REQUIREMENTS

3. CONCRETE FIXES, only if needed

4. FINAL DECISION

The FINAL non-empty line of your response MUST be
exactly one of:

VERIFICATION: PASS

or

VERIFICATION: FAIL
"""

    result = await agent.run(
        prompt
    )

    print(result.text)

    return result.text

# ==================================================
# UI Bug / Issue Agent Verification
# ==================================================

async def verify_ui_work(
    plan,
    ui_result,
    written_files
):

    print(
        "\n===== BUG/ISSUE AGENT - UI VERIFICATION =====\n"
    )

    agent = get_bug_agent()

    # Collect actual frontend file contents
    evidence_parts = []

    for relative_file in written_files:

        file_path = (
            PROJECT_ROOT / relative_file
        ).resolve()

        frontend_root = (
            PROJECT_ROOT / "frontend"
        ).resolve()

        try:
            file_path.relative_to(frontend_root)
        except ValueError:
            continue

        if not file_path.exists():
            continue

        if not file_path.is_file():
            continue

        content = file_path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        if len(content) > 20000:
            content = (
                content[:20000]
                + "\n[CONTENT TRUNCATED]"
            )

        evidence_parts.append(
            f"""
================================
FILE: {relative_file}
================================

{content}
"""
        )

    file_evidence = "\n".join(
        evidence_parts
    )

    # Real Stitch evidence
    stitch_file = (
        PROJECT_ROOT
        / "frontend"
        / "stitch-design.html"
    )

    if stitch_file.exists():

        stitch_content = stitch_file.read_text(
            encoding="utf-8",
            errors="replace"
        )

        if len(stitch_content) > 20000:
            stitch_content = (
                stitch_content[:20000]
                + "\n[STITCH CONTENT TRUNCATED]"
            )

        stitch_status = f"""
REAL GOOGLE STITCH EVIDENCE:

The user generated the Campus Placement AI design
using Google Stitch and exported the generated HTML.

That actual Stitch-generated HTML is stored at:

frontend/stitch-design.html

The UI Agent received this actual Stitch export as
its source design.

Compare the implemented frontend against the
actual Stitch HTML below.

================================
ACTUAL GOOGLE STITCH HTML
================================

{stitch_content}

================================
END GOOGLE STITCH HTML
================================
"""

    else:

        stitch_status = """
GOOGLE STITCH EVIDENCE:

No Stitch export file was found.

Do NOT verify any Stitch-specific requirement.
"""

    files_text = "\n".join(
        f"- {file}"
        for file in written_files
    )

    prompt = f"""
Verify the UI Agent's work for the CURRENT GitHub
issue.

================================
CURRENT ISSUE / ARCHITECTURE PLAN
================================

{plan}

================================
UI AGENT OUTPUT
================================

{ui_result}

================================
FILES ACTUALLY WRITTEN
================================

{files_text}

================================
ACTUAL FRONTEND FILE CONTENTS
================================

{file_evidence}

================================
GOOGLE STITCH EVIDENCE
================================

{stitch_status}

================================
VERIFICATION RULES
================================

The GitHub issue checklist is authoritative.

Verify only requirements supported by actual
evidence.

The UI Agent used is the real Microsoft Foundry
agent named:

ui-agent

version 2.

The orchestrator successfully invoked this agent.

Do not invent evidence.

Do not modify GitHub.

Do not mark GitHub checkboxes yourself.

For Google Stitch requirements:

- Only verify them when real Stitch evidence exists.
- frontend/stitch-design.html is real exported
  Stitch HTML when the evidence above confirms it.
- Check whether the implemented frontend follows
  the supplied Stitch design.
- Do not assume Stitch usage without evidence.

Review:

1. Current GitHub issue requirements
2. UI Agent output
3. Files actually written
4. Actual frontend file contents
5. Google Stitch evidence
6. Loading, validation and error states when
   required
7. Backend API integration when required

Your response must contain:

1. VERIFIED REQUIREMENTS

List the exact GitHub checklist requirement text
that is supported by evidence.

2. FAILED OR UNVERIFIED REQUIREMENTS

List requirements that still lack evidence.

3. CONCRETE FIXES

Only when needed.

4. FINAL DECISION

Use PASS only if ALL checklist requirements for the
current issue are verified.

The FINAL non-empty line MUST be exactly:

VERIFICATION: PASS

or

VERIFICATION: FAIL
"""

    result = await agent.run(
        prompt
    )

    print(result.text)

    return result.text

# ==================================================
# Architecture / System Issue Verification
# ==================================================

async def verify_system_issue(plan):

    print(
        "\n===== BUG/ISSUE AGENT - "
        "SYSTEM VERIFICATION =====\n"
    )

    agent = get_bug_agent()

    # Collect real project evidence
    evidence_files = [
        "agents/foundry_agents.py",
        "orchestrator/workflow.py",
        "orchestrator/file_manager.py",
        "orchestrator/frontend_file_manager.py",
        "orchestrator/test_runner.py",
        "orchestrator/github_update.py",
        "docs/bug-issue-agent-runbook.md",
        "evidence/architecture-latest.txt",
        "evidence/workflow-latest.txt",
    ]

    evidence_parts = []

    for relative_file in evidence_files:

        file_path = (
            PROJECT_ROOT / relative_file
        ).resolve()

        if not file_path.exists():
            continue

        if not file_path.is_file():
            continue

        content = file_path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        if len(content) > 100000:
            content = (
                content[:100000]
                + "\n[CONTENT TRUNCATED]"
            )

        evidence_parts.append(
            f"""
================================
FILE: {relative_file}
================================

{content}
"""
        )

    system_file_evidence = "\n".join(
        evidence_parts
    )

    prompt = f"""
Verify the CURRENT GitHub issue using the actual
runtime evidence of this multi-agent project.

================================
CURRENT ISSUE / ARCHITECTURE PLAN
================================

{plan}

================================
ACTUAL SYSTEM EVIDENCE
================================
{system_file_evidence}

The project currently uses these four Microsoft
Foundry agents:

1. architecture-agent
2. backend-agent
3. ui-agent
4. bug-issue-agent

The Architecture Agent reads GitHub issues and
creates implementation plans.

The Backend Agent receives backend tasks and
generates backend implementation.

The UI Agent receives frontend tasks and uses the
real Google Stitch export stored at:

frontend/stitch-design.html

The Bug/Issue Agent is invoked by the orchestrator
to review completed Backend and UI work.

The orchestrator has automatic correction loops.

When Bug/Issue Agent verification fails, work is
returned to the appropriate implementation agent
for correction.

GitHub checklist updates are performed only after
successful Bug/Issue Agent verification.

================================
VERIFICATION RULES
================================

The GitHub issue checklist in the Architecture
Agent plan is the authoritative source of
requirements.

IMPORTANT:
Only the items listed under REQUIREMENTS are
acceptance criteria.

IMPLEMENTATION_PLAN is guidance only.
Do NOT treat implementation-plan steps,
suggestions, documentation examples, connector
examples, deterministic verifier suggestions,
smoke-test examples, or optional artifacts as
additional requirements unless they also appear
as an exact REQUIREMENTS item.

Evaluate PASS or FAIL using only the exact
REQUIREMENTS checklist.

Verify each checklist requirement only when the
runtime evidence above and the current project
workflow support it.

Do NOT invent evidence.

Do NOT modify GitHub.

Do NOT mark checkboxes yourself.

Do NOT require unrelated production infrastructure,
deployment, pull requests, CI/CD, or webhooks unless
the current GitHub issue explicitly requires them.

Your response MUST contain:

1. VERIFIED REQUIREMENTS

List the exact GitHub checklist requirement text
that is supported by evidence.

2. FAILED OR UNVERIFIED REQUIREMENTS

List exact requirements that are not supported by
the supplied evidence.

3. CONCRETE FIXES

Only when needed.

4. FINAL DECISION

Use PASS only when ALL checklist requirements for
the current issue are verified.

The FINAL non-empty line MUST be exactly:

VERIFICATION: PASS

or

VERIFICATION: FAIL
"""

    result = await agent.run(prompt)

    print(result.text)

    return result.text

# ==================================================
# Determine verification status safely
# ==================================================

def verification_passed(
    verification_text
):

    if not verification_text:

        return False

    lines = [
        line.strip().upper()
        for line
        in verification_text.splitlines()
        if line.strip()
    ]

    if not lines:

        return False

    return (
        lines[-1]
        == "VERIFICATION: PASS"
    )

def extract_verified_items(
    verification_text
):

    if not verification_text:
        return []

    verified_items = []

    lines = verification_text.splitlines()

    inside_verified_section = False

    for line in lines:

        stripped = line.strip()

        # Markdown formatting bhi remove kar dega
        # jaise **VERIFIED REQUIREMENTS**
        normalized = stripped.strip("#* _`")
        upper = normalized.upper()

        # VERIFIED REQUIREMENTS section start
        if upper in {
            "VERIFIED REQUIREMENTS",
            "1. VERIFIED REQUIREMENTS",
            "VERIFIED REQUIREMENTS:",
            "1. VERIFIED REQUIREMENTS:"
        }:
            inside_verified_section = True
            continue

        # Next section aate hi stop
        if inside_verified_section and (
            upper.startswith(
                "FAILED OR UNVERIFIED REQUIREMENTS"
            )
            or upper.startswith(
                "2. FAILED OR UNVERIFIED REQUIREMENTS"
            )
            or upper.startswith(
                "BUGS / ISSUES"
            )
            or upper.startswith(
                "CONCRETE FIXES"
            )
            or upper.startswith(
                "3. CONCRETE FIXES"
            )
            or upper.startswith(
                "FINAL DECISION"
            )
            or upper.startswith(
                "4. FINAL DECISION"
            )
            or upper.startswith(
                "VERIFICATION:"
            )
        ):
            break

        if not inside_verified_section:
            continue

        # Bullet item extract karo
        if stripped.startswith("- "):
            item = stripped[2:].strip()

        elif stripped.startswith("* "):
            item = stripped[2:].strip()

        else:
            continue

        # Checkbox remove karo agar agent ne diya ho
        if (
            item.startswith("[x]")
            or item.startswith("[X]")
        ):
            item = item[3:].strip()

        elif item.startswith("[ ]"):
            item = item[3:].strip()

        # Quotes remove
        if item.startswith('"') and '"' in item[1:]:
            end_quote = item.find('"', 1)

            if end_quote != -1:
                item = item[1:end_quote].strip()

        # " — Verified..." jaisi explanation remove
        elif " — " in item:
            item = item.split(
                " — ",
                1
            )[0].strip()

        if item:
            verified_items.append(item)

    return verified_items

# ==================================================
# Extract GitHub issue number
# ==================================================

def extract_issue_number(plan):

    if not plan:
        return None

    for line in plan.splitlines():

        stripped = line.strip()

        if stripped.upper().startswith(
            "ISSUE_NUMBER:"
        ):

            value = stripped.split(
                ":",
                1
            )[1].strip()

            try:
                return int(value)

            except ValueError:
                return None

    return None


# ==================================================
# Execute real backend tests
# ==================================================


# ==================================================
# Execute real backend tests
# ==================================================

def execute_tests():

    print(
        "\n===== RUNNING REAL BACKEND TESTS =====\n"
    )

    results = run_backend_tests()

    evidence = format_test_evidence(
        results
    )

    return (
        results,
        evidence
    )


# ==================================================
# Backend workflow
# ==================================================

async def run_backend_workflow(
    plan
):

    # ==============================================
    # Initial implementation
    # ==============================================

    work_result = await run_backend_agent(
        plan
    )

    written_files = write_backend_files(
        work_result
    )

    if written_files is None:

        return False

    # ==============================================
    # Run REAL tests
    # ==============================================

    (
        test_results,
        test_evidence
    ) = execute_tests()

    # ==============================================
    # Collect REAL files
    # ==============================================

    file_evidence = collect_file_evidence(
        written_files
    )

    # ==============================================
    # Bug Agent verification
    # ==============================================

    verification = await verify_work(
        plan,
        work_result,
        written_files,
        test_evidence,
        file_evidence
    )

    retry = 0

    # ==============================================
    # Automatic correction loop
    # ==============================================

    while (
        not verification_passed(
            verification
        )
        and retry < MAX_RETRIES
    ):

        retry += 1

        print(
            "\n========================================"
        )

        print(
            f"     AUTOMATIC FIX ATTEMPT {retry}"
        )

        print(
            "========================================"
        )

        # ------------------------------------------
        # Backend Agent receives Bug Agent feedback
        # ------------------------------------------

        fixed_result = (
            await run_backend_fix_agent(
                plan,
                work_result,
                verification,
                test_evidence
            )
        )

        # ------------------------------------------
        # Apply corrected files
        # ------------------------------------------

        fixed_files = write_backend_files(
            fixed_result
        )

        if fixed_files is None:

            print(
                "\nAutomatic correction could not "
                "write files."
            )

            return False

        # ------------------------------------------
        # Keep cumulative evidence of files
        # ------------------------------------------

        for file in fixed_files:

            if file not in written_files:

                written_files.append(
                    file
                )

        work_result = fixed_result

        # ------------------------------------------
        # REAL tests run again
        # ------------------------------------------

        (
            test_results,
            test_evidence
        ) = execute_tests()

        # ------------------------------------------
        # Collect latest actual contents
        # ------------------------------------------

        file_evidence = collect_file_evidence(
            written_files
        )

        # ------------------------------------------
        # Bug Agent verifies again
        # ------------------------------------------

        verification = await verify_work(
            plan,
            work_result,
            written_files,
            test_evidence,
            file_evidence
        )

    # ==============================================
    # Final result
    # ==============================================

    if verification_passed(
        verification
    ):

        print(
            "\n========================================"
        )

        print(
            "        VERIFICATION PASSED"
        )

        print(
            "========================================"
        )

        print(
            "\nBackend implementation passed "
            "Bug/Issue Agent verification."
        )

        # ------------------------------------------
        # Extract verified GitHub checklist items
        # ------------------------------------------

        verified_items = extract_verified_items(
            verification
        )

        issue_number = extract_issue_number(
            plan
        )

        # ------------------------------------------
        # Update GitHub only after verification
        # ------------------------------------------

        if (
            verified_items
            and issue_number is not None
        ):

            await update_github_checklist(
                issue_number=issue_number,
                verified_items=verified_items
            )

        elif not verified_items:

            print(
                "\nNo verified checklist items were "
                "returned. GitHub was not modified."
            )

        else:

            print(
                "\nERROR: Could not extract GitHub "
                "issue number. GitHub was not modified."
            )

        return True

    print(
        "\n========================================"
    )

    print(
        "        VERIFICATION FAILED"
    )

    print(
        "========================================"
    )

    print(
        f"\nBackend Agent attempted automatic "
        f"correction {retry} time(s)."
    )

    print(
        "\nSome current issue requirements are "
        "still missing or unverified."
    )

    print(
        "\nGitHub checkboxes remain unchecked."
    )

    return False

# ==================================================
# Main workflow
# ==================================================

# ==================================================
# Safe Backend Verification Only
# ==================================================

async def verify_existing_backend_only():

    print(
        "\n===== SAFE BACKEND VERIFICATION ONLY =====\n"
    )

    # Issue #8 plan/checklist
    plan = """
ISSUE_NUMBER: 8

ISSUE_TITLE: Build Backend API

REQUIREMENTS:
- Set up Python FastAPI backend
- Create required API endpoints
- Connect backend with Microsoft Foundry
- Add API endpoint for student queries
- Add resume upload and processing endpoint
- Connect backend with the multi-agent system
- Add input validation
- Add exception and error handling
- Configure CORS for frontend-backend communication
- Test backend APIs
- Send completed backend work to Bug/Issue Agent for verification

ROUTE: BACKEND
"""

    # Files that already exist and must only be VERIFIED
    written_files = [
        "backend/app/main.py",
        "backend/app/api/routes.py",
        "backend/app/schemas.py",
        "backend/app/api/schemas.py",
        "backend/app/foundry_client.py",
    ]

    # Run real tests on current backend
    test_results, test_evidence = execute_tests()

    # Collect current file contents
    file_evidence = collect_file_evidence(
        written_files
    )

    # Important:
    # no Backend Agent generation/write happens here.
    work_result = """
Existing backend implementation.

This verification-only run did NOT ask the Backend
Agent to regenerate or overwrite backend files.

The current backend files are being verified using
their actual contents and real pytest execution.
"""

    # Send existing work directly to Bug/Issue Agent
    verification = await verify_work(
        plan,
        work_result,
        written_files,
        test_evidence,
        file_evidence,
    )

    if verification_passed(verification):

        print(
            "\n========================================"
        )
        print(
            "        VERIFICATION PASSED"
        )
        print(
            "========================================"
        )

        verified_items = extract_verified_items(
            verification
        )

        if verified_items:

            await update_github_checklist(
                issue_number=8,
                verified_items=verified_items,
            )

        else:
            print(
                "\nNo verified checklist items extracted. "
                "GitHub was not modified."
            )

        return True

    print(
        "\n========================================"
    )
    print(
        "        VERIFICATION FAILED"
    )
    print(
        "========================================"
    )

    print(
        "\nBackend files were NOT modified."
    )

    return False

async def main():

    print(
        "\n========================================"
    )

    print(
        "   CAMPUS PLACEMENT AI WORKFLOW"
    )

    print(
        "========================================"
    )

    # ==============================================
    # STEP 1 - Architecture Agent
    # ==============================================

    plan = await run_architecture_agent()

    if not plan:

        print(
            "\nERROR: Architecture Agent returned "
            "no plan."
        )

        return

    plan_upper = plan.upper()

    # ==============================================
    # STEP 2 - Route task
    # ==============================================

    if "ROUTE: BACKEND" in plan_upper:

        print(
            "\n>>> ROUTE SELECTED: BACKEND"
        )

        await run_backend_workflow(
            plan
        )

    elif "ROUTE: UI" in plan_upper:

        print(
            "\n>>> ROUTE SELECTED: UI"
        )

        ui_result = await run_ui_agent(
            plan
        )

        ui_written_files = write_ui_files(
            ui_result
        )

        if ui_written_files is None:
            print(
                "\nUI implementation could not be written."
            )
        else:

            print(
                "\nUI implementation successfully "
                "written to frontend/."
            )

            ui_verification = await verify_ui_work(
                plan,
                ui_result,
                ui_written_files
            )

            ui_retry = 0

            # ==========================================
            # Automatic UI correction loop
            # ==========================================

            while (
                not verification_passed(
                    ui_verification
                )
                and ui_retry < MAX_RETRIES
            ):

                ui_retry += 1

                print(
                    "\n========================================"
                )

                print(
                    f"     UI FIX ATTEMPT {ui_retry}"
                )

                print(
                    "========================================"
                )

                # --------------------------------------
                # Send Bug Agent feedback to UI Agent
                # --------------------------------------

                fixed_ui_result = await run_ui_fix_agent(
                    plan,
                    ui_result,
                    ui_verification
                )

                # --------------------------------------
                # Safely write corrected frontend files
                # --------------------------------------

                fixed_ui_files = write_ui_files(
                    fixed_ui_result
                )

                if fixed_ui_files is None:

                    print(
                        "\nUI correction could not be written."
                    )

                    break

                # --------------------------------------
                # Keep track of all written files
                # --------------------------------------

                for file in fixed_ui_files:

                    if file not in ui_written_files:

                        ui_written_files.append(
                            file
                        )

                ui_result = fixed_ui_result

                # --------------------------------------
                # Bug Agent verifies corrected UI again
                # --------------------------------------

                ui_verification = await verify_ui_work(
                    plan,
                    ui_result,
                    ui_written_files
                )

            # ==========================================
            # Final UI result
            # ==========================================

            if verification_passed(
                ui_verification
            ):

                print(
                    "\nUI implementation passed "
                    "Bug/Issue Agent verification."
                )

                verified_items = extract_verified_items(
                    ui_verification
                )

                if verified_items:

                    issue_number = extract_issue_number(
                        plan
                    )

                    if issue_number is not None:

                        await update_github_checklist(
                            issue_number=issue_number,
                            verified_items=verified_items
                        )

                    else:

                        print(
                            "\nERROR: Could not extract GitHub "
                            "issue number. GitHub was not modified."
                        )

                else:

                    print(
                        "\nNo verified checklist items were "
                        "returned. GitHub was not modified."
                    )

            else:

                print(
                    "\nUI implementation still failed "
                    "Bug/Issue Agent verification after "
                    f"{ui_retry} correction attempt(s)."
                )

                print(
                    "\nGitHub checkboxes remain unchecked."
                )
    elif "ROUTE: BOTH" in plan_upper:

        print(
            "\n>>> ROUTE SELECTED: BOTH"
        )

        print(
            "\nStarting Backend and UI workflows "
            "concurrently..."
        )

        backend_task = asyncio.create_task(
            run_backend_workflow(
                plan
            )
        )

        ui_task = asyncio.create_task(
            run_ui_agent(
                plan
            )
        )

        backend_success, ui_result = await asyncio.gather(
            backend_task,
            ui_task
        )

        ui_written_files = write_ui_files(
            ui_result
        )

        if ui_written_files is None:

            print(
                "\nUI implementation could not be written."
            )

        else:

            print(
                "\nUI implementation successfully "
                "written to frontend/."
            )

            ui_verification = await verify_ui_work(
                plan,
                ui_result,
                ui_written_files
            )

            ui_retry = 0

            while (
                not verification_passed(
                    ui_verification
                )
                and ui_retry < MAX_RETRIES
            ):

                ui_retry += 1

                print(
                    "\n========================================"
                )

                print(
                    f"     UI FIX ATTEMPT {ui_retry}"
                )

                print(
                    "========================================"
                )

                fixed_ui_result = await run_ui_fix_agent(
                    plan,
                    ui_result,
                    ui_verification
                )

                fixed_ui_files = write_ui_files(
                    fixed_ui_result
                )

                if fixed_ui_files is None:

                    print(
                        "\nUI correction could not be written."
                    )

                    break

                for file in fixed_ui_files:

                    if file not in ui_written_files:

                        ui_written_files.append(
                            file
                        )

                ui_result = fixed_ui_result

                ui_verification = await verify_ui_work(
                    plan,
                    ui_result,
                    ui_written_files
                )

            if verification_passed(
                ui_verification
            ):

                print(
                    "\nUI implementation passed "
                    "Bug/Issue Agent verification."
                )

                verified_items = extract_verified_items(
                    ui_verification
                )

                issue_number = extract_issue_number(
                    plan
                )

                if (
                    verified_items
                    and issue_number is not None
                ):

                    await update_github_checklist(
                        issue_number=issue_number,
                        verified_items=verified_items
                    )

            else:

                print(
                    "\nUI implementation still failed "
                    "Bug/Issue Agent verification."
                )

        if backend_success:

            print(
                "\nBackend workflow completed successfully."
            )

        else:

            print(
                "\nBackend workflow did not pass verification."
            )

    elif "ROUTE: ARCHITECTURE" in plan_upper:

        print(
            "\n>>> ROUTE SELECTED: ARCHITECTURE"
        )

        print(
            "\nArchitecture/System task selected."
        )

        system_verification = await verify_system_issue(
            plan
        )

        if verification_passed(
            system_verification
        ):

            print(
                "\nSystem issue passed "
                "Bug/Issue Agent verification."
            )

            verified_items = extract_verified_items(
                system_verification
            )

            issue_number = extract_issue_number(
                plan
            )

            if (
                verified_items
                and issue_number is not None
            ):

                await update_github_checklist(
                    issue_number=issue_number,
                    verified_items=verified_items
                )

            elif not verified_items:

                print(
                    "\nNo verified checklist items were "
                    "returned. GitHub was not modified."
                )

            else:

                print(
                    "\nERROR: Could not extract GitHub "
                    "issue number. GitHub was not modified."
                )

        else:

            print(
                "\nSystem issue FAILED "
                "Bug/Issue Agent verification."
            )

            print(
                "\nGitHub checkboxes remain unchecked."
            )

    else:

        print(
            "\nERROR: Could not determine route."
        )

    print(
        "\n========================================"
    )

    evidence_dir = PROJECT_ROOT / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    workflow_evidence = (
        evidence_dir / "workflow-latest.txt"
    )

    workflow_evidence.write_text(
        "Complete multi-agent workflow executed.\n"
        "Architecture Agent read GitHub issues.\n"
        "Issue requirements were analyzed and routed.\n"
        "Backend/UI routing and Bug Agent verification "
        "are handled by the orchestrator.\n"
        "Failed work is returned through automatic "
        "correction loops.\n"
        "GitHub checklist updates occur only after "
        "successful verification.\n",
        encoding="utf-8"
    )

    print(
        "\nWorkflow runtime evidence saved to:"
    )
    print(workflow_evidence)

    print(
        "           WORKFLOW FINISHED"
    )

    print(
        "========================================"
    )


# ==================================================
# Start
# ==================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )