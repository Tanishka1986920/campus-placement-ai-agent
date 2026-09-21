from typing import Dict, Any
import logging

logger = logging.getLogger("foundry_adapter")

class FoundryAdapter:
    """
    FoundryAdapter - interface and mock implementation for local/dev.
    In production, implement methods to authenticate and call Microsoft Foundry endpoints.
    Configuration should be provided via environment variables (see README).
    """

    def __init__(self, base_url: str = None, client_id: str = None):
        # For local mock, no configuration required
        self.base_url = base_url
        self.client_id = client_id

    def submit_resume_processing(self, resume_id: str, file_bytes: bytes) -> Dict[str, Any]:
        logger.info(f"(mock) submit_resume_processing for {resume_id}")
        # Return a mock task id and status
        return {"task_id": f"mock-task-{resume_id}", "status": "submitted"}

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        logger.info(f"(mock) get_task_status for {task_id}")
        return {"task_id": task_id, "status": "completed"}
