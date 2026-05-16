#!/usr/bin/env python3
"""
view_image — analyse an image with a free vision LLM.

Providers (checked in order):
  1. Google Gemini (GOOGLE_AI_API_KEY) model: GARUDUST_MODEL env (default: gemini-flash-latest)
  2. OpenRouter  (OPENROUTER_API_KEY)  model: GARUDUST_FALLBACK_MODEL env (default: nvidia/nemotron-nano-12b-v2-vl:free)

Usage: run.py <source> [question] [sender]
  source   — local file path or public URL
  question — what to ask (optional)
  sender   — name/username of the person who sent the image (optional, for logging)
"""

import sys
import os
import time
import base64
import mimetypes
import datetime
import httpx

GEMINI_MODEL = os.environ.get("GARUDUST_MODEL", "gemini-flash-latest")
OPENROUTER_MODEL = os.environ.get("GARUDUST_FALLBACK_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free")
DEFAULT_QUESTION = "Describe this image in detail."


def die(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_image(source: str) -> tuple[str, str]:
    """Return (base64_data, media_type) for a local file, or ("", url) for URLs."""
    if source.startswith("http://") or source.startswith("https://"):
        return "", source
    if not os.path.isfile(source):
        die(f"File not found: {source}")
    mime, _ = mimetypes.guess_type(source)
    if not mime or not mime.startswith("image/"):
        mime = "image/jpeg"
    with open(source, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode()
    return data, mime


def build_image_part(source: str) -> dict:
    b64, meta = load_image(source)
    if b64:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{meta};base64,{b64}"},
        }
    return {"type": "image_url", "image_url": {"url": meta}}


def ask_openrouter(source: str, question: str, api_key: str) -> str:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    build_image_part(source),
                    {"type": "text", "text": question},
                ],
            }
        ],
    }
    resp = httpx.post(
        "https://openrouter.ai/api/v1/chat/completions",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def ask_gemini(source: str, question: str, api_key: str) -> str:
    b64, meta = load_image(source)
    if b64:
        image_part = {"inline_data": {"mime_type": meta, "data": b64}}
    else:
        image_part = {"file_data": {"mime_type": "image/jpeg", "file_uri": meta}}

    payload = {
        "contents": [
            {
                "parts": [
                    image_part,
                    {"text": question},
                ]
            }
        ]
    }
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={api_key}"
    )
    resp = httpx.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


def ask_gemini_with_retry(
    source: str, question: str, api_key: str, attempts: int = 3
) -> str:
    """Call Gemini, retrying on 429 (free-tier rate limit) with backoff.

    Honours the Retry-After header when present (capped at 20s so the tool
    never hangs the caller), otherwise falls back to 1s/2s/4s backoff.
    """
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return ask_gemini(source, question, api_key)
        except httpx.HTTPStatusError as e:
            last_err = e
            if e.response.status_code == 429 and i < attempts - 1:
                wait = 2**i
                ra = e.response.headers.get("retry-after", "")
                if ra.isdigit():
                    wait = min(int(ra), 20)
                time.sleep(wait)
                continue
            raise
    assert last_err is not None
    raise last_err


LOG_FILE = os.path.expanduser("~/.garudust/view_image.log")


def log_entry(source: str, sender: str) -> None:
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    n = 1
    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE) as f:
            n = sum(1 for _ in f) + 1

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    sender_part = f" @{sender}" if sender else ""
    with open(LOG_FILE, "a") as f:
        f.write(f"[รูปที่ {n}] {now}{sender_part} — {source}\n")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        die("Usage: run.py <source> [question] [sender]")

    source = args[0]
    question = args[1].strip() if len(args) > 1 else ""
    sender = args[2].strip() if len(args) > 2 else ""
    if not question:
        question = DEFAULT_QUESTION

    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    gm_key = os.environ.get("GOOGLE_AI_API_KEY", "")

    # Gemini preferred — far better Thai output and a more generous free tier
    # than the OpenRouter free vision model, which hallucinated garbled text.
    # On Gemini failure (rate limit after retries, network, etc.) fall back to
    # OpenRouter so a transient 429 degrades to a weaker answer, not no answer.
    if gm_key:
        try:
            result = ask_gemini_with_retry(source, question, gm_key)
        except Exception as e:  # noqa: BLE001 — any Gemini failure → fallback
            if or_key:
                print(
                    f"[view_image: Gemini failed ({e}); falling back to OpenRouter]",
                    file=sys.stderr,
                )
                result = ask_openrouter(source, question, or_key)
            else:
                die(f"Gemini failed and no OpenRouter fallback configured: {e}")
    elif or_key:
        result = ask_openrouter(source, question, or_key)
    else:
        die("Set GOOGLE_AI_API_KEY or OPENROUTER_API_KEY to use view_image.")

    log_entry(source, sender)
    print(result)


if __name__ == "__main__":
    main()
