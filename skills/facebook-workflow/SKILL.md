---
name: facebook-workflow
description: Prepare and publish content to a Facebook Page — handles text posts and photo posts via the facebook_post tool
version: 1.0.0
permissions:
  facebook_post: true
  terminal: false
  web_fetch: false
---

## When to use this skill

Load this skill whenever the user asks to post, publish, or share content on a Facebook Page.

## Setup check

Before posting, verify:

1. `FACEBOOK_ACCESS_TOKEN` is set in the environment — if not, ask the user to set it:
   ```
   export FACEBOOK_ACCESS_TOKEN=your_token_here
   ```
2. The user has provided a `page_id` — if not, ask. It is the numeric ID found in Page settings or the URL (`facebook.com/your-page-name` → Settings → Page ID).

## Preparing the message

- Keep the **first 125 characters** compelling — this is what shows before "See more"
- Use line breaks to improve readability, not walls of text
- Add 3–5 relevant hashtags at the end (more than this hurts reach on Facebook)
- Emojis are effective on Facebook — use sparingly and only if they fit the brand tone
- Avoid all-caps, excessive punctuation, and link shorteners in the text body

## Preparing the image

If the user provides an image:
- Confirm the file exists and is JPG or PNG
- Recommended dimensions: **1200 × 630 px** for landscape, **1080 × 1080 px** for square
- If the image needs resizing, use the `image_resize` tool before posting
- Pass the absolute path to `facebook_post`

For a text-only post, pass an empty string as `image_path`.

## Posting

Call `facebook_post` with:
- `page_id` — the Page ID
- `message` — the prepared post text
- `image_path` — absolute path to the image, or `""` for text-only

**Always confirm the final message with the user before calling the tool.** Show them the exact text and image that will be posted and wait for approval.

## After posting

- Report the `post_id` from the tool response
- Confirm success: "Posted to Facebook Page — post ID: `{post_id}`"
- If the tool returns an error, surface the error message clearly and suggest checking the token or page_id
