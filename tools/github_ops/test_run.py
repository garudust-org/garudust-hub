"""Unit tests for github_ops/run.py — no real GitHub API calls."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import module under test
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location(
    "github_ops_run", Path(__file__).parent / "run.py"
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

main = _mod.main
create_pr = _mod.create_pr
list_prs = _mod.list_prs
list_issues = _mod.list_issues
add_comment = _mod.add_comment
merge_pr = _mod.merge_pr
close_issue = _mod.close_issue
get_pr = _mod.get_pr
get_issue = _mod.get_issue
make_client = _mod.make_client
gh = _mod.gh


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fake_client() -> MagicMock:
    return MagicMock()


def pr_fixture(number=1, state="open") -> dict:
    return {
        "number": number,
        "title": "Fix bug",
        "state": state,
        "html_url": f"https://github.com/org/repo/pull/{number}",
        "user": {"login": "alice"},
        "head": {"ref": "fix/bug"},
        "base": {"ref": "main"},
        "body": "desc",
        "mergeable": True,
    }


def issue_fixture(number=10, state="open") -> dict:
    return {
        "number": number,
        "title": "Issue title",
        "state": state,
        "html_url": f"https://github.com/org/repo/issues/{number}",
        "body": "issue body",
        "labels": [{"name": "bug"}],
    }


# ---------------------------------------------------------------------------
# main() — validation
# ---------------------------------------------------------------------------

class TestMainValidation:
    def test_missing_action(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"repo": "org/repo"}))
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        with pytest.raises(SystemExit):
            main()

    def test_missing_repo(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"action": "list_prs"}))
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        with pytest.raises(SystemExit):
            main()

    def test_unknown_action(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"action": "fly", "repo": "org/repo"}))
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        with pytest.raises(SystemExit):
            main()

    def test_invalid_json_exits(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", "bad json{")
        monkeypatch.setenv("GITHUB_TOKEN", "tok")
        with pytest.raises(SystemExit):
            main()


# ---------------------------------------------------------------------------
# make_client()
# ---------------------------------------------------------------------------

class TestMakeClient:
    def test_missing_token_exits(self, monkeypatch):
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        with pytest.raises(SystemExit):
            make_client()

    def test_returns_client_with_auth_header(self, monkeypatch):
        monkeypatch.setenv("GITHUB_TOKEN", "tok_abc")
        client = make_client()
        assert "Bearer tok_abc" in client.headers["Authorization"]


# ---------------------------------------------------------------------------
# create_pr()
# ---------------------------------------------------------------------------

class TestCreatePr:
    def test_success_returns_number_and_url(self):
        client = fake_client()
        with patch.object(_mod, "gh", return_value=pr_fixture(42)):
            result = create_pr(client, "org/repo", {
                "title": "My PR", "head": "feature/x", "base": "main",
            })
        assert result["number"] == 42
        assert "pull/42" in result["url"]

    def test_missing_title_exits(self):
        with pytest.raises(SystemExit):
            create_pr(fake_client(), "org/repo", {"head": "feat/x"})

    def test_missing_head_exits(self):
        with pytest.raises(SystemExit):
            create_pr(fake_client(), "org/repo", {"title": "T"})

    def test_default_base_is_main(self):
        captured = {}
        def fake_gh(client, method, path, **kwargs):
            captured["json"] = kwargs.get("json", {})
            return pr_fixture()
        with patch.object(_mod, "gh", side_effect=fake_gh):
            create_pr(fake_client(), "org/repo", {"title": "T", "head": "feat/x"})
        assert captured["json"]["base"] == "main"


# ---------------------------------------------------------------------------
# list_prs()
# ---------------------------------------------------------------------------

class TestListPrs:
    def test_returns_mapped_list(self):
        with patch.object(_mod, "gh", return_value=[pr_fixture(1), pr_fixture(2)]):
            result = list_prs(fake_client(), "org/repo", {})
        assert len(result) == 2
        assert result[0]["number"] == 1
        assert result[0]["author"] == "alice"

    def test_default_state_is_open(self):
        captured = {}
        def fake_gh(client, method, path, **kwargs):
            captured["params"] = kwargs.get("params", {})
            return []
        with patch.object(_mod, "gh", side_effect=fake_gh):
            list_prs(fake_client(), "org/repo", {})
        assert captured["params"]["state"] == "open"

    def test_custom_state_forwarded(self):
        captured = {}
        def fake_gh(client, method, path, **kwargs):
            captured["params"] = kwargs.get("params", {})
            return []
        with patch.object(_mod, "gh", side_effect=fake_gh):
            list_prs(fake_client(), "org/repo", {"state": "closed"})
        assert captured["params"]["state"] == "closed"


# ---------------------------------------------------------------------------
# list_issues() — PR filtering
# ---------------------------------------------------------------------------

class TestListIssues:
    def test_filters_out_pull_requests(self):
        issue = issue_fixture(10)
        pr_as_issue = {**issue_fixture(11), "pull_request": {"url": "..."}}
        with patch.object(_mod, "gh", return_value=[issue, pr_as_issue]):
            result = list_issues(fake_client(), "org/repo", {})
        assert len(result) == 1
        assert result[0]["number"] == 10

    def test_labels_forwarded(self):
        captured = {}
        def fake_gh(client, method, path, **kwargs):
            captured["params"] = kwargs.get("params", {})
            return []
        with patch.object(_mod, "gh", side_effect=fake_gh):
            list_issues(fake_client(), "org/repo", {"labels": "bug,help-wanted"})
        assert captured["params"]["labels"] == "bug,help-wanted"


# ---------------------------------------------------------------------------
# add_comment()
# ---------------------------------------------------------------------------

class TestAddComment:
    def test_success_returns_comment_id(self):
        with patch.object(_mod, "gh", return_value={"id": 99, "html_url": "https://github.com/..."}):
            result = add_comment(fake_client(), "org/repo", {"number": 5, "body": "LGTM"})
        assert result["comment_id"] == 99

    def test_missing_number_exits(self):
        with pytest.raises(SystemExit):
            add_comment(fake_client(), "org/repo", {"body": "hi"})

    def test_missing_body_exits(self):
        with pytest.raises(SystemExit):
            add_comment(fake_client(), "org/repo", {"number": 1})


# ---------------------------------------------------------------------------
# merge_pr()
# ---------------------------------------------------------------------------

class TestMergePr:
    def test_success_returns_merged_true(self):
        with patch.object(_mod, "gh", return_value={"merged": True, "sha": "abc123", "message": "merged"}):
            result = merge_pr(fake_client(), "org/repo", {"number": 3})
        assert result["merged"] is True

    def test_missing_number_exits(self):
        with pytest.raises(SystemExit):
            merge_pr(fake_client(), "org/repo", {})

    def test_default_merge_method_is_merge(self):
        captured = {}
        def fake_gh(client, method, path, **kwargs):
            captured["json"] = kwargs.get("json", {})
            return {"merged": True, "sha": "x", "message": "ok"}
        with patch.object(_mod, "gh", side_effect=fake_gh):
            merge_pr(fake_client(), "org/repo", {"number": 1})
        assert captured["json"]["merge_method"] == "merge"


# ---------------------------------------------------------------------------
# close_issue()
# ---------------------------------------------------------------------------

class TestCloseIssue:
    def test_success_returns_closed_state(self):
        closed = {**issue_fixture(7), "state": "closed"}
        with patch.object(_mod, "gh", return_value=closed):
            result = close_issue(fake_client(), "org/repo", {"number": 7})
        assert result["state"] == "closed"

    def test_missing_number_exits(self):
        with pytest.raises(SystemExit):
            close_issue(fake_client(), "org/repo", {})


# ---------------------------------------------------------------------------
# get_pr() / get_issue()
# ---------------------------------------------------------------------------

class TestGetPr:
    def test_success_returns_fields(self):
        with patch.object(_mod, "gh", return_value=pr_fixture(5)):
            result = get_pr(fake_client(), "org/repo", {"number": 5})
        assert result["number"] == 5
        assert result["head"] == "fix/bug"

    def test_missing_number_exits(self):
        with pytest.raises(SystemExit):
            get_pr(fake_client(), "org/repo", {})


class TestGetIssue:
    def test_success_returns_fields(self):
        with patch.object(_mod, "gh", return_value=issue_fixture(3)):
            result = get_issue(fake_client(), "org/repo", {"number": 3})
        assert result["number"] == 3
        assert result["labels"] == ["bug"]

    def test_missing_number_exits(self):
        with pytest.raises(SystemExit):
            get_issue(fake_client(), "org/repo", {})
