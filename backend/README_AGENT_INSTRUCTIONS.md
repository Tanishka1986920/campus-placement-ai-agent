Resume Analysis / Backend Agent - Developer Instructions

Purpose:
- This explains the responsibilities and capabilities the Backend Agent must perform when running inside Microsoft Foundry or locally for development.

Responsibilities:
- Claim backend GitHub issues labeled with "backend" or matching regex patterns like "resume|backend|api".
- For claimed issues: create a feature branch, implement code, run tests and linters, push branch, and open a PR with a clear template.
- Do not modify issue checkboxes or close issues. Notify the Bug/Issue Agent for verification by leaving a comment on the issue with a verification checklist.

Templates:
- Commit message template: feat(back-end): <short description>\n\nIssue: #<number>\n
- PR template header: Implement <short description> (Issue #<number>)\n\nSummary:\n- What changed\n- How to test\n
- Test criteria example:\n  - Unit tests added for parsing\n  - End-to-end flow: upload resume -> retrieve result\n
Issue routing & guardrails:
- Use issue labels to determine scope: [backend, api, infra, resume]
- Only act on issues NOT already assigned to other agent identities. If issue.assignee exists, do not claim.
- Read-only rule: the agent MUST NOT toggle issue checklist boxes nor close issues. It must add a comment for handoff instead.

Integration points:
- The agent will expose HTTP endpoints for other agents to call at /api/agent/webhook and /api/resume/upload and /api/resume/result/{job_id}
- When work completes, the agent saves artifacts to configured storage and then notifies the Bug/Issue Agent by calling a configured webhook or leaving a GitHub issue comment via API (using secrets from Foundry secret store).

Secrets and storage:
- Do NOT store tokens or keys in repo. Use Foundry secret manager and environment variables: GITHUB_TOKEN, S3_ENDPOINT, S3_KEY, S3_SECRET (names are illustrative).

CI and quality gates:
- Ensure tests run and pass locally. Add linting as required by project standards.

Notes for implementers:
- This file is intentionally non-secret and documents agent behavior. Keep it updated when agent responsibilities change.
