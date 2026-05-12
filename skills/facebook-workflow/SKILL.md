---
name: facebook-workflow
description: Research a topic, summarise it as a Facebook post, generate a matching image, and publish to a Facebook Page — all in one workflow
version: 2.0.0
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

## Step 2 — Write the post (TEXT OUTPUT — NO TOOL CALLS IN THIS TURN)

🚫 **DO NOT call `generate_image` or `facebook_post` in this turn.**
🚫 **DO NOT write the post inside a tool parameter.**
✅ **Output the post as plain text in your response only.**

Write a post of **at least 200 Thai words** following this structure:

**[ประโยคเกริ่น]** — hook สั้น 1–2 ประโยค ดึงดูดให้คลิก "ดูเพิ่มเติม"

**[ย่อหน้าที่ 1 — ความเป็นมา]** — อธิบายบริบทและความสำคัญของข่าว (3–5 ประโยค)

**[ย่อหน้าที่ 2 — เนื้อหาหลัก]** — รายละเอียดข่าว ตัวเลข ข้อมูล และคำพูดอ้างอิง (3–5 ประโยค)

**[ย่อหน้าที่ 3 — ผลกระทบและวิเคราะห์]** — ความหมายและผลต่ออนาคต (3–5 ประโยค)

**[Call to action]** — 1 ประโยคชวนคอมเมนต์หรือติดตาม

**[Hashtags]** — 3–5 hashtag บรรทัดสุดท้าย

⚠️ เมื่อเขียนครบแล้ว ให้ระบุ `[DRAFT COMPLETE]` ท้ายสุด แล้วจึงไปขั้นตอนถัดไป

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
