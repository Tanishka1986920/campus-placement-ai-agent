import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("github_adapter")

try:
    import requests
except Exception:
    requests = None

class GitHubAdapter:
    """
    Minimal GitHub adapter to support Backend Agent operations for issue claiming/commenting.

    Usage:
      - Provide GITHUB_TOKEN via environment variable for authenticated requests.
      - For local dev and tests this adapter can be mocked.

    Methods implemented:
      - get_issue(owner, repo, issue_number)
      - comment_on_issue(owner, repo, issue_number, body)
      - assign_issue(owner, repo, issue_number, assignees)
      - search_issues(owner, repo, query)  # lightweight wrapper

    Note: This adapter is intentionally small and safe (no automatic destructive actions). It expects the caller to verify permissions.
    """

    def __init__(self, token: Optional[str] = None, base_url: str = "https://api.github.com"):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = base_url.rstrip("/")
        if not requests:
            logger.warning("requests library not available; network calls will fail. In tests, mock this adapter.")

    def _headers(self) -> Dict[str, str]:
        hdrs = {"Accept": "application/vnd.github+json"}
        if self.token:
            hdrs["Authorization"] = f"Bearer {self.token}"
        return hdrs

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Return issue JSON or raise RuntimeError on failure."""
        if not requests:
            raise RuntimeError("requests not available")
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        resp = requests.get(url, headers=self._headers())
        if resp.status_code != 200:
            logger.error("Failed to get issue %s/%s#%s: %s", owner, repo, issue_number, resp.text)
            raise RuntimeError(f"GitHub get_issue failed: {resp.status_code}")
        return resp.json()

    def comment_on_issue(self, owner: str, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
        """Post a comment on an issue. Returns comment JSON."""
        if not requests:
            raise RuntimeError("requests not available")
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        resp = requests.post(url, headers=self._headers(), json={"body": body})
        if resp.status_code not in (200, 201):
            logger.error("Failed to comment on issue %s/%s#%s: %s", owner, repo, issue_number, resp.text)
            raise RuntimeError(f"GitHub comment failed: {resp.status_code}")
        return resp.json()

    def assign_issue(self, owner: str, repo: str, issue_number: int, assignees: list) -> Dict[str, Any]:
        """Assign issue to user(s). Returns issue JSON."""
        if not requests:
            raise RuntimeError("requests not available")
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        resp = requests.patch(url, headers=self._headers(), json={"assignees": assignees})
        if resp.status_code not in (200, 201):
            logger.error("Failed to assign issue %s/%s#%s: %s", owner, repo, issue_number, resp.text)
            raise RuntimeError(f"GitHub assign failed: {resp.status_code}")
        return resp.json()

    def search_issues(self, owner: str, repo: str, query: str) -> Dict[str, Any]:
        """Perform a simple issues search within a repository. Returns search results JSON."""
        if not requests:
            raise RuntimeError("requests not available")
        q = f"repo:{owner}/{repo} {query}"
        url = f"{self.base_url}/search/issues"
        resp = requests.get(url, headers=self._headers(), params={"q": q})
        if resp.status_code != 200:
            logger.error("Failed to search issues in %s/%s: %s", owner, repo, resp.text)
            raise RuntimeError(f"GitHub search failed: {resp.status_code}")
        return resp.json()
