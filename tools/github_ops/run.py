#!/usr/bin/env python3
"""GitHub operations hub tool.

Supported actions:
  create_pr    — open a pull request
  list_prs     — list PRs (default: open)
  get_pr       — get PR details
  comment      — add a comment to a PR or issue
  list_issues  — list issues (default: open)
  get_issue    — get issue details
  merge_pr     — merge a pull request
  close_issue  — close an issue

All parameters arrive via TOOL_PARAMS env var as JSON (injected by garudust).
Requires GITHUB_TOKEN env var (personal access token or fine-grained PAT).
"""

import json
import os
import sys
from typing import Any

try:
    import httpx
except ImportError:
    print("error: httpx not installed — run: pip install httpx", file=sys.stderr)
    sys.exit(1)

API = "https://api.github.com"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def make_client() -> httpx.Client:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        die("GITHUB_TOKEN is not set")
    return httpx.Client(
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )


def gh(client: httpx.Client, method: str, path: str, **kwargs: Any) -> Any:
    try:
        resp = client.request(method, f"{API}{path}", **kwargs)
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        die(f"GitHub API {e.response.status_code}: {e.response.text[:400]}")
    except httpx.RequestError as e:
        die(f"GitHub request failed: {e}")
    return resp.json() if resp.content else {}


def create_pr(client: httpx.Client, repo: str, p: dict) -> dict:
    title = p.get("title", "").strip()
    head = p.get("head", "").strip()
    base = p.get("base", "main").strip()
    body = p.get("body", "")
    if not title:
        die("'title' is required for create_pr")
    if not head:
        die("'head' (source branch) is required for create_pr")
    data = gh(client, "POST", f"/repos/{repo}/pulls",
              json={"title": title, "body": body, "head": head, "base": base})
    return {"number": data["number"], "url": data["html_url"], "state": data["state"]}


def list_prs(client: httpx.Client, repo: str, p: dict) -> list:
    state = p.get("state", "open")
    data = gh(client, "GET", f"/repos/{repo}/pulls", params={"state": state, "per_page": 20})
    return [
        {
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "url": pr["html_url"],
            "author": pr["user"]["login"],
            "head": pr["head"]["ref"],
            "base": pr["base"]["ref"],
        }
        for pr in data
    ]


def get_pr(client: httpx.Client, repo: str, p: dict) -> dict:
    number = p.get("number")
    if not number:
        die("'number' is required for get_pr")
    data = gh(client, "GET", f"/repos/{repo}/pulls/{number}")
    return {
        "number": data["number"],
        "title": data["title"],
        "state": data["state"],
        "url": data["html_url"],
        "body": data.get("body", ""),
        "head": data["head"]["ref"],
        "base": data["base"]["ref"],
        "mergeable": data.get("mergeable"),
        "author": data["user"]["login"],
    }


def add_comment(client: httpx.Client, repo: str, p: dict) -> dict:
    number = p.get("number")
    body = p.get("body", "").strip()
    if not number:
        die("'number' is required for comment")
    if not body:
        die("'body' is required for comment")
    data = gh(client, "POST", f"/repos/{repo}/issues/{number}/comments", json={"body": body})
    return {"comment_id": data["id"], "url": data["html_url"]}


def list_issues(client: httpx.Client, repo: str, p: dict) -> list:
    state = p.get("state", "open")
    params: dict = {"state": state, "per_page": 20}
    if labels := p.get("labels", "").strip():
        params["labels"] = labels
    data = gh(client, "GET", f"/repos/{repo}/issues", params=params)
    # GitHub /issues returns PRs too — filter them out
    return [
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"],
            "url": i["html_url"],
            "labels": [lb["name"] for lb in i.get("labels", [])],
        }
        for i in data
        if "pull_request" not in i
    ]


def get_issue(client: httpx.Client, repo: str, p: dict) -> dict:
    number = p.get("number")
    if not number:
        die("'number' is required for get_issue")
    data = gh(client, "GET", f"/repos/{repo}/issues/{number}")
    return {
        "number": data["number"],
        "title": data["title"],
        "state": data["state"],
        "body": data.get("body", ""),
        "url": data["html_url"],
        "labels": [lb["name"] for lb in data.get("labels", [])],
    }


def merge_pr(client: httpx.Client, repo: str, p: dict) -> dict:
    number = p.get("number")
    if not number:
        die("'number' is required for merge_pr")
    method = p.get("merge_method", "merge")
    data = gh(client, "PUT", f"/repos/{repo}/pulls/{number}/merge",
              json={"merge_method": method})
    return {
        "merged": data.get("merged", False),
        "sha": data.get("sha"),
        "message": data.get("message"),
    }


def close_issue(client: httpx.Client, repo: str, p: dict) -> dict:
    number = p.get("number")
    if not number:
        die("'number' is required for close_issue")
    data = gh(client, "PATCH", f"/repos/{repo}/issues/{number}", json={"state": "closed"})
    return {"number": data["number"], "state": data["state"], "url": data["html_url"]}


ACTIONS = {
    "create_pr": create_pr,
    "list_prs": list_prs,
    "get_pr": get_pr,
    "comment": add_comment,
    "list_issues": list_issues,
    "get_issue": get_issue,
    "merge_pr": merge_pr,
    "close_issue": close_issue,
}


def main() -> None:
    try:
        p = json.loads(os.environ.get("TOOL_PARAMS", "{}"))
    except json.JSONDecodeError:
        die("invalid TOOL_PARAMS JSON")

    action = p.get("action", "").strip()
    repo = p.get("repo", "").strip()

    if not action:
        die("'action' is required")
    if not repo:
        die("'repo' is required (owner/repo format)")

    fn = ACTIONS.get(action)
    if not fn:
        die(f"unknown action '{action}'. Valid: {', '.join(ACTIONS)}")

    with make_client() as client:
        result = fn(client, repo, p)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
