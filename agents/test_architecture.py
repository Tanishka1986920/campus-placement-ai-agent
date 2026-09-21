import asyncio
import os

from dotenv import load_dotenv
from azure.identity import AzureCliCredential
from agent_framework.foundry import FoundryAgent

load_dotenv()

async def main():
    agent = FoundryAgent(
        project_endpoint=os.getenv("FOUNDRY_PROJECT_ENDPOINT"),
        agent_name="architecture-agent",
        agent_version="3",
        credential=AzureCliCredential(),
    )

    result = await agent.run(
        "Introduce yourself briefly and tell me your role in this project. "
        "Do not modify GitHub."
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(main())