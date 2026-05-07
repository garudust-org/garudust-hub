#!/usr/bin/env python3
import sys
import httpx
from bs4 import BeautifulSoup

url = sys.argv[1]

try:
    response = httpx.get(url, follow_redirects=True, timeout=10)
    response.raise_for_status()
except httpx.InvalidURL:
    print(f"Error: invalid URL: {url}", file=sys.stderr)
    sys.exit(1)
except httpx.HTTPStatusError as e:
    print(f"Error: HTTP {e.response.status_code}", file=sys.stderr)
    sys.exit(1)
except httpx.RequestError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

soup = BeautifulSoup(response.text, "html.parser")
title = soup.title.string.strip() if soup.title and soup.title.string else None

if not title:
    print("Error: no <title> found", file=sys.stderr)
    sys.exit(1)

print(title)
