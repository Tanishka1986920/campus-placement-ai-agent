from typing import Tuple, Dict, Any, List
import logging

logger = logging.getLogger("bug_issue_agent.utils")


def run_api_contract_check(expected: Dict[str, Any], artifacts: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Simulate an API contract check.

    For the student project, this function will inspect provided artifacts and the expected
    contract object and return pass/fail plus evidence strings. Real HTTP calls are not made
    to keep this self-contained and deterministic for tests.
    """
    endpoint = expected.get("endpoint")
    method = expected.get("method", "GET").upper()
    sample_input = expected.get("sample_input")
    expected_output = expected.get("expected_output")

    evidence: List[str] = []

    available_endpoints = artifacts.get("api_endpoints", [])

    if not endpoint:
        return False, ["expected.endpoint not specified for api_contract check"]

    if endpoint not in available_endpoints:
        return False, [f"endpoint {endpoint} not found in artifacts"]

    # If the artifact includes a mapping of endpoint -> sample response, try to match
    endpoint_responses = artifacts.get("endpoint_responses", {})
    if endpoint in endpoint_responses:
        observed = endpoint_responses[endpoint]
        evidence.append(f"observed_response: {observed}")
        if expected_output is None:
            return True, evidence
        # simple equality check
        if observed == expected_output:
            return True, evidence + ["response matched expected_output"]
        else:
            return False, evidence + ["response did not match expected_output"]

    # If no response mapping provided, pass but note that live checks were not performed
    return True, [f"endpoint {endpoint} declared in artifacts; no live response provided (assumed ok)"]


def run_ui_smoke_check(expected: Dict[str, Any], artifacts: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Simulate a small UI smoke test based on artifacts.

    This looks for a 'ui_screenshots' artifact or 'ui_checks' and uses them to decide pass/fail.
    """
    evidence: List[str] = []
    checks = expected.get("checks", []) or []

    ui_checks = artifacts.get("ui_checks", {})
    screenshots = artifacts.get("ui_screenshots", [])

    if not checks:
        return False, ["no ui checks defined in expected"]

    for c in checks:
        key = c.get("key")
        must_exist = c.get("must_exist", True)
        found = ui_checks.get(key, False)
        if found and must_exist:
            evidence.append(f"ui_check {key}: present")
        elif not found and must_exist:
            evidence.append(f"ui_check {key}: missing")
        else:
            evidence.append(f"ui_check {key}: condition satisfied (must_exist={must_exist})")

    # if any missing -> fail
    if any("missing" in e for e in evidence):
        return False, evidence
    return True, evidence


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize verification results into an overall status and counts."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    severities = {}
    for r in results:
        sev = r.severity or "none"
        severities[sev] = severities.get(sev, 0) + 1

    status = "passed" if failed == 0 else "failed"
    return {
        "total_items": total,
        "passed": passed,
        "failed": failed,
        "severities": severities,
        "status": status,
    }
