#!/usr/bin/env python3
import sys, os, json
import urllib.parse
import httpx


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

    encoded = urllib.parse.quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&nologo=true&model=flux"
    )

    print(f"Generating {width}×{height} image...", file=sys.stderr)

    try:
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
    except httpx.RequestError as e:
        die(f"network error: {e}")

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(resp.content)

    print(json.dumps({
        "success": True,
        "output_path": output_path,
        "width": width,
        "height": height,
        "size_kb": len(resp.content) // 1024,
    }, indent=2))


if __name__ == "__main__":
    main()
