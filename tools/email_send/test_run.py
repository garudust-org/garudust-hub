"""Unit tests for email_send/run.py — no real network or SMTP calls."""

import importlib.util
import json
import smtplib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import the module under test from its directory (avoids name collisions)
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location(
    "email_send_run", Path(__file__).parent / "run.py"
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

main = _mod.main
send_resend = _mod.send_resend
send_smtp = _mod.send_smtp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def tool_params(**kwargs) -> dict:
    return {"to": "a@b.com", "subject": "Hi", "body": "Hello", **kwargs}


def mock_ok_response(json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# main() — param validation
# ---------------------------------------------------------------------------

class TestMainValidation:
    def test_missing_to(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"subject": "s", "body": "b"}))
        with pytest.raises(SystemExit):
            main()

    def test_missing_subject(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"to": "a@b.com", "body": "b"}))
        with pytest.raises(SystemExit):
            main()

    def test_missing_body(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"to": "a@b.com", "subject": "s"}))
        with pytest.raises(SystemExit):
            main()

    def test_no_provider_exits(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps(tool_params()))
        monkeypatch.delenv("RESEND_API_KEY", raising=False)
        monkeypatch.delenv("SMTP_HOST", raising=False)
        with pytest.raises(SystemExit):
            main()

    def test_invalid_json_exits(self, monkeypatch):
        monkeypatch.setenv("TOOL_PARAMS", "not-json")
        with pytest.raises(SystemExit):
            main()

    def test_resend_key_takes_priority_over_smtp(self, monkeypatch, capsys):
        monkeypatch.setenv("TOOL_PARAMS", json.dumps(tool_params()))
        monkeypatch.setenv("RESEND_API_KEY", "re_key")
        monkeypatch.setenv("RESEND_FROM_EMAIL", "sender@example.com")
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        with patch("httpx.post", return_value=mock_ok_response({"id": "abc123"})):
            main()
        out = capsys.readouterr().out
        assert "Resend" in out


# ---------------------------------------------------------------------------
# send_resend()
# ---------------------------------------------------------------------------

class TestSendResend:
    def _env(self, monkeypatch, key="re_abc", from_email="from@example.com"):
        monkeypatch.setenv("RESEND_API_KEY", key)
        monkeypatch.setenv("RESEND_FROM_EMAIL", from_email)

    def test_success_prints_id(self, monkeypatch, capsys):
        self._env(monkeypatch)
        with patch("httpx.post", return_value=mock_ok_response({"id": "msg_123"})) as mock_post:
            send_resend("a@b.com", "Subj", "Body", False, "", "", "re_abc")
        out = capsys.readouterr().out
        assert "msg_123" in out
        mock_post.assert_called_once()

    def test_payload_to_is_list(self, monkeypatch):
        self._env(monkeypatch)
        captured = {}
        def fake_post(url, *, headers, json, timeout):
            captured["json"] = json
            return mock_ok_response({"id": "x"})
        with patch("httpx.post", side_effect=fake_post):
            send_resend("a@b.com,c@d.com", "S", "B", False, "", "", "re_abc")
        assert captured["json"]["to"] == ["a@b.com", "c@d.com"]

    def test_html_uses_html_key(self, monkeypatch):
        self._env(monkeypatch)
        captured = {}
        def fake_post(url, *, headers, json, timeout):
            captured["json"] = json
            return mock_ok_response({"id": "x"})
        with patch("httpx.post", side_effect=fake_post):
            send_resend("a@b.com", "S", "<b>hi</b>", True, "", "", "re_abc")
        assert "html" in captured["json"]
        assert "text" not in captured["json"]

    def test_from_name_formatted(self, monkeypatch):
        self._env(monkeypatch)
        captured = {}
        def fake_post(url, *, headers, json, timeout):
            captured["json"] = json
            return mock_ok_response({"id": "x"})
        with patch("httpx.post", side_effect=fake_post):
            send_resend("a@b.com", "S", "B", False, "Alice", "", "re_abc")
        assert captured["json"]["from"] == "Alice <from@example.com>"

    def test_cc_included(self, monkeypatch):
        self._env(monkeypatch)
        captured = {}
        def fake_post(url, *, headers, json, timeout):
            captured["json"] = json
            return mock_ok_response({"id": "x"})
        with patch("httpx.post", side_effect=fake_post):
            send_resend("a@b.com", "S", "B", False, "", "cc@b.com", "re_abc")
        assert captured["json"]["cc"] == ["cc@b.com"]

    def test_missing_from_email_exits(self, monkeypatch):
        monkeypatch.delenv("RESEND_FROM_EMAIL", raising=False)
        with pytest.raises(SystemExit):
            send_resend("a@b.com", "S", "B", False, "", "", "re_abc")

    def test_api_error_exits(self, monkeypatch):
        self._env(monkeypatch)
        import httpx
        resp = MagicMock()
        resp.status_code = 422
        resp.text = "Unprocessable"
        with patch("httpx.post", side_effect=httpx.HTTPStatusError("err", request=MagicMock(), response=resp)):
            with pytest.raises(SystemExit):
                send_resend("a@b.com", "S", "B", False, "", "", "re_abc")


# ---------------------------------------------------------------------------
# send_smtp()
# ---------------------------------------------------------------------------

class TestSendSmtp:
    def _env(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.setenv("SMTP_PORT", "587")
        monkeypatch.setenv("SMTP_USER", "user@example.com")
        monkeypatch.setenv("SMTP_PASSWORD", "secret")
        monkeypatch.setenv("SMTP_FROM", "from@example.com")

    def test_success_calls_sendmail(self, monkeypatch):
        self._env(monkeypatch)
        mock_server = MagicMock()
        with patch("smtplib.SMTP", return_value=mock_server.__enter__.return_value):
            mock_server.__enter__.return_value = mock_server
            mock_server.__exit__.return_value = False
            with patch("smtplib.SMTP") as mock_smtp_cls:
                mock_smtp_cls.return_value.__enter__.return_value = mock_server
                mock_smtp_cls.return_value.__exit__.return_value = False
                send_smtp("a@b.com", "S", "B", False, "", "", "smtp.example.com")
        mock_server.sendmail.assert_called_once()

    def test_missing_smtp_user_exits(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.delenv("SMTP_USER", raising=False)
        with pytest.raises(SystemExit):
            send_smtp("a@b.com", "S", "B", False, "", "", "smtp.example.com")

    def test_smtp_error_exits(self, monkeypatch):
        self._env(monkeypatch)
        with patch("smtplib.SMTP") as mock_smtp_cls:
            mock_smtp_cls.return_value.__enter__.side_effect = smtplib.SMTPException("conn failed")
            with pytest.raises(SystemExit):
                send_smtp("a@b.com", "S", "B", False, "", "", "smtp.example.com")
