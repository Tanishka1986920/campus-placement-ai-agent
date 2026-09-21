import os
import sys
import inspect
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")


class FoundryClient:
    """
    Connects the FastAPI backend with the Microsoft Foundry
    multi-agent system.

    Uses local fallback when Foundry is not configured.
    Foundry agents are imported lazily only when required.
    """

    def __init__(self):
        self.project_endpoint = os.getenv(
            "FOUNDRY_PROJECT_ENDPOINT"
        )

    def is_configured(self) -> bool:
        return bool(self.project_endpoint)

    async def _run_agent(self, agent, prompt: str):
        """
        Supports both async and sync agent.run().
        """

        result = agent.run(prompt)

        if inspect.isawaitable(result):
            result = await result

        return result

    async def process_query(
        self,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:

        # Safe local/test fallback
        if not self.is_configured():
            return {
                "echo": payload,
                "recommendation": "contact_career_services",
                "mode": "local-fallback",
            }

        # Lazy import: only load Foundry when configured
        from agents.foundry_agents import (
            get_architecture_agent,
        )

        agent = get_architecture_agent()

        prompt = (
            "Analyze this Campus Placement AI request and "
            "provide a concise response or implementation plan.\n\n"
            f"Request: {payload}"
        )

        response = await self._run_agent(
            agent,
            prompt,
        )

        return {
            "echo": payload,
            "recommendation": response.text,
            "mode": "microsoft-foundry",
            "agent": "architecture-agent",
        }

    async def process_resume(
        self,
        file_path: str
    ) -> Dict[str, Any]:

        with open(file_path, "rb") as file:
            data = file.read()

        result = {
            "parsed_text_sample": data[:200].decode(
                errors="ignore"
            ),
            "size_bytes": len(data),
        }

        # Safe local/test fallback
        if not self.is_configured():
            result["mode"] = "local-fallback"
            return result

        # Lazy Foundry import
        from agents.foundry_agents import (
            get_backend_agent,
        )

        agent = get_backend_agent()

        prompt = (
            "A resume was uploaded to the Campus Placement "
            "AI backend. Verify its backend processing flow "
            "through the Microsoft Foundry system. "
            f"Filename: {Path(file_path).name}, "
            f"size: {len(data)} bytes."
        )

        response = await self._run_agent(
            agent,
            prompt,
        )

        result["mode"] = "microsoft-foundry"
        result["agent"] = "backend-agent"
        result["foundry_response"] = response.text

        return result

    def get_multi_agent_status(self) -> Dict[str, Any]:
        """
        Reports connection status for all four required agents.
        """

        agent_names = [
            "architecture-agent",
            "backend-agent",
            "ui-agent",
            "bug-issue-agent",
        ]

        if not self.is_configured():
            return {
                "configured": False,
                "agents": agent_names,
                "agent_factories": {},
                "mode": "local-fallback",
            }

        # Lazy imports prevent test/offline failures
        from agents.foundry_agents import (
            get_architecture_agent,
            get_backend_agent,
            get_ui_agent,
            get_bug_agent,
        )

        return {
            "configured": True,
            "agents": agent_names,
            "mode": "microsoft-foundry",
            "agent_factories": {
                "architecture": get_architecture_agent,
                "backend": get_backend_agent,
                "ui": get_ui_agent,
                "bug": get_bug_agent,
            },
        }