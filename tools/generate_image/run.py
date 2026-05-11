#!/usr/bin/env python3
import sys, os, json, time
import httpx

IDEOGRAM_API = "https://api.ideogram.ai/generate"
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]

ASPECT_RATIOS = [
    (16 / 9,  "ASPECT_16_9"),
    (3 / 2,   "ASPECT_3_2"),
    (4 / 3,   "ASPECT_4_3"),
    (1 / 1,   "ASPECT_1_1"),
    (3 / 4,   "ASPECT_3_4"),
    (2 / 3,   "ASPECT_2_3"),
    (9 / 16,  "ASPECT_9_16"),
]


def nearest_aspect(width: int, height: int) -> str:
    ratio = width / height
    return min(ASPECT_RATIOS, key=lambda x: abs(x[0] - ratio))[1]


def die(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) < 3:
        die("Usage: run.py <prompt> <output_path> [width] [height]")

    prompt = sys.argv[1].strip()
    output_path = sys.argv[2].strip()

    width, height = 1200, 630
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

    api_key = os.environ.get("IDEOGRAM_API_KEY", "").strip()
    if not api_key:
        die("IDEOGRAM_API_KEY environment variable is not set")

    aspect_ratio = nearest_aspect(width, height)
    print(f"Generating image ({aspect_ratio})...", file=sys.stderr)

    payload = {
        "image_request": {
            "prompt": prompt,
            "model": "V_2",
            "aspect_ratio": aspect_ratio,
            "magic_prompt_option": "AUTO",
        }
    }

    image_url = None
    with httpx.Client(timeout=120) as client:
        for attempt in range(MAX_RETRIES):
            try:
                resp = client.post(
                    IDEOGRAM_API,
                    headers={"Api-Key": api_key, "Content-Type": "application/json"},
                    json=payload,
                )
            except httpx.RequestError as e:
                die(f"network error: {e}")

            if resp.status_code in (429, 500, 502, 503):
                if attempt < MAX_RETRIES - 1:
                    wait = RETRY_DELAYS[attempt]
                    reason = "rate limited" if resp.status_code == 429 else f"server error {resp.status_code}"
                    print(f"{reason} — retrying in {wait}s (attempt {attempt + 1}/{MAX_RETRIES})...", file=sys.stderr)
                    time.sleep(wait)
                    continue
                die(f"HTTP {resp.status_code} after {MAX_RETRIES} attempts — try again later")

            if resp.status_code != 200:
                try:
                    err = resp.json()
                    die(err.get("message") or resp.text[:200])
                except Exception:
                    die(f"HTTP {resp.status_code}: {resp.text[:200]}")

            data = resp.json().get("data", [])
            if not data:
                die("no image returned from Ideogram")

            image_url = data[0]["url"]
            break

        # Download the generated image
        try:
            img_resp = client.get(image_url, follow_redirects=True)
            img_resp.raise_for_status()
        except httpx.RequestError as e:
            die(f"failed to download image: {e}")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(img_resp.content)

    print(json.dumps({
        "success": True,
        "output_path": output_path,
        "aspect_ratio": aspect_ratio,
        "size_kb": len(img_resp.content) // 1024,
    }, indent=2))


if __name__ == "__main__":
    main()
