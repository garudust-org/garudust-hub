#!/usr/bin/env python3
import sys, os, json, time
import httpx

HF_API = "https://router.huggingface.co/hf-inference/models"
DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"
MAX_RETRIES = 5
RETRY_DELAYS = [2, 4, 8, 16, 30]


def die(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) < 3:
        die("Usage: run.py <prompt> <output_path> [width] [height]")

    prompt = sys.argv[1].strip()
    output_path = sys.argv[2].strip()

    width, height = 1024, 576
    try:
        if len(sys.argv) > 3 and sys.argv[3].strip():
            width = int(sys.argv[3])
        if len(sys.argv) > 4 and sys.argv[4].strip():
            height = int(sys.argv[4])
    except ValueError:
        die("width and height must be integers")

    if not prompt:
        die("prompt is required")
    if not output_path:
        die("output_path is required")

    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        die("HF_TOKEN environment variable is not set (get a free token at huggingface.co/settings/tokens)")

    url = f"{HF_API}/{DEFAULT_MODEL}"
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": width,
            "height": height,
            "num_inference_steps": 4,
        },
    }

    print(f"Generating {width}×{height} image with {DEFAULT_MODEL}...", file=sys.stderr)

    image_bytes = None
    with httpx.Client(timeout=120) as client:
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.post(
                    url,
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                )
            except httpx.RequestError as e:
                die(f"network error: {e}")

            # Model still loading — HF returns 503 with estimated_time
            if resp.status_code == 503:
                try:
                    body = resp.json()
                    wait = int(body.get("estimated_time", RETRY_DELAYS[attempt]))
                    wait = min(wait, 30)
                except Exception:
                    wait = RETRY_DELAYS[attempt]
                if attempt < MAX_RETRIES - 1:
                    print(f"Model loading — retrying in {wait}s (attempt {attempt + 1}/{MAX_RETRIES})...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                die("model still loading after max retries — try again in a moment")

            if resp.status_code == 429:
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAYS[attempt]
                    print(f"Rate limited — retrying in {wait}s (attempt {attempt + 1}/{MAX_RETRIES})...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                die("rate limited — try again later")

            if resp.status_code != 200:
                try:
                    err = resp.json()
                    die(err.get("error") or resp.text[:200])
                except Exception:
                    die(f"HTTP {resp.status_code}: {resp.text[:200]}")

            image_bytes = resp.content
            break

    if not image_bytes:
        die("no image returned")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(image_bytes)

    print(json.dumps({
        "success": True,
        "output_path": output_path,
        "model": DEFAULT_MODEL,
        "width": width,
        "height": height,
        "size_kb": len(image_bytes) // 1024,
    }, indent=2))


if __name__ == "__main__":
    main()
