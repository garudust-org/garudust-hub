#!/usr/bin/env python3
"""LINE Official Account hub tool — push / broadcast / reply / multicast / get_profile."""

import json
import os
import sys

import httpx

BASE = "https://api.line.me/v2/bot"
TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")


def err(msg: str) -> None:
    print(json.dumps({"ok": False, "error": msg}))
    sys.exit(1)


def headers() -> dict:
    return {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }


def build_message(params: dict) -> dict:
    msg_type = params.get("message_type", "text")
    alt = params.get("alt_text", "Message")

    if msg_type == "text":
        text = params.get("text")
        if not text:
            err("'text' is required for message_type 'text'")
        return {"type": "text", "text": text}

    if msg_type == "image":
        image_url = params.get("image_url")
        if not image_url:
            err("'image_url' is required for message_type 'image'")
        preview_url = params.get("preview_url") or image_url
        return {
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": preview_url,
        }

    if msg_type == "sticker":
        pkg = params.get("sticker_package_id")
        sid = params.get("sticker_id")
        if pkg is None or sid is None:
            err("'sticker_package_id' and 'sticker_id' are required for message_type 'sticker'")
        return {
            "type": "sticker",
            "packageId": str(pkg),
            "stickerId": str(sid),
        }

    if msg_type == "flex":
        content = params.get("flex_content")
        if not content:
            err("'flex_content' is required for message_type 'flex'")
        return {
            "type": "flex",
            "altText": alt,
            "contents": content,
        }

    err(f"unknown message_type: {msg_type!r}")


def action_push(client: httpx.Client, params: dict) -> dict:
    user_id = params.get("user_id")
    if not user_id:
        err("'user_id' is required for action 'push'")
    body = {
        "to": user_id,
        "messages": [build_message(params)],
        "notificationDisabled": params.get("notification_disabled", False),
    }
    r = client.post(f"{BASE}/message/push", json=body, headers=headers())
    r.raise_for_status()
    return {"ok": True, "action": "push", "user_id": user_id, "response": r.json()}


def action_broadcast(client: httpx.Client, params: dict) -> dict:
    body = {
        "messages": [build_message(params)],
        "notificationDisabled": params.get("notification_disabled", False),
    }
    r = client.post(f"{BASE}/message/broadcast", json=body, headers=headers())
    r.raise_for_status()
    return {"ok": True, "action": "broadcast", "response": r.json()}


def action_reply(client: httpx.Client, params: dict) -> dict:
    reply_token = params.get("reply_token")
    if not reply_token:
        err("'reply_token' is required for action 'reply'")
    body = {
        "replyToken": reply_token,
        "messages": [build_message(params)],
        "notificationDisabled": params.get("notification_disabled", False),
    }
    r = client.post(f"{BASE}/message/reply", json=body, headers=headers())
    r.raise_for_status()
    return {"ok": True, "action": "reply", "response": r.json()}


def action_multicast(client: httpx.Client, params: dict) -> dict:
    user_ids = params.get("user_ids")
    if not user_ids:
        err("'user_ids' is required for action 'multicast'")
    if len(user_ids) > 500:
        err("'user_ids' must not exceed 500 recipients per call")
    body = {
        "to": user_ids,
        "messages": [build_message(params)],
        "notificationDisabled": params.get("notification_disabled", False),
    }
    r = client.post(f"{BASE}/message/multicast", json=body, headers=headers())
    r.raise_for_status()
    return {"ok": True, "action": "multicast", "recipients": len(user_ids), "response": r.json()}


def action_get_profile(client: httpx.Client, params: dict) -> dict:
    user_id = params.get("user_id")
    if not user_id:
        err("'user_id' is required for action 'get_profile'")
    r = client.get(f"{BASE}/profile/{user_id}", headers=headers())
    r.raise_for_status()
    return {"ok": True, "action": "get_profile", "profile": r.json()}


ACTIONS = {
    "push": action_push,
    "broadcast": action_broadcast,
    "reply": action_reply,
    "multicast": action_multicast,
    "get_profile": action_get_profile,
}


def main() -> None:
    if not TOKEN:
        err("LINE_CHANNEL_ACCESS_TOKEN is not set")

    raw = os.environ.get("TOOL_PARAMS", "")
    if raw:
        try:
            params = json.loads(raw)
        except json.JSONDecodeError as exc:
            err(f"failed to parse TOOL_PARAMS: {exc}")
    elif len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except json.JSONDecodeError as exc:
            err(f"failed to parse argv[1]: {exc}")
    else:
        err("no params provided (expected TOOL_PARAMS env var or argv[1] JSON)")

    action = params.get("action")
    if not action:
        err("'action' is required")

    fn = ACTIONS.get(action)
    if fn is None:
        err(f"unknown action: {action!r}. Valid: {', '.join(ACTIONS)}")

    with httpx.Client(timeout=30) as client:
        try:
            result = fn(client, params)
            print(json.dumps(result, ensure_ascii=False))
        except httpx.HTTPStatusError as exc:
            body = ""
            try:
                body = exc.response.json()
            except Exception:
                body = exc.response.text
            err(f"LINE API error {exc.response.status_code}: {body}")
        except httpx.RequestError as exc:
            err(f"network error: {exc}")


if __name__ == "__main__":
    main()
