#!/usr/bin/env python3
"""Edge-blur pass for AI try-on images.

Removes the mirror-frame seam and hard studio edges by cropping a small border and
feathering a Gaussian blur inwards, so the subject sits on a soft cream background.

Usage:
    python blur_edges.py <input_dir> <output_dir> [--prefix look] [--crop-left 0.055]
                        [--crop-right 0.015] [--crop-top 0.01] [--crop-bottom 0.04]
                        [--blur 16] [--quality 85]

Input files are processed in sorted filename order and written as
    <prefix>_1.jpg, <prefix>_2.jpg, ...
so their order matches the look order in looks.json.
"""
import argparse
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError:
    sys.exit("Pillow is required: pip install pillow")


def feather_mask(size, fade_x, fade_y, steps=24):
    """Opaque at the very edge, transparent once inset by fade_x / fade_y."""
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    for s in range(steps):
        alpha = int(255 * (1 - s / steps))
        dx = s * fade_x // steps
        dy = s * fade_y // steps
        draw.rectangle([dx, dy, w - 1 - dx, h - 1 - dy], outline=alpha)
    return mask


def process(src, dst, args):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    im = im.crop((
        int(w * args.crop_left),
        int(h * args.crop_top),
        int(w * (1 - args.crop_right)),
        int(h * (1 - args.crop_bottom)),
    ))
    w, h = im.size
    blurred = im.filter(ImageFilter.GaussianBlur(args.blur))
    mask = feather_mask((w, h), int(w * 0.10), int(h * 0.07))
    out = Image.composite(blurred, im, mask)
    out.save(dst, "JPEG", quality=args.quality)
    return dst, os.path.getsize(dst) // 1024


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input_dir")
    p.add_argument("output_dir")
    p.add_argument("--prefix", default="look")
    p.add_argument("--crop-left", type=float, default=0.055)
    p.add_argument("--crop-right", type=float, default=0.015)
    p.add_argument("--crop-top", type=float, default=0.01)
    p.add_argument("--crop-bottom", type=float, default=0.04)
    p.add_argument("--blur", type=int, default=16)
    p.add_argument("--quality", type=int, default=85)
    args = p.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    files = sorted(
        f for f in os.listdir(args.input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    )
    if not files:
        sys.exit(f"No images found in {args.input_dir}")

    for i, f in enumerate(files, 1):
        dst = os.path.join(args.output_dir, f"{args.prefix}_{i}.jpg")
        path, kb = process(os.path.join(args.input_dir, f), dst, args)
        print(f"{path}  {kb} KB")


if __name__ == "__main__":
    main()
