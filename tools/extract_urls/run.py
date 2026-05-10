#!/usr/bin/env python3
import sys, json, re
from bs4 import BeautifulSoup

path = sys.argv[1]

try:
    with open(path, encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print(f"Error: file not found: {path}", file=sys.stderr)
    sys.exit(1)
except UnicodeDecodeError:
    print(f"Error: file is not valid UTF-8", file=sys.stderr)
    sys.exit(1)

urls = []

# parse HTML tags first if file looks like HTML
if "<html" in content.lower() or "<a " in content.lower():
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup.find_all(True):
        for attr in ("href", "src", "action"):
            val = tag.get(attr, "")
            if val and val.startswith(("http://", "https://")):
                urls.append(val)

# also extract bare URLs from the raw text
for match in re.finditer(r'https?://[^\s\'"<>)\]]+', content):
    urls.append(match.group())

# deduplicate preserving order
seen = set()
unique = []
for u in urls:
    if u not in seen:
        seen.add(u)
        unique.append(u)

if not unique:
    print("[]")
else:
    print(json.dumps(unique, indent=2))
