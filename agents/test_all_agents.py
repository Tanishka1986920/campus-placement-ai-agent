import asyncio

from foundry_agents import (
    get_architecture_agent,
    get_backend_agent,
    get_ui_agent,
    get_bug_agent,
)


async def test_agent(name, agent):
    print(f"\nTesting {name}...")

    result = await agent.run(
        "Introduce yourself in one sentence and state your role. "
        "Do not modify GitHub or any files."
    )

    print(result)


async def main():
    await test_agent("Architecture Agent", get_architecture_agent())
    await test_agent("Backend Agent", get_backend_agent())
    await test_agent("UI Agent", get_ui_agent())
    await test_agent("Bug/Issue Agent", get_bug_agent())


if __name__ == "__main__":
    asyncio.run(main())