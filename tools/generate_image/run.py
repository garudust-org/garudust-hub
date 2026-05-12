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


def add_overlay(image_path: str, text: str) -> None:
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(image_path).convert("RGBA")
    w, h = img.size
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    bar_h = int(h * 0.15)
    draw.rectangle([(0, h - bar_h), (w, h)], fill=(0, 0, 0, 175))

    font_size = int(bar_h * 0.45)
    font = None
    for font_path in [
        # macOS — Thai support
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Thonburi.ttc",
        "/System/Library/Fonts/Supplemental/Tahoma.ttf",
        # Linux — Thai support
        "/usr/share/fonts/truetype/tlwg/Garuda-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
        "/usr/share/fonts/noto/NotoSansThai-Bold.ttf",
        # Fallbacks (Latin only)
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/liberation/LiberationSans-Bold.ttf",
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except Exception:
                continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((w - tw) / 2, h - bar_h + (bar_h - th) / 2),
        text,
        font=font,
        fill=(255, 255, 255, 255),
    )

    out = Image.alpha_composite(img, overlay).convert("RGB")
    out.save(image_path)


def main() -> None:
    if len(sys.argv) < 3:
        die("Usage: run.py <prompt> <output_path> [width] [height] [overlay_text]")

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

    # overlay_text is optional — unsubstituted placeholder arrives as literal "{overlay_text}"
    overlay_text = ""
    if len(sys.argv) > 5:
        raw = sys.argv[5].strip()
        if raw and raw != "{overlay_text}":
            overlay_text = raw

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

    if overlay_text:
        print(f"Adding overlay: {overlay_text!r}", file=sys.stderr)
        add_overlay(output_path, overlay_text)

    print(json.dumps({
        "success": True,
        "output_path": output_path,
        "model": DEFAULT_MODEL,
        "width": width,
        "height": height,
        "size_kb": len(image_bytes) // 1024,
        "overlay_text": overlay_text or None,
    }, indent=2))


if __name__ == "__main__":
    main()
