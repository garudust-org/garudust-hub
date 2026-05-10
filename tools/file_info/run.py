#!/usr/bin/env python3
import sys, os, json, mimetypes

path = sys.argv[1]

if not os.path.exists(path):
    print(f"Error: file not found: {path}", file=sys.stderr)
    sys.exit(1)

if not os.path.isfile(path):
    print(f"Error: not a file: {path}", file=sys.stderr)
    sys.exit(1)

stat = os.stat(path)
size = stat.st_size

def human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"

mime, _ = mimetypes.guess_type(path)
ext = os.path.splitext(path)[1].lower()

is_text = False
encoding = None
lines = None
words = None

if mime and mime.startswith("text") or ext in {".txt", ".md", ".csv", ".yaml", ".yml", ".json", ".toml", ".rs", ".py", ".js", ".ts", ".sh"}:
    for enc in ("utf-8", "latin-1"):
        try:
            with open(path, encoding=enc) as f:
                content = f.read()
            is_text = True
            encoding = enc
            lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            words = len(content.split())
            break
        except (UnicodeDecodeError, PermissionError):
            continue

result = {
    "size_bytes": size,
    "size_human": human_size(size),
    "mime_type": mime or "application/octet-stream",
    "extension": ext or "(none)",
    "is_text": is_text,
}
if is_text:
    result["encoding"] = encoding
    result["lines"] = lines
    result["words"] = words

print(json.dumps(result, indent=2))
