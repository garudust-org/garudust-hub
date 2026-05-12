---
name: facebook-workflow
description: Research a topic, summarise it as a Facebook post, generate a matching image, and publish to a Facebook Page — all in one workflow
version: 1.8.0
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

1. Use `web_search` to find the single most recent, credible article about the topic — **stop after one search call**
2. Use `web_fetch` to read **only that one article** — do not fetch additional URLs
3. Extract the key facts, figures, and quotes from it
4. Identify the angle most relevant and engaging for the page's audience

> **Context budget rule:** Limit research to 1 search + 1 fetch. This preserves enough output budget to write a full-length post.

## Step 2 — Write the post

Write the post as a **full, detailed article** — minimum **400 words**. Cover every key fact, figure, quote, background context, and implication found in the research. Do not shorten or condense.

Follow this structure:

1. **Hook** (1–2 sentences, first 125 characters visible before "See more") — must grab attention immediately
2. **Background** (1–2 paragraphs) — why this topic matters, context the reader needs
3. **Main news** (2–3 paragraphs) — the core facts, figures, and developments; cite sources inline (e.g. "— Reuters")
4. **Analysis / implications** (1–2 paragraphs) — what this means going forward, expert quotes if available
5. **Call to action** (1 sentence) — invite the reader to comment, share, or follow
6. **Hashtags** — 3–5 relevant hashtags on their own line

Rules:
- Write in full paragraphs — no bullet points or numbered lists in the post itself
- Use line breaks between paragraphs for readability
- Use emojis sparingly and only where they fit the tone (1–3 max)
- Do **not** use all-caps, excessive punctuation, or link shorteners in the body

## Step 3 — Generate an image

Always generate an image to accompany the post using the `generate_image` tool (requires `HF_TOKEN`):

1. Write an image prompt based on the post content — be specific about subject, mood, style, and composition
2. Choose dimensions:
   - **1024 × 576** — landscape (default, good for news/article posts)
   - **1080 × 1080** — square (better for feed visibility)
3. Save to `/tmp/fb_post_image.png`
4. Set `overlay_text` to the single most important phrase from the post (max 6 words, in Thai or English matching the post language) — this burns the caption directly onto the image

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
