#!/usr/bin/env python3
"""Thai TTS tool — calls iApp TTS API via GARUDUST_BASE_URL / GARUDUST_API_KEY.

Endpoint: POST https://api.iapp.co.th/v3/store/audio/tts
Returns raw 16-bit PCM at 24kHz mono; this script wraps it in a WAV header.

Config (set in ~/.garudust/.env):
  GARUDUST_BASE_URL   - TTS API endpoint  (via tools.tts.model profile)
  GARUDUST_API_KEY    - API key           (via tools.tts.model profile)
"""

import os
import sys
import struct
import uuid

try:
    import httpx
except ImportError:
    print("error: httpx not installed — run: pip install httpx", file=sys.stderr)
    sys.exit(1)


def pcm_to_wav(pcm: bytes, sample_rate: int = 24000, channels: int = 1, bits: int = 16) -> bytes:
    byte_rate   = sample_rate * channels * bits // 8
    block_align = channels * bits // 8
    data_size   = len(pcm)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + data_size, b"WAVE",
        b"fmt ", 16,
        1,            # PCM
        channels,
        sample_rate,
        byte_rate,
        block_align,
        bits,
        b"data", data_size,
    )
    return header + pcm


def main() -> None:
    if len(sys.argv) < 2:
        print("error: text argument required", file=sys.stderr)
        sys.exit(1)

    text     = sys.argv[1]
    base_url = os.environ.get("GARUDUST_BASE_URL", "").rstrip("/")
    api_key  = os.environ.get("GARUDUST_API_KEY", "")

    if not base_url:
        print("error: GARUDUST_BASE_URL not set — add tools.tts.model in config.yaml", file=sys.stderr)
        sys.exit(1)
    if not api_key:
        print("error: GARUDUST_API_KEY not set — add providers.<name>.key in config.yaml", file=sys.stderr)
        sys.exit(1)

    try:
        resp = httpx.post(
            base_url,
            headers={"apikey": api_key, "Content-Type": "application/json"},
            json={"text": text},
            timeout=30,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"error: TTS API returned {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"error: TTS API request failed: {e}", file=sys.stderr)
        sys.exit(1)

    raw = resp.content
    # iApp returns raw PCM (no RIFF header) — wrap it
    wav = pcm_to_wav(raw) if not raw.startswith(b"RIFF") else raw

    out_path = f"/tmp/tts_{uuid.uuid4().hex}.wav"
    with open(out_path, "wb") as f:
        f.write(wav)

    print(out_path)


if __name__ == "__main__":
    main()
