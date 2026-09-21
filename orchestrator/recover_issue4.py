import asyncio

from orchestrator.github_update import update_github_checklist


async def main():

    verified_items = [
        "Create UI Agent in Microsoft Foundry",
        "Add frontend development instructions",
        "Create Campus Placement AI interface design using Google Stitch",
        "Generate/export the required UI from Stitch",
        "Implement the Stitch UI in the project",
        "Connect UI with backend API endpoints",
        "Add loading, validation, and error states",
        "Send completed UI work to Bug/Issue Agent for verification",
    ]

    await update_github_checklist(
        issue_number=4,
        verified_items=verified_items
    )


if __name__ == "__main__":
    asyncio.run(main())