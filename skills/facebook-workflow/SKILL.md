---
name: facebook-workflow
description: Research a topic, summarise it as a Facebook post, generate a matching image, and publish to a Facebook Page — all in one workflow
version: 1.5.0
permissions:
  facebook_post: true
  generate_image: true
  web_search: true
  web_fetch: true
  terminal: true
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

Write the post as a **full, detailed article** — not a summary. Cover every key fact, figure, quote, background context, and implication found in the research. Use as much of the available context window as possible; do not shorten or condense.

- **First 125 characters must hook the reader** — this is what shows before "See more"
- Write in full paragraphs with detail — avoid bullet points and short summaries
- Use line breaks between paragraphs for readability
- Include background context, expert quotes, data, and analysis
- Add 3–5 relevant hashtags at the end
- Use emojis sparingly and only if they fit the brand tone
- Cite the source inline when quoting a stat or claim (e.g. "— Reuters")
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

### Step 3b — Add text overlay

After the image is saved, add a keyword phrase from the post content onto the image using `run_command`:

1. Pick the single most important phrase from the post — max 6 words, in Thai or English matching the post language
2. Run:

```bash
uv run --with pillow -c "
from PIL import Image, ImageDraw, ImageFont
import textwrap, os

img = Image.open('/tmp/fb_post_image.png').convert('RGBA')
w, h = img.size
overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
draw = ImageDraw.Draw(overlay)

bar_h = int(h * 0.15)
draw.rectangle([(0, h - bar_h), (w, h)], fill=(0, 0, 0, 175))

try:
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', int(bar_h * 0.45))
except:
    font = ImageFont.load_default()

text = '<KEYWORD_PHRASE>'
bbox = draw.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(((w - tw) / 2, h - bar_h + (bar_h - th) / 2), text, font=font, fill=(255, 255, 255, 255))

out = Image.alpha_composite(img, overlay).convert('RGB')
out.save('/tmp/fb_post_image.png')
print('overlay done')
"
```

Replace `<KEYWORD_PHRASE>` with the chosen phrase before running. The result overwrites `/tmp/fb_post_image.png`.

## Step 4 — Post

Post immediately after image generation without asking for confirmation.

Call `facebook_post` with:
- `page_id` — the Page ID
- `message` — the confirmed post text
- `image_path` — absolute path to the image (never empty for this workflow)

> **CRITICAL — you MUST call the tool and wait for its result:**
> - Do NOT report success until `facebook_post` has been called and a tool result has been returned by the system.
> - Do NOT assume or simulate the outcome. If you have not received a tool result block, the post has NOT been sent.
> - Do NOT write "I have posted" or "Posted successfully" before you see the tool result.
> - The workflow is incomplete if the tool was never called, regardless of what was written or generated in prior steps.

## Step 5 — Report

After the tool result is received:

- If the result contains a `post_id`, confirm success: "Posted to Facebook Page — post ID: `<actual_id_from_tool_result>`"
  - The `post_id` must be the exact value returned by the tool — never use a placeholder or a made-up ID.
- If the result contains an error, surface the message clearly and suggest checking the token or page_id.
- If no tool result was received (tool was not called), report: "Post was not sent — facebook_post was not called. Please retry."
