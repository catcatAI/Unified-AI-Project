import os
import json
import requests
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class UnifiedAIClient:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None,
                 timeout: Optional[int] = None):
        self.base_url = (
            base_url
            or os.environ.get("CLI_BASE_URL")
            or "http://localhost:8000"
        ).rstrip("/")

        self.token = token or os.environ.get("CLI_TOKEN")
        try:
            self.timeout = (
                int(timeout)
                if timeout is not None
                else int(os.environ.get("CLI_TIMEOUT", "10"))
            )
        except ValueError:
            self.timeout = 10

    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None,
                      params: Optional[dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/v1/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        try:
            if method.upper() == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            elif method.upper() == "POST":
                resp = requests.post(url, headers=headers, json=data, params=params, timeout=self.timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            resp.raise_for_status()
            try:
                return resp.json()
            except ValueError:
                return {"raw": resp.text}
        except requests.exceptions.HTTPError as e:
            body = None
            try:
                body = resp.json()
            except (ValueError, KeyError, TypeError):
                body = resp.text if 'resp' in locals() else None
            return {
                "error": str(e),
                "status": getattr(resp, 'status_code', None),
                "body": body,
            }
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def health_check(self) -> Dict[str, Any]:
        return self._make_request("GET", "health")

    def chat(self, message: str, user_id: str = "cli_user",
             session_id: str = "cli_session") -> Dict[str, Any]:
        data = {"text": message, "user_id": user_id, "session_id": session_id}
        return self._make_request("POST", "chat", data=data)

    def analyze_code(self, code: str, language: str = "auto") -> Dict[str, Any]:
        data = {"code": code, "language": language}
        return self._make_request("POST", "code", data=data)

    def search(self, query: str) -> Dict[str, Any]:
        data = {"query": query}
        return self._make_request("POST", "search", data=data)

    def generate_image(self, prompt: str, style: str = "realistic") -> Dict[str, Any]:
        data = {"prompt": prompt, "style": style}
        return self._make_request("POST", "image", data=data)

    def get_atlassian_status(self) -> Dict[str, Any]:
        return self._make_request("GET", "atlassian/status")

    def get_jira_projects(self) -> Dict[str, Any]:
        return self._make_request("GET", "atlassian/jira/projects")

    def get_jira_issues(self, jql: str = "", limit: int = 50) -> Dict[str, Any]:
        params = {"limit": limit}
        if jql:
            params["jql"] = jql
        return self._make_request("GET", "atlassian/jira/issues", params=params)

    def create_jira_issue(self, project_key: str, summary: str, description: str = "",
                          issue_type: str = "Task") -> Dict[str, Any]:
        data = {
            "project_key": project_key,
            "summary": summary,
            "description": description,
            "issue_type": issue_type,
        }
        return self._make_request("POST", "atlassian/jira/issue", data=data)

    def get_confluence_spaces(self) -> Dict[str, Any]:
        return self._make_request("GET", "atlassian/confluence/spaces")

    def search_confluence(self, query: str, limit: int = 25) -> Dict[str, Any]:
        params = {"query": query, "limit": limit}
        return self._make_request("GET", "atlassian/confluence/search", params=params)
