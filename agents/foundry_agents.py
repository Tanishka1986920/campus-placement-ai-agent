import os

from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework.foundry import FoundryAgent

load_dotenv()

PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT")

credential = AzureCliCredential()


def get_architecture_agent():
    return FoundryAgent(
        project_endpoint=PROJECT_ENDPOINT,
        agent_name="architecture-agent",
        agent_version="3",
        credential=credential,
    )


def get_backend_agent():
    return FoundryAgent(
        project_endpoint=PROJECT_ENDPOINT,
        agent_name="backend-agent",
        agent_version="2",
        credential=credential,
    )


def get_ui_agent():
    return FoundryAgent(
        project_endpoint=PROJECT_ENDPOINT,
        agent_name="ui-agent",
        agent_version="2",
        credential=credential,
    )


def get_bug_agent():
    return FoundryAgent(
        project_endpoint=PROJECT_ENDPOINT,
        agent_name="bug-issue-agent",
        agent_version="2",
        credential=credential,
    )