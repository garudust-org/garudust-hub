---
name: fetch-title
description: Fetch the HTML <title> of any webpage using web_fetch — no Python or uv dependency required. Replaces the fetch_title hub tool.
version: 1.0.0
---

## When to use this skill

Load this skill whenever the user asks for the title of a webpage, wants to identify a URL, or needs to label a link without reading its full content.

## How to fetch a page title

Call `web_fetch` with the URL the user provided.

Then extract the content between `<title>` and `</title>` from the returned HTML. The title is typically near the top of the `<head>` section.

Return the extracted title to the user, trimmed of leading/trailing whitespace.

## Edge cases

- **No `<title>` tag** — tell the user no title was found and offer to summarise the page content instead.
- **`<title>` is empty or whitespace-only** — treat as "no title found".
- **Redirect pages** — `web_fetch` follows redirects automatically; use the title from the final destination.
- **Encoding issues** — `web_fetch` returns decoded text; the title should already be readable. If you see HTML entities (e.g. `&amp;`, `&#39;`), decode them before returning.
- **JavaScript-rendered titles** — `web_fetch` retrieves the raw HTML. If the title appears to be a placeholder (e.g. "Loading…", "React App"), note that the real title may require JavaScript execution, and offer to summarise the visible text content instead.
- **Invalid or unreachable URL** — report the error from `web_fetch` directly.

## Do not

- Do not use the `fetch_title` hub tool — this skill replaces it with no subprocess or Python dependency.
- Do not call `run_command` or `curl` to fetch the page.
