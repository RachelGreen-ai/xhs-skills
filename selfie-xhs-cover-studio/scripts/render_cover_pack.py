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
TITLE_FONT_CANDIDATES = [
    os.environ.get("XHS_FONT"),
    os.environ.get("XHS_TITLE_FONT"),
    str(Path(__file__).resolve().parents[1] / "assets/fonts/ZCOOLKuaiLe-Regular.ttf"),
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
SUBTITLE_FONT_CANDIDATES = [
    os.environ.get("XHS_SUBTITLE_FONT"),
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def find_font(role: str = "title") -> str | None:
    candidates = SUBTITLE_FONT_CANDIDATES if role == "subtitle" else TITLE_FONT_CANDIDATES
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def font(size: int, role: str = "title") -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    font_path = find_font(role)
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


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    start_size: int,
    min_size: int,
    role: str = "title",
) -> ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        face = font(size, role)
        lines = wrap_text(draw, text, face, max_width)
        if lines and max(text_width(draw, line, face) for line in lines) <= max_width:
            return face
    return font(min_size, role)


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


def blend(color: str, target: str, amount: float) -> str:
    src = hex_to_rgb(color)
    dst = hex_to_rgb(target)
    mixed = tuple(round(src[i] * (1 - amount) + dst[i] * amount) for i in range(3))
    return "#%02x%02x%02x" % mixed


def cover_background(spec: dict[str, Any], width: int, height: int, root: Path) -> Image.Image:
    base_image = spec.get("base_image")
    if base_image and spec.get("background_mode", "photo") == "photo":
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
    if spec.get("background_mode") == "solid":
        return Image.new("RGB", (width, height), palette.get("background_solid", palette.get("background_top", "#fbfbf7")))

    return make_gradient(
        (width, height),
        palette.get("background_top", "#fbfbf7"),
        palette.get("background_bottom", "#efe9dc"),
    )


def draw_background_pattern(draw: ImageDraw.ImageDraw, width: int, height: int, variant: dict[str, Any]) -> None:
    palette = variant.get("palette", {})
    pattern = variant.get("pattern", "none")
    accent = palette.get("accent", "#ff4d6d")
    paper = palette.get("paper_line", blend(palette.get("background_bottom", "#f4e5d4"), "#ffffff", 0.35))

    if pattern == "grid":
        step = int(variant.get("grid_step", 54))
        for x in range(0, width, step):
            draw.line((x, 0, x, height), fill=paper, width=2)
        for y in range(0, height, step):
            draw.line((0, y, width, y), fill=paper, width=2)
    elif pattern == "dots":
        step = int(variant.get("dot_step", 82))
        for x in range(20, width, step):
            for y in range(20, height, step):
                draw.ellipse((x, y, x + 8, y + 8), fill=paper)
    elif pattern == "diagonal":
        stripe = blend(accent, "#ffffff", 0.64)
        for offset in range(-height, width, 150):
            draw.polygon(
                [(offset, height), (offset + 54, height), (offset + height + 54, 0), (offset + height, 0)],
                fill=stripe,
            )
    elif pattern == "photo-collage":
        collage_colors = palette.get("collage", ["#d7e8df", "#f1d3bb", "#c7dff0", "#e7bfd0"])
        boxes = [
            (70, 135, 520, 500),
            (540, 125, width - 70, 445),
            (80, 535, 450, 860),
            (470, 500, width - 90, 875),
            (80, 920, width - 85, 1235),
        ]
        for index, box in enumerate(boxes):
            fill = collage_colors[index % len(collage_colors)]
            draw.rounded_rectangle(box, radius=18, fill=fill, outline=palette.get("panel_outline", "#17211e"), width=6)
            x1, y1, x2, y2 = box
            for stripe_y in range(y1 + 30, y2, 58):
                draw.line((x1 + 24, stripe_y, x2 - 24, stripe_y + 26), fill=blend(fill, "#ffffff", 0.38), width=7)
            draw.rectangle((x1 + 18, y1 + 18, x2 - 18, y2 - 18), outline=blend(fill, "#000000", 0.28), width=2)


def draw_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None) -> None:
    draw.rounded_rectangle(box, radius=34, fill=fill, outline=outline, width=3 if outline else 1)


def draw_tape(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str) -> None:
    x1, y1, x2, y2 = box
    draw.polygon(
        [
            (x1 + 18, y1),
            (x2, y1 + 6),
            (x2 - 18, y2),
            (x1, y2 - 6),
        ],
        fill=fill,
    )
    for x in range(x1 + 24, x2 - 18, 34):
        draw.line((x, y1 + 8, x + 12, y2 - 8), fill=blend(fill, "#000000", 0.18), width=2)


def draw_burst(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int, fill: str) -> None:
    cx, cy = center
    points = []
    for i in range(18):
        angle = math.pi * 2 * i / 18
        r = radius if i % 2 == 0 else int(radius * 0.48)
        points.append((cx + int(math.cos(angle) * r), cy + int(math.sin(angle) * r)))
    draw.polygon(points, fill=fill)


def draw_decorations(draw: ImageDraw.ImageDraw, width: int, height: int, variant: dict[str, Any]) -> None:
    palette = variant.get("palette", {})
    accent = palette.get("accent", "#ff4d6d")
    accent2 = palette.get("accent2", "#ffe84a")
    ink = palette.get("doodle", "#ffffff")
    decorations = set(variant.get("decorations", []))

    if "burst" in decorations:
        draw_burst(draw, (118, 126), 72, accent2)
        draw_burst(draw, (width - 118, height - 168), 54, accent)
    if "rings" in decorations:
        for box in [(54, 1040, 126, 1112), (width - 160, 260, width - 90, 330), (width - 210, height - 250, width - 150, height - 190)]:
            draw.ellipse(box, outline=ink, width=8)
    if "squiggle" in decorations:
        points = [(90, 430), (150, 390), (210, 440), (270, 402), (330, 448)]
        draw.line(points, fill=accent, width=13, joint="curve")
        points2 = [(width - 310, 1000), (width - 250, 930), (width - 190, 1005), (width - 130, 940)]
        draw.line(points2, fill=accent2, width=13, joint="curve")
    if "paperclip" in decorations:
        draw.arc((78, 250, 170, 370), 100, 430, fill=ink, width=8)
        draw.arc((100, 270, 150, 342), 100, 430, fill=ink, width=6)
    if "corner-dots" in decorations:
        for i in range(6):
            draw.ellipse((width - 46, 120 + i * 40, width - 26, 140 + i * 40), fill=ink)


def draw_mock_portrait(draw: ImageDraw.ImageDraw, width: int, height: int, variant: dict[str, Any]) -> None:
    palette = variant.get("palette", {})
    pose = variant.get("portrait_pose", "right")
    scale = float(variant.get("portrait_scale", 1.0))
    outline = palette.get("portrait_outline", "#ffffff")
    block = palette.get("portrait_block", "#d9d2c5")
    face = palette.get("portrait_face", "#f1d3ba")
    hair = palette.get("portrait_hair", "#202020")
    body = palette.get("portrait_body", "#2c313a")
    shadow = palette.get("portrait_shadow", "#00000028")

    if pose == "center":
        cx = width // 2
        top = int(height * 0.28)
    elif pose == "left":
        cx = int(width * 0.34)
        top = int(height * 0.26)
    else:
        cx = int(width * 0.68)
        top = int(height * 0.23)

    head_r = int(120 * scale)
    body_w = int(360 * scale)
    body_h = int(520 * scale)
    stroke = int(34 * scale)

    draw.rounded_rectangle(
        (cx - body_w // 2 - stroke + 18, top + head_r + 90, cx + body_w // 2 + stroke + 18, top + head_r + body_h + 90),
        radius=int(140 * scale),
        fill=shadow,
    )
    draw.rounded_rectangle(
        (cx - body_w // 2 - stroke, top + head_r + 70, cx + body_w // 2 + stroke, top + head_r + body_h + 70),
        radius=int(150 * scale),
        fill=outline,
    )
    draw.ellipse((cx - head_r - stroke, top - stroke, cx + head_r + stroke, top + head_r * 2 + stroke), fill=outline)
    draw.ellipse((cx - head_r - 28, top - 22, cx + head_r + 28, top + head_r * 2 + 40), fill=hair)
    draw.ellipse((cx - head_r, top, cx + head_r, top + head_r * 2), fill=face)
    draw.rounded_rectangle(
        (cx - body_w // 2, top + head_r + 100, cx + body_w // 2, top + head_r + body_h + 70),
        radius=int(120 * scale),
        fill=body,
    )
    draw.rounded_rectangle(
        (cx - body_w // 2, top + head_r + 100, cx + body_w // 2, top + head_r + 250),
        radius=int(80 * scale),
        fill=block,
    )


def draw_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    face: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_gap: int,
    stroke_width: int = 0,
    stroke_fill: str = "#000000",
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, face, max_width)
    for line in lines:
        draw.text((x, y), line, font=face, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        bbox = draw.textbbox((x, y), line, font=face)
        y = bbox[3] + line_gap
    return y


def resolve_position(value: float | int, total: int) -> int:
    if isinstance(value, float) and 0 <= value <= 1:
        return int(value * total)
    return int(value)


def draw_rotated_text(
    image: Image.Image,
    text: str,
    center: tuple[int, int],
    face: ImageFont.ImageFont,
    fill: str,
    stroke_width: int,
    stroke_fill: str,
    angle: float = 0,
) -> None:
    padding = max(24, stroke_width * 4)
    measure = Image.new("RGBA", (10, 10), "#00000000")
    measure_draw = ImageDraw.Draw(measure)
    bbox = measure_draw.textbbox((0, 0), text, font=face, stroke_width=stroke_width)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    layer = Image.new("RGBA", (text_w + padding * 2, text_h + padding * 2), "#00000000")
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.text(
        (padding - bbox[0], padding - bbox[1]),
        text,
        font=face,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=stroke_fill,
    )
    if angle:
        layer = layer.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    x = center[0] - layer.width // 2
    y = center[1] - layer.height // 2
    image.alpha_composite(layer, (x, y))


def draw_arc_text(
    image: Image.Image,
    text: str,
    center: tuple[int, int],
    radius: int,
    start_angle: float,
    angle_step: float,
    face: ImageFont.ImageFont,
    fill: str,
    stroke_width: int,
    stroke_fill: str,
) -> None:
    for index, char in enumerate(text):
        if char.isspace():
            continue
        angle = start_angle + index * angle_step
        radians = math.radians(angle)
        x = int(center[0] + math.cos(radians) * radius)
        y = int(center[1] + math.sin(radians) * radius)
        draw_rotated_text(
            image,
            char,
            (x, y),
            face,
            fill,
            stroke_width,
            stroke_fill,
            angle + 90,
        )


def draw_contour_chunks(image: Image.Image, variant: dict[str, Any], width: int, height: int) -> bool:
    chunks = variant.get("contour_chunks", [])
    if not chunks:
        return False

    palette = variant.get("palette", {})
    fill = palette.get("text", "#fff7e5")
    stroke_fill = palette.get("title_stroke", "#173d35")
    default_size = int(variant.get("title_size", 128))
    default_stroke = int(variant.get("title_stroke_width", 8))

    for chunk in chunks:
        chunk_text = str(chunk.get("text", "")).strip()
        if not chunk_text:
            continue
        chunk_face = font(int(chunk.get("size", default_size)), chunk.get("role", "title"))
        x = resolve_position(chunk.get("x", 0.5), width)
        y = resolve_position(chunk.get("y", 0.5), height)
        draw_rotated_text(
            image,
            chunk_text,
            (x, y),
            chunk_face,
            chunk.get("fill", fill),
            int(chunk.get("stroke_width", default_stroke)),
            chunk.get("stroke_fill", stroke_fill),
            float(chunk.get("angle", 0)),
        )

    for arc in variant.get("arc_subtitles", []):
        arc_text = str(arc.get("text", "")).strip()
        if not arc_text:
            continue
        arc_face = font(int(arc.get("size", 38)), "subtitle")
        center = (
            resolve_position(arc.get("x", 0.5), width),
            resolve_position(arc.get("y", 0.5), height),
        )
        draw_arc_text(
            image,
            arc_text,
            center,
            int(arc.get("radius", 300)),
            float(arc.get("start_angle", -65)),
            float(arc.get("angle_step", 8)),
            arc_face,
            arc.get("fill", palette.get("subtitle_text", "#fffaf0")),
            int(arc.get("stroke_width", 2)),
            arc.get("stroke_fill", palette.get("subtitle_stroke", "#173d35")),
        )
    return True


def draw_visible_contour_subtitle(image: Image.Image, variant: dict[str, Any], width: int, height: int) -> None:
    subtitle = str(variant.get("subtitle", "")).strip()
    if not subtitle:
        return

    palette = variant.get("palette", {})
    face = font(int(variant.get("subtitle_size", 48)), "subtitle")
    center = variant.get("subtitle_center", [0.64, 0.58])
    draw_arc_text(
        image,
        subtitle,
        (resolve_position(center[0], width), resolve_position(center[1], height)),
        int(variant.get("subtitle_radius", 360)),
        float(variant.get("subtitle_start_angle", 18)),
        float(variant.get("subtitle_angle_step", 6.8)),
        face,
        palette.get("subtitle_text", palette.get("muted", "#fffaf0")),
        int(variant.get("subtitle_stroke_width", 2)),
        palette.get("subtitle_stroke", palette.get("title_stroke", "#173d35")),
    )


def render_cover(variant: dict[str, Any], canvas: dict[str, int], root: Path) -> Image.Image:
    width = int(canvas.get("width", DEFAULT_CANVAS["width"]))
    height = int(canvas.get("height", DEFAULT_CANVAS["height"]))
    palette = variant.get("palette", {})
    image = cover_background(variant, width, height, root).convert("RGBA")
    draw = ImageDraw.Draw(image)
    draw_background_pattern(draw, width, height, variant)

    margin = int(variant.get("margin", 76))
    text_color = palette.get("text", "#141414")
    accent = palette.get("accent", "#d83232")
    panel = palette.get("panel", "#fffffff0")
    muted = palette.get("muted", "#5f5f5f")
    layout = variant.get("layout", "bottom_panel")
    panel_style = variant.get("panel_style", "card")
    draw_decorations(draw, width, height, variant)

    # Add a deterministic visual anchor when no base image exists.
    if not variant.get("base_image"):
        draw_mock_portrait(draw, width, height, variant)

    if layout == "contour":
        draw_contour_chunks(image, variant, width, height)
        if variant.get("subtitle") and not variant.get("arc_subtitles"):
            draw_visible_contour_subtitle(image, variant, width, height)
        badge = variant.get("badge")
        if badge:
            badge_font = font(int(variant.get("badge_size", 36)), "subtitle")
            draw.text((margin, margin), badge, font=badge_font, fill=palette.get("muted", "#5f5f5f"))
        kicker = variant.get("kicker")
        if kicker:
            small = font(30, "subtitle")
            draw.text((margin, height - 52), kicker, font=small, fill=muted)
        return image.convert("RGB")

    if layout == "top_title":
        panel_box = (margin, margin, width - margin, 520)
    elif layout == "split":
        panel_box = (margin, 120, int(width * 0.58), height - 120)
    elif layout == "center_poster":
        panel_box = (margin, int(height * 0.26), width - margin, int(height * 0.74))
    else:
        panel_box = (margin, height - 610, width - margin, height - margin)

    if panel_style == "slant_banner":
        x1, y1, x2, y2 = panel_box
        draw.polygon([(x1 - 24, y1 + 26), (x2, y1 - 18), (x2 + 24, y2 - 26), (x1, y2 + 18)], fill=palette.get("panel_shadow", "#000000"))
        draw.polygon([(x1 - 34, y1), (x2, y1 - 44), (x2 + 34, y2), (x1, y2 + 44)], fill=panel)
    elif panel_style == "tape":
        draw_tape(draw, (panel_box[0], panel_box[1], panel_box[2], panel_box[1] + 96), palette.get("tape", "#ffd166"))
        draw_panel(draw, panel_box, panel, palette.get("panel_outline"))
    elif panel_style == "none":
        pass
    else:
        draw_panel(draw, panel_box, panel, palette.get("panel_outline"))

    x = panel_box[0] + 46
    y = panel_box[1] + 42
    max_width = panel_box[2] - panel_box[0] - 92

    badge = variant.get("badge")
    if badge:
        badge_font = font(34, "subtitle")
        badge_w = int(text_width(draw, badge, badge_font)) + 42
        if variant.get("badge_style") == "burst":
            draw_burst(draw, (x + badge_w // 2, y + 30), max(42, badge_w // 2), accent)
        else:
            draw.rounded_rectangle((x, y, x + badge_w, y + 56), radius=28, fill=accent)
        draw.text((x + 21, y + 9), badge, font=badge_font, fill=palette.get("badge_text", "#ffffff"))
        y += 82

    title = str(variant.get("title", "封面标题"))
    title_face = fit_font(draw, title, max_width, int(variant.get("title_size", 124)), 58)
    y = draw_multiline(
        draw,
        title,
        (x, y),
        title_face,
        text_color,
        max_width,
        int(variant.get("title_gap", 14)),
        stroke_width=int(variant.get("title_stroke_width", 0)),
        stroke_fill=palette.get("title_stroke", "#000000"),
    )

    subtitle = variant.get("subtitle")
    if subtitle:
        subtitle_face = fit_font(draw, subtitle, max_width, int(variant.get("subtitle_size", 42)), 28, "subtitle")
        y += 20
        draw_multiline(draw, subtitle, (x, y), subtitle_face, muted, max_width, 10)

    kicker = variant.get("kicker")
    if kicker:
        small = font(30, "subtitle")
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
    label_font = font(24, "subtitle")

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
