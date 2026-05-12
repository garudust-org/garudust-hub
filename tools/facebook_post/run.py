#!/usr/bin/env python3
import sys, os, json
import httpx

GRAPH_API = "https://graph.facebook.com/v19.0"


def die(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) < 3:
        die("Usage: run.py <page_id> <message> [image_path]")

    page_id = sys.argv[1].strip()
    message = sys.argv[2].strip()
    image_path = sys.argv[3].strip() if len(sys.argv) > 3 else ""

    token = os.environ.get("FACEBOOK_ACCESS_TOKEN", "").strip()
    if not token:
        die("FACEBOOK_ACCESS_TOKEN environment variable is not set")

    if not page_id:
        die("page_id is required")
    if not message:
        die("message is required")

    word_count = len(message.split())
    if word_count < 100:
        die(
            f"Post content too short ({word_count} words). "
            "Minimum 100 words required. "
            "Rewrite the message parameter with a full article: hook, background (3-5 sentences), "
            "main news (3-5 sentences), analysis (3-5 sentences), call to action, and hashtags."
        )

    try:
        if image_path:
            if not os.path.isfile(image_path):
                die(f"image file not found: {image_path}")
            with open(image_path, "rb") as img:
                resp = httpx.post(
                    f"{GRAPH_API}/{page_id}/photos",
                    data={"caption": message, "access_token": token},
                    files={"source": img},
                    timeout=30,
                )
        else:
            resp = httpx.post(
                f"{GRAPH_API}/{page_id}/feed",
                data={"message": message, "access_token": token},
                timeout=30,
            )
    except httpx.RequestError as e:
        die(f"network error: {e}")

    body = resp.json()

    if resp.status_code != 200:
        error = body.get("error", {})
        die(error.get("message", resp.text))

    post_id = body.get("post_id") or body.get("id", "")
    print(json.dumps({"success": True, "post_id": post_id}, indent=2))


if __name__ == "__main__":
    main()
