---
name: daily-outfit-lookbook
description: Build a daily 5-look outfit lookbook for a specific person — reads their personal photos, wardrobe shopping screenshots and saved inspiration images, generates character-consistent try-on images on a fixed cream studio base portrait, blurs the frame edges, and renders a self-contained HTML page where every item is tagged as owned / in-cart / to-buy with a Taobao search link. This skill should be used when the user asks for daily outfit recommendations, personal styling based on their own photos or wardrobe, virtual try-on effect images, or an outfit inspo page they can shop from.
agent_created: true
---

# Daily Outfit Lookbook

## Purpose

Turn a person's own materials into a shop-ready daily lookbook: 5 outfits, each shown as an
image of a consistent character wearing the look on a cream studio background, with the exact
items listed, their provenance marked, and a search link for anything missing.

The value is not the pretty picture — it is that every look is assembled from garments the
person already owns or has already saved, so it can be worn today.

## When to use

- "每天推荐几套搭配" / "每日穿搭灵感" / "帮我搭几套"
- "按我的照片和衣柜做搭配" / "用我的衣柜单品"
- "生成上身效果图" / "virtual try-on"
- Recurring daily push of outfit ideas as an HTML page

Do not use for one-off styling questions with no personal material (answer directly), or for
creating product photos for a storefront.

## Workflow

### 1. Locate the source material

Ask for, or auto-detect, three inputs. Desktop defaults:

| Input | Default path | Purpose |
|---|---|---|
| Personal photos | `~/Desktop/个人照片/` | Face, hair, skin tone, body type, colours actually worn |
| Wardrobe | `~/Desktop/我的衣柜/` | Taobao/Tmall screenshots = intent + price |
| Inspiration | `~/Desktop/穿搭灵感库/` | Styling tricks only |

Read 4–6 photos, 8–15 wardrobe screenshots, 3–5 inspiration images. See
`references/style-profiling.md` for what to extract and how to tag provenance.

### 2. Fix the base portrait

Character consistency comes from a **reference chain**, never from the user's real photo —
image-to-image on a real face re-renders the face. Use an existing base portrait, or generate
one with the prompt in `references/prompt-templates.md`. Keep the same base file across days.

Store it at a stable path and reuse it, e.g. `work/base_portrait.jpg`.

### 3. Generate the 5 looks

For each look, call the image tool with `image1 = base portrait`, `input_fidelity: "high"`,
and the outfit-swap template from `references/prompt-templates.md`. One outfit per call.
Vary occasions across the five: commute, casual, statement/monochrome, vintage/literary, date.

Write outputs to `work/YYYY-MM-DD/raw/`. Retry a failed image at most once.

### 4. Blur the frame edges

```bash
python scripts/blur_edges.py work/YYYY-MM-DD/raw work/YYYY-MM-DD/wear --prefix look
```

Crops the mirror seam and feathers a Gaussian blur into the cream wall. Output `look_1..N.jpg`
in filename order — this order must match the `looks` array.

### 5. Write looks.json

Fill the schema documented at the top of `scripts/build_lookbook.py`: date, title, subtitle,
analysis block (palette + two short paragraphs), and 5 looks with 4–5 items each. Every item
needs `name`, `note` (fit requirement, plus `衣柜收藏 ¥xx` when the price is known), `keyword`
(fit-specific search query) and `source` (`owned` / `cart` / `buy`).

At least 3 items per look should be `owned` or `cart`.

### 6. Render and present

```bash
python scripts/build_lookbook.py lookbook.json lookbook-YYYY-MM-DD.html
```

The HTML embeds images as base64, so it is self-contained. Present it to the user.

### 7. Wire the daily automation (only if asked)

Create a recurring automation that repeats steps 1–6, and pin these facts into the prompt so
future runs are self-contained: base portrait path, source folder paths, the person's style
profile, the script paths, and "every day must differ from previous days".

## Guardrails

- **Cost**: each image costs roughly 5–10 credits. Five looks per day ≈ 25–50. Say so before
  the first run and mention it when adding a schedule.
- **Identity**: never promise the user's real face on a generated body. Explain the reference
  chain instead and offer real alternatives (product-page model shots, in-app AI try-on,
  returns-insurance try-on).
- **Privacy**: do not publish or commit the user's real photos, or a base portrait derived from
  them, into a public repo. Keep those in a local work directory.
- **Wardrobe screenshots are intent, not ownership** — get the badges right; it is the whole
  point of the page.
- **Fit over brand**: always specify the construction that makes the garment work (fabric
  drape, hem position, sleeve length), not a brand name.
