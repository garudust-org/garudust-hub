---
name: facebook-workflow
description: Research a topic, summarise it as a Facebook post, generate a matching image, and publish to a Facebook Page — all in one workflow
version: 1.3.0
permissions:
  facebook_post: true
  generate_image: true
  web_search: true
  web_fetch: true
  terminal: false
---

## When to use this skill

Load this skill whenever the user asks to post, publish, or share content on a Facebook Page — including when they provide a topic and want the agent to research, write, and post automatically.

## Setup check

Before starting, verify:

1. `FACEBOOK_ACCESS_TOKEN` is set in the environment — if not, ask the user to set it:
   ```
   export FACEBOOK_ACCESS_TOKEN=your_token_here
   ```
2. `HF_TOKEN` is set (for image generation) — if not, ask the user to set it:
   ```
   export HF_TOKEN=your_token_here
   ```
3. The user has provided a `page_id` — if not, ask. Found in Page settings or URL (`facebook.com/<page>` → Settings → Page ID).

## Step 1 — Research the topic

When the user provides a topic (not a pre-written post):

1. Use `web_search` to find 3–5 recent, credible sources about the topic
2. Use `web_fetch` to read the most relevant articles in full
3. Extract the key facts, figures, and quotes
4. Identify the angle most relevant and engaging for the page's audience

## Step 2 — Write the post

Compose a Facebook post from the research:

- **First 125 characters must hook the reader** — this is what shows before "See more"
- Keep total length under 400 characters for best reach; use "See more" intentionally for longer content
- Use short paragraphs and line breaks — no walls of text
- Add 3–5 relevant hashtags at the end
- Use emojis sparingly and only if they fit the brand tone
- Cite the source briefly if quoting a stat or claim (e.g. "— Reuters")
- Do **not** use all-caps, excessive punctuation, or link shorteners in the body

## Step 3 — Generate an image

Always generate an image to accompany the post using the `generate_image` tool (requires `HF_TOKEN`):

1. Write an image prompt based on the post content — be specific about subject, mood, style, and composition
2. Choose dimensions:
   - **1024 × 576** — landscape (default, good for news/article posts)
   - **1080 × 1080** — square (better for feed visibility)
3. Save to `/tmp/fb_post_image.png`

Good image prompt patterns:
- News/tech: `"[subject], cinematic lighting, editorial photography style, sharp detail"`
- AI/science: `"[concept] visualized as futuristic digital art, dark background, glowing elements"`
- Lifestyle: `"[scene], golden hour lighting, wide angle, vivid colors, travel photography style"`

If the user provides their own image, use that instead and skip generation.

## Step 4 — Post

Post immediately after image generation without asking for confirmation.

Call `facebook_post` with:
- `page_id` — the Page ID
- `message` — the confirmed post text
- `image_path` — absolute path to the image (never empty for this workflow)

## Step 5 — Report

- Confirm success: "Posted to Facebook Page — post ID: `{post_id}`"
- If the tool returns an error, surface the message clearly and suggest checking the token or page_id
