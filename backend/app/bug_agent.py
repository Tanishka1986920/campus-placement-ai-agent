import logging
from typing import Dict, Any, List
from .schemas import ChecklistItemResult
from .utils import run_api_contract_check, run_ui_smoke_check, summarize_results

logger = logging.getLogger("bug_issue_agent.bug_agent")


class BugIssueAgent:
    """A simplified Bug/Issue Agent implementation suitable for a student project.

    Responsibilities implemented:
    - Accept evidence (artifacts) and checklist items to verify.
    - Run a suite of lightweight checks (API contract, UI smoke, sample input checks).
    - Produce reproducible bug reports for failing items, with severity and remediation.
    - Only mark checklist items 'complete' when verification passes.
    - Maintain an audit-style log (in-memory) of verifications.

    Notes:
    - This implementation intentionally does not integrate with GitHub or Microsoft Foundry.
      It focuses on backend verification logic and structured outputs required by the issue.
    - External services are simulated by utility functions in utils.py to keep the module testable.
    """

    def __init__(self):
        self.audit_log: List[Dict[str, Any]] = []

    def verify_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        required_keys = ["issue_number", "checklist"]
        for k in required_keys:
            if k not in payload:
                raise ValueError(f"missing required field: {k}")

        issue_number = payload["issue_number"]
        checklist = payload["checklist"]
        artifacts = payload.get("artifacts", {})
        run_tests = payload.get("run_tests", True)

        logger.info("Starting verification for issue %s with %d checklist items",
                    issue_number, len(checklist))

        results: List[ChecklistItemResult] = []

        # Iterate checklist items and attempt to verify each one.
        for item in checklist:
            item_id = item.get("id") or item.get("title")
            description = item.get("description", "")
            expected = item.get("expected", {})

            logger.info("Verifying item %s: %s", item_id, description)

            # Default result structure
            result = ChecklistItemResult(
                id=str(item_id),
                description=description,
                passed=False,
                evidence=[],
                severity="low",
                remediation=None,
            )

            # Choose checks based on expected.type
            expected_type = expected.get("type") if isinstance(expected, dict) else None

            try:
                if not run_tests:
                    # If tests are not requested, only do superficial presence checks
                    ok, evidence = self._presence_check(item, artifacts)
                else:
                    if expected_type == "api_contract":
                        ok, evidence = run_api_contract_check(expected, artifacts)
                    elif expected_type == "ui_smoke":
                        ok, evidence = run_ui_smoke_check(expected, artifacts)
                    elif expected_type == "sample_io":
                        # sample IO check is handled as API contract for simplicity
                        ok, evidence = run_api_contract_check(expected, artifacts)
                    else:
                        # Unknown expected type -> fallback to presence check
                        ok, evidence = self._presence_check(item, artifacts)

                result.passed = bool(ok)
                result.evidence = evidence or []

                if not ok:
                    result.severity = self._assess_severity(item, evidence)
                    result.remediation = self._make_remediation(item, evidence)
                else:
                    result.severity = "none"

            except Exception as e:
                logger.exception("Error while verifying item %s", item_id)
                result.passed = False
                result.evidence = [f"exception: {str(e)}"]
                result.severity = "critical"
                result.remediation = "Investigate exception in verification runner; check agent logs."

            results.append(result)

        overall = summarize_results(results)

        audit_entry = {
            "issue_number": issue_number,
            "result_summary": overall,
            "raw_results": [r.dict() for r in results],
        }
        self.audit_log.append(audit_entry)

        output = {
            "issue_number": issue_number,
            "overall": overall,
            "items": [r.dict() for r in results],
            "audit_id": len(self.audit_log) - 1,
        }

        logger.info("Verification complete for issue %s: %s", issue_number, overall["status"])
        return output

    def _presence_check(self, item: Dict[str, Any], artifacts: Dict[str, Any]):
        """Perform a minimal check to see if the artifact referenced exists.

        This is used as a fallback when no specific checks are available.
        """
        expected = item.get("expected", {})
        evidence = []

        # If the expected object references an endpoint name, check artifacts
        endpoint = expected.get("endpoint") if isinstance(expected, dict) else None
        pr_url = artifacts.get("pr_url")

        if endpoint:
            available_endpoints = artifacts.get("api_endpoints", [])
            if endpoint in available_endpoints:
                return True, [f"endpoint {endpoint} reachable (listed in artifacts)"]
            else:
                return False, [f"endpoint {endpoint} not found in artifacts"]

        if pr_url:
            return True, ["pull request provided in artifacts"]

        # Default: pass if any artifact exists
        if artifacts:
            return True, ["artifacts provided but no specific checks defined"]

        return False, ["no artifacts provided to verify this checklist item"]

    def _assess_severity(self, item: Dict[str, Any], evidence: List[str]) -> str:
        """Simple heuristic to determine severity from evidence text."""
        text = " ".join(evidence).lower()
        if "exception" in text or "500" in text or "critical" in text:
            return "critical"
        if "not found" in text or "missing" in text:
            return "high"
        return "medium"

    def _make_remediation(self, item: Dict[str, Any], evidence: List[str]) -> str:
        """Produce a short remediation instruction for the failing item."""
        if not evidence:
            return "Provide artifacts (API endpoints, PR link, logs) and sample inputs/expected outputs."

        if any("not found" in e.lower() for e in evidence):
            return "Attach the missing artifact or ensure the deployment exposes the expected endpoint."
        if any("schema mismatch" in e.lower() for e in evidence):
            return "Fix the API contract to match the documented schema or update the documentation."
        if any("exception" in e.lower() for e in evidence):
            return "Inspect agent logs, reproduce locally with the provided steps, and fix the exception."

        return "Check the failing evidence and run the checklist tests locally; provide corrected artifacts."
