"""
Foundry Agent Configuration Template

This file contains non-secret configuration and instructions for the Backend Agent
that will be created in Microsoft Foundry. Do NOT store secrets or tokens here.
Secrets should be provided by the Foundry secret manager or environment variables at runtime.

Fields:
- agent_name: descriptive name for the Foundry agent
- role: short summary of responsibilities
- permissions: list of required high-level permissions; actual secrets are managed elsewhere
- webhooks: configured endpoints for inter-agent communication (placeholders)

This file is intended to be used by automation when provisioning the Foundry agent.
"""

AGENT_CONFIG = {
    "agent_name": "ResumeAnalysisBackendAgent",
    "role": "Backend agent responsible for implementing resume analysis, FastAPI endpoints, storage and integration points for multi-agent orchestration.",
    "permissions": [
        "github:repo:read",
        "github:repo:write",
        "foundry:secrets:read",
        "storage:put_object",
        "storage:get_object",
    ],
    "webhooks": {
        "bug_issue_agent": "https://foundry.example/webhook/bug-issue",
        "internal_agent_call": "https://foundry.example/webhook/agents"
    },
    "notes": "Do not store secrets here. Use Foundry secret store for OAuth tokens, S3 credentials, and GitHub app keys."
}
