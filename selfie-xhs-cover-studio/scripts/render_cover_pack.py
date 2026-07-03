#!/usr/bin/env python3
"""Render Xiaohongshu cover PNGs with deterministic text overlays.

The image model should create portrait/background layers without text.
This script renders Chinese titles, subtitles, badges, and contact sheets
so the final cover does not suffer from hallucinated or broken text.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_CANVAS = {"width": 1242, "height": 1656}
FONT_CANDIDATES = [
    os.environ.get("XHS_FONT"),
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def find_font() -> str | None:
    for candidate in FONT_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = find_font()
    if font_path:
        return ImageFont.truetype(font_path, size=size)
    return ImageFont.load_default(size=size)


def text_width(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.ImageFont) -> float:
    return draw.textlength(text, font=face)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    if len(words) > 1:
        units = words
        joiner = " "
    else:
        units = list(text)
        joiner = ""

    lines: list[str] = []
    current = ""
    for unit in units:
        candidate = unit if not current else current + joiner + unit
        if text_width(draw, candidate, face) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = unit
    if current:
        lines.append(current)
    return lines


def fit_font(draw: ImageDraw.ImageDraw, text: str, max_width: int, start_size: int, min_size: int) -> ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        face = font(size)
        lines = wrap_text(draw, text, face, max_width)
        if lines and max(text_width(draw, line, face) for line in lines) <= max_width:
            return face
    return font(min_size)


def make_gradient(size: tuple[int, int], top: str, bottom: str) -> Image.Image:
    width, height = size
    top_rgb = hex_to_rgb(top)
    bottom_rgb = hex_to_rgb(bottom)
    image = Image.new("RGB", size, top_rgb)
    pixels = image.load()
    for y in range(height):
        t = y / max(1, height - 1)
        row = tuple(round(top_rgb[i] * (1 - t) + bottom_rgb[i] * t) for i in range(3))
        for x in range(width):
            pixels[x, y] = row
    return image


def cover_background(spec: dict[str, Any], width: int, height: int, root: Path) -> Image.Image:
    base_image = spec.get("base_image")
    if base_image:
        path = Path(base_image)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            image = Image.open(path).convert("RGB")
            image.thumbnail((width, height * 2))
            left = max(0, (image.width - width) // 2)
            top = max(0, (image.height - height) // 2)
            image = image.crop((left, top, min(left + width, image.width), min(top + height, image.height)))
            return image.resize((width, height), Image.Resampling.LANCZOS)

    palette = spec.get("palette", {})
    return make_gradient(
        (width, height),
        palette.get("background_top", "#fbfbf7"),
        palette.get("background_bottom", "#efe9dc"),
    )


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None) -> None:
    draw.rounded_rectangle(box, radius=34, fill=fill, outline=outline, width=3 if outline else 1)


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    face: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int,
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, face, max_width)
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill)
        bbox = draw.textbbox((x, y), line, font=face)
        y = bbox[3] + line_gap
    return y


def render_cover(variant: dict[str, Any], canvas: dict[str, int], root: Path) -> Image.Image:
    width = int(canvas.get("width", DEFAULT_CANVAS["width"]))
    height = int(canvas.get("height", DEFAULT_CANVAS["height"]))
    palette = variant.get("palette", {})
    image = cover_background(variant, width, height, root).convert("RGBA")
    draw = ImageDraw.Draw(image)

    margin = int(variant.get("margin", 76))
    text_color = palette.get("text", "#141414")
    accent = palette.get("accent", "#d83232")
    panel = palette.get("panel", "#fffffff0")
    muted = palette.get("muted", "#5f5f5f")
    layout = variant.get("layout", "bottom_panel")

    # Add a deterministic visual anchor when no base image exists.
    if not variant.get("base_image"):
        draw.rounded_rectangle(
            (width - 470, 170, width - 86, 750),
            radius=180,
            fill=palette.get("portrait_block", "#d9d2c5"),
        )
        draw.ellipse((width - 350, 245, width - 190, 405), fill=palette.get("portrait_face", "#f1d3ba"))
        draw.rounded_rectangle((width - 395, 425, width - 145, 740), radius=90, fill=palette.get("portrait_body", "#2c313a"))

    if layout == "top_title":
        panel_box = (margin, margin, width - margin, 520)
    elif layout == "split":
        panel_box = (margin, 120, int(width * 0.58), height - 120)
    elif layout == "center_poster":
        panel_box = (margin, int(height * 0.26), width - margin, int(height * 0.74))
    else:
        panel_box = (margin, height - 610, width - margin, height - margin)

    draw_panel(draw, panel_box, panel, palette.get("panel_outline"))

    x = panel_box[0] + 46
    y = panel_box[1] + 42
    max_width = panel_box[2] - panel_box[0] - 92

    badge = variant.get("badge")
    if badge:
        badge_font = font(34)
        badge_w = int(text_width(draw, badge, badge_font)) + 42
        draw.rounded_rectangle((x, y, x + badge_w, y + 56), radius=28, fill=accent)
        draw.text((x + 21, y + 9), badge, font=badge_font, fill=palette.get("badge_text", "#ffffff"))
        y += 82

    title = str(variant.get("title", "封面标题"))
    title_face = fit_font(draw, title, max_width, int(variant.get("title_size", 106)), 58)
    y = draw_multiline(draw, title, (x, y), title_face, text_color, max_width, 14)

    subtitle = variant.get("subtitle")
    if subtitle:
        subtitle_face = fit_font(draw, subtitle, max_width, int(variant.get("subtitle_size", 42)), 28)
        y += 20
        draw_multiline(draw, subtitle, (x, y), subtitle_face, muted, max_width, 10)

    kicker = variant.get("kicker")
    if kicker:
        small = font(30)
        draw.text((margin, height - 52), kicker, font=small, fill=muted)

    return image.convert("RGB")


def make_contact_sheet(images: list[tuple[str, Image.Image]], out_path: Path) -> None:
    thumb_w = 360
    thumb_h = 480
    label_h = 54
    columns = 3
    rows = math.ceil(len(images) / columns)
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#f4f1ea")
    draw = ImageDraw.Draw(sheet)
    label_font = font(24)

    for index, (label, image) in enumerate(images):
        x = (index % columns) * thumb_w
        y = (index // columns) * (thumb_h + label_h)
        thumb = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        sheet.paste(thumb, (x, y))
        draw.text((x + 16, y + thumb_h + 14), label[:24], font=label_font, fill="#2a2a2a")

    sheet.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render XHS cover pack PNGs from a JSON spec.")
    parser.add_argument("--spec", required=True, help="Path to cover-pack JSON spec.")
    parser.add_argument("--out", required=True, help="Output directory.")
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    root = spec_path.parent
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    canvas = spec.get("canvas", DEFAULT_CANVAS)
    variants = spec.get("variants", [])
    if not variants:
        raise SystemExit("Spec must include at least one variant.")

    rendered: list[tuple[str, Image.Image]] = []
    for index, variant in enumerate(variants, start=1):
        image = render_cover(variant, canvas, root)
        variant_id = variant.get("id", f"cover-{index:02d}")
        label = f"{variant_id} {variant.get('style', '')}".strip()
        path = out_dir / f"{variant_id}.png"
        image.save(path)
        rendered.append((label, image))

    make_contact_sheet(rendered, out_dir / "contact-sheet.png")
    print(f"Rendered {len(rendered)} covers to {out_dir}")


if __name__ == "__main__":
    main()
