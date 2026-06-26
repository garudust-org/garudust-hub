#!/usr/bin/env python3
"""
view_image — analyse an image with a free vision LLM.

Providers (checked in order):
  1. Google Gemini  model: GARUDUST_MODEL env (default: gemini-flash-latest)
                    key:   GARUDUST_API_KEY → GOOGLE_AI_API_KEY (fallback)
  2. OpenRouter     model: GARUDUST_FALLBACK_MODEL env (default: nvidia/nemotron-nano-12b-v2-vl:free)
                    key:   GARUDUST_FALLBACK_API_KEY → OPENROUTER_API_KEY (fallback)

GARUDUST_API_KEY and GARUDUST_FALLBACK_API_KEY are injected automatically when
tools.view_image.model / fallback_model use the profile/model format in config.yaml
(e.g. model: vision/gemini-flash-latest). Named env vars are used as fallbacks for
backward compatibility.

Usage: run.py <source> [question]
  source   — local file path or public URL
  question — what to ask (optional)
"""

import sys
import os
import io
import re
import time
import base64
import mimetypes
import httpx

# Transient server-side failures worth retrying. 503 (Gemini overloaded) is the
# common one; 500/502/504 are added defensively. 429 is the free-tier rate limit.
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def scrub(text: object) -> str:
    """Redact API keys before anything reaches stderr/history.

    Both providers leak the key in error text: Gemini puts it in the request URL
    (?key=…) and OpenRouter uses an Authorization: Bearer header. These errors are
    captured into the LINE conversation log and the model's context, so the raw key
    must never survive into them.
    """
    s = str(text)
    s = re.sub(r"([?&]key=)[A-Za-z0-9._\-]+", r"\1REDACTED", s)
    s = re.sub(r"(Bearer\s+)[A-Za-z0-9._\-]+", r"\1REDACTED", s)
    return s

GEMINI_MODEL = os.environ.get("GARUDUST_MODEL", "gemini-2.5-flash")
# Second Gemini model, tried on the SAME key when the primary is unavailable
# (the shared free-tier `*-latest` alias frequently returns 503 "high demand").
# A pinned, lighter model sits in a different capacity pool and is usually up
# when the primary is overloaded — far more reliable than dropping straight to
# the OpenRouter free tier, which idle-times-out under load. Set to "" to skip.
GEMINI_FALLBACK_MODEL = os.environ.get(
    "GARUDUST_GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest"
)
OPENROUTER_MODEL = os.environ.get("GARUDUST_FALLBACK_MODEL", "nvidia/nemotron-nano-12b-v2-vl:free")
DEFAULT_QUESTION = "Describe this image in detail."

# Per-request network timeouts. Kept tight so a stalled provider fails over to
# the next link in the chain quickly instead of hanging the LINE reply for
# minutes. Vision responses are normally well under 15s; these are generous
# ceilings, not targets.
GEMINI_TIMEOUT = 30
OPENROUTER_TIMEOUT = 45

# Downscale large photos before upload. Gemini and OpenRouter both internally
# cap vision inputs around ~1024–2048 px; sending a 4000×3000 phone photo
# wastes seconds of upload + server-side resize for no quality gain. 1280 is
# a conservative cap that preserves enough detail for QR/text reading.
MAX_DIM = 1280
JPEG_QUALITY = 85


def die(msg: object) -> None:
    print(f"Error: {scrub(msg)}", file=sys.stderr)
    sys.exit(1)


def maybe_downscale(raw: bytes, fallback_mime: str) -> tuple[bytes, str]:
    """Return (bytes, mime) — downscaled to <= MAX_DIM if larger, else original.

    Falls back to the input bytes + caller's mime if Pillow is unavailable or
    decoding fails. JPEG is forced when actually resizing, since transparency
    isn't useful for vision-model description and JPEG compresses far smaller.
    """
    try:
        from PIL import Image, ImageOps  # type: ignore
    except ImportError:
        return raw, fallback_mime

    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)  # honour camera rotation
        w, h = img.size
        if max(w, h) <= MAX_DIM:
            return raw, fallback_mime
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
        if img.mode not in ("RGB", "L"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "RGBA":
                bg.paste(img, mask=img.split()[-1])
            else:
                bg.paste(img.convert("RGB"))
            img = bg
        out = io.BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return out.getvalue(), "image/jpeg"
    except Exception:
        return raw, fallback_mime


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
        raw = f.read()
    data, mime = maybe_downscale(raw, mime)
    return base64.standard_b64encode(data).decode(), mime


def build_image_part(source: str) -> dict:
    b64, meta = load_image(source)
    if b64:
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{meta};base64,{b64}"},
        }
    return {"type": "image_url", "image_url": {"url": meta}}


def ask_openrouter(
    source: str, question: str, api_key: str, model: str = OPENROUTER_MODEL
) -> str:
    payload = {
        "model": model,
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
        timeout=OPENROUTER_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    # A 200 from OpenRouter can still be an error envelope ({"error": {...}}) when
    # the free model is rate-limited or unavailable — indexing ["choices"] blindly
    # then dies with a bare KeyError. Surface a clean message instead.
    choices = data.get("choices")
    if not choices:
        err = data.get("error")
        msg = err.get("message") if isinstance(err, dict) else err
        raise RuntimeError(f"OpenRouter returned no choices: {msg or data}")
    return choices[0]["message"]["content"]


def ask_gemini(
    source: str, question: str, api_key: str, model: str = GEMINI_MODEL
) -> str:
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
        f"{model}:generateContent?key={api_key}"
    )
    resp = httpx.post(url, json=payload, timeout=GEMINI_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    # A 200 from Gemini can still carry no usable text: the prompt may be blocked
    # (promptFeedback.blockReason), or the candidate may stop on SAFETY/RECITATION
    # with no parts. Indexing ["candidates"][0]…["text"] blindly then dies with a
    # bare KeyError/IndexError and wrongly trips the OpenRouter fallback, hiding
    # the real reason. Surface a clean message instead — mirrors ask_openrouter.
    block = data.get("promptFeedback", {}).get("blockReason")
    if block:
        raise RuntimeError(f"Gemini blocked the prompt: {block}")
    candidates = data.get("candidates")
    if not candidates:
        raise RuntimeError(f"Gemini returned no candidates: {data}")
    parts = candidates[0].get("content", {}).get("parts")
    if not parts:
        reason = candidates[0].get("finishReason", "unknown")
        raise RuntimeError(f"Gemini returned no content (finishReason: {reason})")
    return parts[0]["text"]


def ask_gemini_with_retry(
    source: str, question: str, api_key: str, model: str = GEMINI_MODEL, attempts: int = 2
) -> str:
    """Call Gemini, retrying transient failures (429 rate limit, 5xx server
    errors such as 503 overloaded) with backoff.

    Honours the Retry-After header when present (capped at 8s so the tool fails
    over to the next provider quickly instead of stalling the LINE reply),
    otherwise falls back to 1s/2s backoff. Only one local retry is attempted —
    a persistently-overloaded model is better escaped via the provider chain
    (a different pinned model / OpenRouter) than hammered in place.
    """
    last_err: Exception | None = None
    for i in range(attempts):
        try:
            return ask_gemini(source, question, api_key, model)
        except httpx.HTTPStatusError as e:
            last_err = e
            if e.response.status_code in RETRYABLE_STATUS and i < attempts - 1:
                wait = 2**i
                ra = e.response.headers.get("retry-after", "")
                if ra.isdigit():
                    wait = min(int(ra), 8)
                time.sleep(wait)
                continue
            raise
    assert last_err is not None
    raise last_err


def main() -> None:
    args = sys.argv[1:]
    if not args:
        die("Usage: run.py <source> [question]")

    source = args[0]
    question = " ".join(args[1:]).strip() if len(args) > 1 else ""
    if not question:
        question = DEFAULT_QUESTION

    # Prefer keys injected by the profile system; fall back to named env vars.
    gm_key = os.environ.get("GARUDUST_API_KEY") or os.environ.get("GOOGLE_AI_API_KEY", "")
    or_key = os.environ.get("GARUDUST_FALLBACK_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")

    # Provider chain, tried in order until one returns an answer. Each link is
    # (label, callable). Gemini is preferred — far better Thai output and a more
    # generous free tier than the OpenRouter free vision model (which hallucinated
    # garbled text). The second Gemini link reuses the same key but a different
    # pinned model: when the primary is 503-overloaded the lighter model is
    # usually still up, so we stay on Gemini quality instead of dropping to the
    # OpenRouter free tier. OpenRouter is the last resort.
    chain: list[tuple[str, object]] = []
    if gm_key:
        chain.append((
            f"Gemini ({GEMINI_MODEL})",
            lambda: ask_gemini_with_retry(source, question, gm_key, GEMINI_MODEL),
        ))
        if GEMINI_FALLBACK_MODEL and GEMINI_FALLBACK_MODEL != GEMINI_MODEL:
            chain.append((
                f"Gemini ({GEMINI_FALLBACK_MODEL})",
                lambda: ask_gemini_with_retry(
                    source, question, gm_key, GEMINI_FALLBACK_MODEL
                ),
            ))
    if or_key:
        chain.append((
            f"OpenRouter ({OPENROUTER_MODEL})",
            lambda: ask_openrouter(source, question, or_key, OPENROUTER_MODEL),
        ))

    if not chain:
        die("Set GOOGLE_AI_API_KEY or OPENROUTER_API_KEY to use view_image.")

    errors: list[str] = []
    result: str | None = None
    for i, (label, call) in enumerate(chain):
        try:
            result = call()  # type: ignore[operator]
            break
        except Exception as e:  # noqa: BLE001 — any failure → try next link
            errors.append(f"{label}: {scrub(e)}")
            if i < len(chain) - 1:
                print(
                    f"[view_image: {label} failed ({scrub(e)}); trying next provider]",
                    file=sys.stderr,
                )

    if result is None:
        die("all vision providers failed — " + " | ".join(errors))

    print(result)


if __name__ == "__main__":
    # Wrap main so any uncaught exception exits as a single scrubbed line rather
    # than a full Python traceback — a traceback would print the failing Gemini
    # URL (with ?key=…) into the captured stderr that lands in conversation logs.
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        die(f"{type(e).__name__}: {e}")
