#!/usr/bin/env python3
"""Thai TTS tool — calls a provider via GARUDUST_BASE_URL / GARUDUST_API_KEY.

Tested with iApp TTS v3 (https://api.iapp.co.th/tts/v3).
Compatible with any REST TTS provider that accepts JSON body:
  {"text": "...", "speaker_id": N, "speed": F}
and returns raw audio bytes.

Config (set in ~/.garudust/.env):
  GARUDUST_BASE_URL   - TTS API endpoint  (via tools.tts.model profile)
  GARUDUST_API_KEY    - API key           (via tools.tts.model profile)
  TTS_SPEAKER_ID      - voice index, default 0
  TTS_SPEED           - speech rate 0.5-2.0, default 1.0
"""

import os
import sys
import uuid

try:
    import httpx
except ImportError:
    print("error: httpx not installed — run: pip install httpx", file=sys.stderr)
    sys.exit(1)

def main() -> None:
    if len(sys.argv) < 2:
        print("error: text argument required", file=sys.stderr)
        sys.exit(1)

    text = sys.argv[1]
    base_url = os.environ.get("GARUDUST_BASE_URL", "").rstrip("/")
    api_key  = os.environ.get("GARUDUST_API_KEY", "")
    speaker_id = int(os.environ.get("TTS_SPEAKER_ID", "0"))
    speed      = float(os.environ.get("TTS_SPEED", "1.0"))

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
            json={"text": text, "speaker_id": speaker_id, "speed": speed},
            timeout=30,
        )
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        print(f"error: TTS API returned {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.RequestError as e:
        print(f"error: TTS API request failed: {e}", file=sys.stderr)
        sys.exit(1)

    content_type = resp.headers.get("content-type", "")
    ext = "mp3" if "mpeg" in content_type else "wav"
    out_path = f"/tmp/tts_{uuid.uuid4().hex}.{ext}"

    with open(out_path, "wb") as f:
        f.write(resp.content)

    print(out_path)

if __name__ == "__main__":
    main()
