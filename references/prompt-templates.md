# Try-on image prompt templates

## Why a fixed base portrait

Feeding the user's **real photo** into image-to-image and asking for new clothes does not
work: the model re-renders the face and the person changes. Verified across high fidelity,
composition-locked and single-garment-swap variants — every attempt returned a different
face. Do not spend credits retrying this.

The reliable method is **character consistency by reference chain**:

1. Create one base portrait once (or reuse an existing one) — a full-body standing figure on
   a plain cream-beige studio wall, soft daylight, phone-photo realism.
2. For every new outfit, pass that base portrait as `image1` with `input_fidelity: "high"` and
   change only the clothing paragraph.
3. Reuse the same base file across days so the whole series looks like one shoot.

Keep the base portrait out of the published repo if it was derived from a real person.

## Base portrait prompt (run once)

```
Full-body photo of a young East Asian woman in her mid-20s standing in a plain
cream-beige empty room, soft natural daylight from the left, no furniture,
no props. Wearing a fitted cream-white ribbed knit short-sleeve crop top and
high-waisted black straight-leg trousers, black leather loafers, white baseball
cap. Relaxed natural standing pose, arms at sides. Phone-camera realism,
realistic fabric texture, sharp focus, vertical full-body framing head to feet.
```

## Outfit swap template

```
Keep the EXACT same woman as the reference image: identical face, identical white
baseball cap, identical hairstyle, identical body proportions, identical pose,
identical cream-beige empty room background, identical soft daylight and camera
angle, identical phone-photo realism and full-body framing.

Change ONLY her clothing to this outfit: <garment 1 with fit and material>,
<garment 2 with fit and material>, <shoes>, <bag>. <mood in 3-5 words>.
No other changes to the person or the scene.
```

Rules that keep consistency:

- Always restate the whole identity list, even when it feels repetitive.
- Describe garments concretely: `high-waisted black straight-leg ankle-length tailored
  trousers`, not `black trousers`.
- One outfit per call. Do not ask for multiple looks in one image.
- For a look that intentionally drops the cap (e.g. date night), say so explicitly and add
  `keep her hairstyle exactly as in the reference`.
- If a garment keeps coming out wrong, retry once with a more literal description. Do not
  loop more than once — the cost is real.

## Post-processing

Run `scripts/blur_edges.py` on the generated folder. It crops the mirror seam (~5% left),
feathers a Gaussian blur inwards and exports `look_1..N.jpg` in filename order, so numbering
matches the `looks` array in `looks.json`.

Adjust `--crop-left` / `--crop-bottom` if the source images have a different frame or floor line.
