"""Unit tests for line_oa/run.py — no real LINE API calls."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Import module under test
# ---------------------------------------------------------------------------
_spec = importlib.util.spec_from_file_location(
    "line_oa_run", Path(__file__).parent / "run.py"
)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

main = _mod.main
build_message = _mod.build_message
action_push = _mod.action_push
action_broadcast = _mod.action_broadcast
action_reply = _mod.action_reply
action_multicast = _mod.action_multicast
action_get_profile = _mod.action_get_profile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fake_post_ok(url, *, json, headers) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {}
    resp.raise_for_status.return_value = None
    return resp


def make_client(post_side_effect=None, get_side_effect=None) -> MagicMock:
    client = MagicMock()
    client.post.side_effect = post_side_effect or fake_post_ok
    client.get.return_value = MagicMock(
        json=lambda: {"userId": "U1", "displayName": "Alice"},
        raise_for_status=lambda: None,
    )
    if get_side_effect:
        client.get.side_effect = get_side_effect
    return client


# ---------------------------------------------------------------------------
# build_message()
# ---------------------------------------------------------------------------

class TestBuildMessage:
    def test_text_message(self):
        msg = build_message({"message_type": "text", "text": "Hello"})
        assert msg == {"type": "text", "text": "Hello"}

    def test_default_type_is_text(self):
        msg = build_message({"text": "Hi"})
        assert msg["type"] == "text"

    def test_text_missing_exits(self):
        with pytest.raises(SystemExit):
            build_message({"message_type": "text"})

    def test_image_message(self):
        msg = build_message({
            "message_type": "image",
            "image_url": "https://example.com/img.jpg",
            "preview_url": "https://example.com/thumb.jpg",
        })
        assert msg["type"] == "image"
        assert msg["originalContentUrl"] == "https://example.com/img.jpg"
        assert msg["previewImageUrl"] == "https://example.com/thumb.jpg"

    def test_image_preview_defaults_to_image_url(self):
        msg = build_message({
            "message_type": "image",
            "image_url": "https://example.com/img.jpg",
        })
        assert msg["previewImageUrl"] == msg["originalContentUrl"]

    def test_image_missing_url_exits(self):
        with pytest.raises(SystemExit):
            build_message({"message_type": "image"})

    def test_sticker_message(self):
        msg = build_message({
            "message_type": "sticker",
            "sticker_package_id": 1,
            "sticker_id": 2,
        })
        assert msg["type"] == "sticker"
        assert msg["packageId"] == "1"
        assert msg["stickerId"] == "2"

    def test_sticker_missing_ids_exits(self):
        with pytest.raises(SystemExit):
            build_message({"message_type": "sticker", "sticker_package_id": 1})

    def test_flex_message(self):
        container = {"type": "bubble", "body": {"type": "box"}}
        msg = build_message({
            "message_type": "flex",
            "flex_content": container,
            "alt_text": "Card",
        })
        assert msg["type"] == "flex"
        assert msg["altText"] == "Card"
        assert msg["contents"] == container

    def test_flex_missing_content_exits(self):
        with pytest.raises(SystemExit):
            build_message({"message_type": "flex"})

    def test_unknown_type_exits(self):
        with pytest.raises(SystemExit):
            build_message({"message_type": "video"})


# ---------------------------------------------------------------------------
# action_push()
# ---------------------------------------------------------------------------

class TestActionPush:
    def test_success_returns_ok(self):
        result = action_push(make_client(), {"user_id": "U123", "text": "Hi"})
        assert result["ok"] is True
        assert result["user_id"] == "U123"

    def test_post_body_contains_to_and_message(self):
        client = make_client()
        action_push(client, {"user_id": "U123", "text": "Hello"})
        call_kwargs = client.post.call_args[1]
        body = call_kwargs["json"]
        assert body["to"] == "U123"
        assert body["messages"][0] == {"type": "text", "text": "Hello"}

    def test_notification_disabled_forwarded(self):
        client = make_client()
        action_push(client, {"user_id": "U1", "text": "Hi", "notification_disabled": True})
        body = client.post.call_args[1]["json"]
        assert body["notificationDisabled"] is True

    def test_missing_user_id_exits(self):
        with pytest.raises(SystemExit):
            action_push(make_client(), {"text": "Hi"})


# ---------------------------------------------------------------------------
# action_broadcast()
# ---------------------------------------------------------------------------

class TestActionBroadcast:
    def test_success_returns_ok(self):
        result = action_broadcast(make_client(), {"text": "Hello everyone"})
        assert result["ok"] is True

    def test_post_called_with_broadcast_endpoint(self):
        client = make_client()
        action_broadcast(client, {"text": "Hi"})
        url = client.post.call_args[0][0]
        assert url.endswith("/message/broadcast")

    def test_no_to_field_in_body(self):
        client = make_client()
        action_broadcast(client, {"text": "Hi"})
        body = client.post.call_args[1]["json"]
        assert "to" not in body


# ---------------------------------------------------------------------------
# action_reply()
# ---------------------------------------------------------------------------

class TestActionReply:
    def test_success_returns_ok(self):
        result = action_reply(make_client(), {
            "reply_token": "tok_abc", "text": "Got it",
        })
        assert result["ok"] is True

    def test_reply_token_in_body(self):
        client = make_client()
        action_reply(client, {"reply_token": "tok_xyz", "text": "OK"})
        body = client.post.call_args[1]["json"]
        assert body["replyToken"] == "tok_xyz"

    def test_missing_reply_token_exits(self):
        with pytest.raises(SystemExit):
            action_reply(make_client(), {"text": "OK"})


# ---------------------------------------------------------------------------
# action_multicast()
# ---------------------------------------------------------------------------

class TestActionMulticast:
    def test_success_returns_recipient_count(self):
        result = action_multicast(make_client(), {
            "user_ids": ["U1", "U2", "U3"], "text": "Hi all",
        })
        assert result["ok"] is True
        assert result["recipients"] == 3

    def test_to_is_list_in_body(self):
        client = make_client()
        action_multicast(client, {"user_ids": ["U1", "U2"], "text": "Hi"})
        body = client.post.call_args[1]["json"]
        assert body["to"] == ["U1", "U2"]

    def test_missing_user_ids_exits(self):
        with pytest.raises(SystemExit):
            action_multicast(make_client(), {"text": "Hi"})

    def test_too_many_users_exits(self):
        with pytest.raises(SystemExit):
            action_multicast(make_client(), {
                "user_ids": [f"U{i}" for i in range(501)], "text": "Hi",
            })

    def test_exactly_500_users_ok(self):
        result = action_multicast(make_client(), {
            "user_ids": [f"U{i}" for i in range(500)], "text": "Hi",
        })
        assert result["recipients"] == 500


# ---------------------------------------------------------------------------
# action_get_profile()
# ---------------------------------------------------------------------------

class TestActionGetProfile:
    def test_success_returns_profile(self):
        result = action_get_profile(make_client(), {"user_id": "U123"})
        assert result["ok"] is True
        assert result["profile"]["displayName"] == "Alice"

    def test_get_called_with_user_id_in_url(self):
        client = make_client()
        action_get_profile(client, {"user_id": "U999"})
        url = client.get.call_args[0][0]
        assert "U999" in url

    def test_missing_user_id_exits(self):
        with pytest.raises(SystemExit):
            action_get_profile(make_client(), {})


# ---------------------------------------------------------------------------
# main() — routing and env validation
# ---------------------------------------------------------------------------

class TestMain:
    def test_missing_token_exits(self, monkeypatch):
        monkeypatch.setattr(_mod, "TOKEN", "")
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"action": "broadcast", "text": "hi"}))
        with pytest.raises(SystemExit):
            main()

    def test_missing_action_exits(self, monkeypatch):
        monkeypatch.setattr(_mod, "TOKEN", "line_token")
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"text": "hi"}))
        with pytest.raises(SystemExit):
            main()

    def test_unknown_action_exits(self, monkeypatch):
        monkeypatch.setattr(_mod, "TOKEN", "line_token")
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"action": "delete_all"}))
        with pytest.raises(SystemExit):
            main()

    def test_invalid_json_exits(self, monkeypatch):
        monkeypatch.setattr(_mod, "TOKEN", "line_token")
        monkeypatch.setenv("TOOL_PARAMS", "not-json")
        with pytest.raises(SystemExit):
            main()

    def test_broadcast_end_to_end(self, monkeypatch, capsys):
        monkeypatch.setattr(_mod, "TOKEN", "line_token")
        monkeypatch.setenv("TOOL_PARAMS", json.dumps({"action": "broadcast", "text": "Hello"}))
        with patch("httpx.Client") as mock_cls:
            instance = MagicMock()
            mock_cls.return_value.__enter__.return_value = instance
            mock_cls.return_value.__exit__.return_value = False
            instance.post.return_value = MagicMock(
                json=lambda: {}, raise_for_status=lambda: None
            )
            main()
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["ok"] is True
