---
name: facebook-workflow
description: Research a topic, summarise it as a Facebook post, generate a matching image, and publish to a Facebook Page — all in one workflow
version: 3.0.0
permissions:
  facebook_post: true
  generate_image: true
  web_search: true
  web_fetch: true
  terminal: true
required_tools: [facebook_post]
---

## When to use this skill

Load this skill whenever the user asks to post, publish, or share content on a Facebook Page — including when they provide a topic and want the agent to research, write, and post automatically.

## Setup check

Before starting, verify:

1. `FACEBOOK_ACCESS_TOKEN` is set — if not, ask the user to set it
2. `HF_TOKEN` is set (for image generation) — if not, ask the user to set it
3. The user has provided a `page_id` — if not, ask

## Step 1 — Research

Call `web_search` once, then `web_fetch` once on the best result. Extract key facts, figures, and the main angle. **Stop after 1 search + 1 fetch.**

## Step 2 — Generate image

**In this response, call `generate_image` with:**
- An image prompt based on the topic (specific subject, mood, style)
- Dimensions: `1024` × `576`
- `output_path`: `/tmp/fb_post_image.png`
- `overlay_text`: the single most important phrase (max 6 Thai words)

Good prompt patterns:
- Tech news: `"[subject], cinematic lighting, editorial photography style"`
- AI: `"[concept] as futuristic digital art, dark background, glowing elements"`

> **If generate_image fails:** skip it and proceed directly to Step 3 — call `facebook_post` without `image_path`.

## Step 3 — Post to Facebook

**Immediately after generate_image finishes (or if it failed), call `facebook_post` with:**
- `page_id`: the page ID provided by the user
- `image_path`: `/tmp/fb_post_image.png` (omit or leave empty if generate_image failed)
- `message`: the full post text written inline (see format below)

**Post format (write directly in the `message` parameter — minimum 200 words in Thai):**

```
[ประโยคเกริ่น — hook 1–2 ประโยค]

[ความเป็นมา — บริบทและความสำคัญ 2–3 ประโยค]

[เนื้อหาหลัก — รายละเอียด ตัวเลข ข้อมูล 2–3 ประโยค]

[ผลกระทบ — ความหมายต่ออนาคต 2–3 ประโยค]

[Call to action — 1 ประโยค]

#hashtag1 #hashtag2 #hashtag3
```

> **CRITICAL:** Do NOT report success until `facebook_post` has been called and a tool result has been returned. Do NOT write "Posted successfully" before receiving a tool result.

## Step 4 — Report

- If result contains `post_id`: confirm "Posted — ID: `<exact_id_from_result>`"
- If result contains an error: surface the message and suggest checking token or page_id
- If tool was never called: report "Post was not sent — please retry"
