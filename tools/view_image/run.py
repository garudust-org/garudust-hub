#!/usr/bin/env python3
"""
view_image — analyse an image with a free vision LLM.

Providers (checked in order):
  1. OpenRouter  (OPENROUTER_API_KEY)  default model: nvidia/nemotron-nano-12b-v2-vl:free
  2. Google Gemini (GOOGLE_AI_API_KEY) model: gemini-2.0-flash

Usage: run.py <source> [question]
  source   — local file path or public URL
  question — what to ask (optional)
"""

import sys
import os
import base64
import mimetypes
import httpx

OPENROUTER_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
GEMINI_MODEL = "gemini-2.0-flash"
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


def main() -> None:
    args = sys.argv[1:]
    if not args:
        die("Usage: run.py <source> [question]")

    source = args[0]
    question = " ".join(args[1:]).strip() if len(args) > 1 else ""
    if not question:
        question = DEFAULT_QUESTION

    or_key = os.environ.get("OPENROUTER_API_KEY", "")
    gm_key = os.environ.get("GOOGLE_AI_API_KEY", "")

    if or_key:
        result = ask_openrouter(source, question, or_key)
    elif gm_key:
        result = ask_gemini(source, question, gm_key)
    else:
        die("Set OPENROUTER_API_KEY or GOOGLE_AI_API_KEY to use view_image.")

    print(result)


if __name__ == "__main__":
    main()
