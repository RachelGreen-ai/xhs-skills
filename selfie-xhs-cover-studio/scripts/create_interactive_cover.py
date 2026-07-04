#!/usr/bin/env python3
"""Create an editable Xiaohongshu cover kit.

Input: one photo, one title, optional subtitle.
Output: standalone interactive HTML editor plus PNG layer assets.
"""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
from string import Template

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

try:
    from rembg import remove
except Exception:  # pragma: no cover - optional dependency
    remove = None


CANVAS_W = 900
CANVAS_H = 1200
SKILL_DIR = Path(__file__).resolve().parents[1]
TITLE_FONT_PATH = SKILL_DIR / "assets/fonts/ZCOOLKuaiLe-Regular.ttf"
SUBTITLE_FONT_CANDIDATES = [
    Path("/System/Library/Fonts/PingFang.ttc"),
    Path("/System/Library/Fonts/STHeiti Light.ttc"),
    Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
    Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
    Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"),
]


def load_font(path: Path | None, size: int) -> ImageFont.ImageFont:
    if path and path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def subtitle_font_path() -> Path | None:
    for path in SUBTITLE_FONT_CANDIDATES:
        if path.exists():
            return path
    return TITLE_FONT_PATH if TITLE_FONT_PATH.exists() else None


def data_uri(path: Path, mime: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def image_data_uri(image: Image.Image, mime: str = "image/png") -> str:
    import io

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def fit_crop(image: Image.Image, box: tuple[float, float, float, float], centering: tuple[float, float]) -> Image.Image:
    width, height = image.size
    x1, y1, x2, y2 = box
    cropped = image.crop((int(width * x1), int(height * y1), int(width * x2), int(height * y2)))
    return ImageOps.fit(cropped, (CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS, centering=centering)


def make_photo_background(source: Image.Image) -> Image.Image:
    background = fit_crop(source, (0, 0, 1, 0.58), (0.5, 0.28)).filter(ImageFilter.GaussianBlur(4))
    background = ImageEnhance.Color(background).enhance(0.74)
    background = ImageEnhance.Brightness(background).enhance(1.10)
    base = background.convert("RGBA")
    base = Image.alpha_composite(base, Image.new("RGBA", (CANVAS_W, CANVAS_H), (238, 241, 215, 86)))
    draw = ImageDraw.Draw(base, "RGBA")
    for y in range(0, 380):
        draw.line((0, y, CANVAS_W, y), fill=(248, 245, 205, int(150 - y * 0.30)))
    return base


def make_solid_background(color: str) -> Image.Image:
    return Image.new("RGBA", (CANVAS_W, CANVAS_H), color)


def crop_for_portrait(source: Image.Image, crop_bottom: float) -> Image.Image:
    width, height = source.size
    return source.crop((0, 0, width, int(height * crop_bottom)))


def remove_background(image: Image.Image) -> Image.Image:
    if remove is None:
        rgba = image.convert("RGBA")
        mask = Image.new("L", rgba.size, 255)
        rgba.putalpha(mask)
        return rgba
    return remove(image).convert("RGBA")


def trim_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def make_portrait_sticker(source: Image.Image, crop_bottom: float, target_height: int) -> Image.Image:
    cutout = trim_alpha(remove_background(crop_for_portrait(source, crop_bottom)))
    scale = target_height / cutout.height
    cutout = cutout.resize((int(cutout.width * scale), target_height), Image.Resampling.LANCZOS)

    alpha = cutout.getchannel("A")
    fat = alpha
    for kernel in (19, 17, 15):
        fat = fat.filter(ImageFilter.MaxFilter(kernel))

    pad = 48
    canvas = Image.new("RGBA", (cutout.width + pad * 2, cutout.height + pad * 2), (0, 0, 0, 0))
    glow = Image.new("RGBA", cutout.size, (255, 255, 255, 115))
    glow.putalpha(fat.filter(ImageFilter.GaussianBlur(7)))
    outline = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    outline.putalpha(fat)
    canvas.alpha_composite(glow, (pad, pad))
    canvas.alpha_composite(outline, (pad, pad))
    canvas.alpha_composite(cutout, (pad, pad))
    return canvas


def draw_text(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], face: ImageFont.ImageFont, fill: str) -> None:
    draw.text(xy, text, font=face, fill=fill, stroke_width=12, stroke_fill="#ffffff")
    draw.text(xy, text, font=face, fill=fill, stroke_width=7, stroke_fill="#173d35")


def draw_subtitle_lockup(image: Image.Image, text: str, x: int, y: int, curve: int, size: int) -> None:
    if not text:
        return
    face = load_font(subtitle_font_path(), size)
    probe = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    widths: list[int] = []
    for char in text:
        bbox = probe.textbbox((0, 0), char, font=face, stroke_width=3)
        widths.append(bbox[2] - bbox[0])
    spacing = 7
    total = sum(widths) + spacing * max(0, len(widths) - 1)
    cursor = x - total / 2
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    for index, char in enumerate(text):
        width = widths[index]
        cx = cursor + width / 2
        t = (cx - x) / max(1, total / 2)
        cy = y + curve * (t * t) - curve * 0.25
        angle = t * 7
        bbox = probe.textbbox((0, 0), char, font=face, stroke_width=3)
        glyph = Image.new("RGBA", (bbox[2] - bbox[0] + 40, bbox[3] - bbox[1] + 40), (0, 0, 0, 0))
        glyph_draw = ImageDraw.Draw(glyph)
        glyph_draw.text(
            (glyph.width / 2, glyph.height / 2),
            char,
            font=face,
            fill="#fbff9a",
            stroke_width=3,
            stroke_fill="#173d35",
            anchor="mm",
        )
        rotated = glyph.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        layer.alpha_composite(rotated, (int(cx - rotated.width / 2), int(cy - rotated.height / 2)))
        cursor += width + spacing
    image.alpha_composite(layer)


def draw_preview(background: Image.Image, sticker: Image.Image, config: dict[str, object]) -> Image.Image:
    image = background.copy().convert("RGBA")
    draw = ImageDraw.Draw(image, "RGBA")
    draw.arc((770, 118, 818, 166), 20, 338, fill="#fff8d5", width=5)
    draw.arc((781, 129, 807, 155), 20, 338, fill="#fff8d5", width=3)
    draw.line((682, 840, 704, 818, 728, 840, 754, 810), fill="#fff176", width=8, joint="curve")
    scale = float(config["portraitScale"])
    portrait = sticker.resize((int(sticker.width * scale), int(sticker.height * scale)), Image.Resampling.LANCZOS)
    image.alpha_composite(portrait, (int(config["portraitX"]), int(config["portraitY"])))
    title_face = load_font(TITLE_FONT_PATH, int(config["titleSize"]))
    draw_text(draw, str(config["title"]), (int(config["titleX"]), int(config["titleY"])), title_face, "#fff8a8")
    draw_subtitle_lockup(
        image,
        str(config["subtitle"]),
        int(config["subtitleX"]),
        int(config["subtitleY"]),
        int(config["subtitleCurve"]),
        int(config["subtitleSize"]),
    )
    return image


EDITOR_TEMPLATE = Template(
    r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>XHS Cover Fine-Tune Editor</title>
  <style>
    @font-face {
      font-family: "ZCOOLKuaiLeLocal";
      src: url("$font_data") format("truetype");
      font-weight: 400;
    }
    :root {
      --bg: #f5f3eb;
      --panel: #ffffff;
      --ink: #1e3029;
      --muted: #63756d;
      --line: #dfe5db;
      --accent: #2f6f55;
      --accent-soft: #dce8cf;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
    }
    .app {
      display: grid;
      grid-template-columns: minmax(420px, 1fr) 340px;
      gap: 24px;
      min-height: 100vh;
      padding: 24px;
    }
    .stage {
      display: grid;
      place-items: center;
      min-width: 0;
    }
    .canvas-wrap {
      position: relative;
      width: min(68vh, 100%);
      max-width: 560px;
      aspect-ratio: 3 / 4;
      box-shadow: 0 24px 70px rgba(22, 38, 30, .18);
      background: #e5eadb;
    }
    canvas {
      display: block;
      width: 100%;
      height: 100%;
      cursor: grab;
      touch-action: none;
    }
    canvas:active { cursor: grabbing; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      align-self: start;
      box-shadow: 0 18px 50px rgba(31, 48, 41, .08);
    }
    h1 {
      margin: 0 0 6px;
      font-size: 20px;
      letter-spacing: 0;
      line-height: 1.2;
    }
    .hint {
      margin: 0 0 18px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .group {
      padding: 14px 0;
      border-top: 1px solid var(--line);
    }
    .group:first-of-type { border-top: 0; padding-top: 0; }
    label {
      display: grid;
      gap: 7px;
      margin: 10px 0;
      font-size: 12px;
      font-weight: 650;
      color: var(--ink);
    }
    input, select, button {
      width: 100%;
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 7px;
      padding: 8px 10px;
      font: inherit;
      color: var(--ink);
      background: #fff;
    }
    input[type="range"] { padding: 0; accent-color: var(--accent); }
    input[type="color"] { padding: 4px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .seg {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 6px;
    }
    .seg button {
      background: #f6f8f3;
      font-size: 12px;
      cursor: pointer;
    }
    .seg button.active {
      background: var(--accent-soft);
      border-color: var(--accent);
      color: #143b2c;
    }
    .primary {
      margin-top: 12px;
      background: var(--ink);
      color: #fff;
      border-color: var(--ink);
      cursor: pointer;
      font-weight: 750;
    }
    .small {
      color: var(--muted);
      font-size: 12px;
      line-height: 1.45;
    }
    @media (max-width: 900px) {
      .app { grid-template-columns: 1fr; padding: 14px; }
      .panel { order: -1; }
      .canvas-wrap { width: min(92vw, 540px); }
    }
  </style>
</head>
<body>
  <main class="app">
    <section class="stage">
      <div class="canvas-wrap">
        <canvas id="cover" width="900" height="1200" aria-label="Editable Xiaohongshu cover"></canvas>
      </div>
    </section>
    <aside class="panel">
      <h1>Cover Fine-Tune</h1>
      <p class="hint">Drag the title, subtitle, or portrait. Adjust size and subtitle curve, then export a ready-to-post PNG.</p>

      <div class="group">
        <div class="seg" id="targetButtons">
          <button data-target="title" class="active">Title</button>
          <button data-target="subtitle">Subtitle</button>
          <button data-target="portrait">Portrait</button>
        </div>
        <label>Main title
          <input id="titleText" value="$title_value" />
        </label>
        <label>Subtitle
          <input id="subtitleText" value="$subtitle_value" />
        </label>
      </div>

      <div class="group">
        <div class="row">
          <label>Title size
            <input id="titleSize" type="range" min="110" max="210" value="$title_size" />
          </label>
          <label>Subtitle size
            <input id="subtitleSize" type="range" min="24" max="74" value="$subtitle_size" />
          </label>
        </div>
        <label>Subtitle curve
          <input id="subtitleCurve" type="range" min="-32" max="42" value="$subtitle_curve" />
        </label>
      </div>

      <div class="group">
        <div class="row">
          <label>Portrait scale
            <input id="portraitScale" type="range" min="0.74" max="1.18" value="$portrait_scale" step="0.01" />
          </label>
          <label>Solid color
            <input id="solidColor" type="color" value="$solid_color" />
          </label>
        </div>
        <label>Background
          <select id="backgroundMode">
            <option value="solid">Solid color</option>
            <option value="photo">Photo background</option>
          </select>
        </label>
      </div>

      <button class="primary" id="exportBtn">Export PNG</button>
      <p class="small">Tip: click an element, then use arrow keys for 1px nudges. Hold Shift for 10px.</p>
    </aside>
  </main>

  <script>
    const assets = {
      photoBg: "$photo_bg_data",
      solidBg: "$solid_bg_data",
      portrait: "$portrait_data"
    };
    const state = $state_json;
    const canvas = document.getElementById("cover");
    const ctx = canvas.getContext("2d");
    const imageCache = {};
    let selected = "title";
    let drag = null;
    let lastBounds = {};

    function loadImage(src) {
      if (imageCache[src]) return imageCache[src];
      const img = new Image();
      img.src = src;
      imageCache[src] = img;
      return img;
    }

    const photoBg = loadImage(assets.photoBg);
    const solidBg = loadImage(assets.solidBg);
    const portrait = loadImage(assets.portrait);

    function drawStrokeText(text, x, y, size) {
      ctx.font = size + 'px ZCOOLKuaiLeLocal, "PingFang SC", sans-serif';
      ctx.textBaseline = "top";
      ctx.lineJoin = "round";
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 12;
      ctx.strokeText(text, x, y);
      ctx.strokeStyle = "#173d35";
      ctx.lineWidth = 7;
      ctx.strokeText(text, x, y);
      ctx.fillStyle = "#fff8a8";
      ctx.fillText(text, x, y);
      const metrics = ctx.measureText(text);
      lastBounds.title = { x, y, w: metrics.width, h: size * 1.05 };
    }

    function drawSubtitle(text, x, y, size, curve) {
      ctx.font = size + 'px "PingFang SC", "Hiragino Sans GB", sans-serif';
      ctx.textBaseline = "middle";
      const chars = Array.from(text);
      const spacing = 7;
      const widths = chars.map(ch => ctx.measureText(ch).width);
      const total = widths.reduce((a, b) => a + b, 0) + spacing * Math.max(0, chars.length - 1);
      let cursor = x - total / 2;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      chars.forEach((ch, i) => {
        const w = widths[i];
        const cx = cursor + w / 2;
        const t = (cx - x) / Math.max(1, total / 2);
        const cy = y + curve * (t * t) - curve * 0.25;
        const angle = t * 7 * Math.PI / 180;
        ctx.save();
        ctx.translate(cx, cy);
        ctx.rotate(angle);
        ctx.lineJoin = "round";
        ctx.strokeStyle = "#173d35";
        ctx.lineWidth = 3;
        ctx.strokeText(ch, -w / 2, 0);
        ctx.fillStyle = "#fbff9a";
        ctx.fillText(ch, -w / 2, 0);
        ctx.restore();
        minX = Math.min(minX, cx - w / 2 - 12);
        maxX = Math.max(maxX, cx + w / 2 + 12);
        minY = Math.min(minY, cy - size / 2 - 18);
        maxY = Math.max(maxY, cy + size / 2 + Math.abs(curve) + 18);
        cursor += w + spacing;
      });
      lastBounds.subtitle = { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    }

    function drawDecor() {
      ctx.strokeStyle = "#fff8d5";
      ctx.lineWidth = 5;
      ctx.beginPath();
      ctx.arc(794, 142, 24, 0.15 * Math.PI, 1.88 * Math.PI);
      ctx.stroke();
      ctx.strokeStyle = "#fff176";
      ctx.lineWidth = 8;
      ctx.beginPath();
      ctx.moveTo(682, 840);
      ctx.lineTo(704, 818);
      ctx.lineTo(728, 840);
      ctx.lineTo(754, 810);
      ctx.stroke();
    }

    function render() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (state.backgroundMode === "photo") {
        ctx.drawImage(photoBg, 0, 0, 900, 1200);
      } else {
        ctx.fillStyle = state.solidColor;
        ctx.fillRect(0, 0, 900, 1200);
      }
      drawDecor();
      const pw = portrait.naturalWidth * state.portraitScale;
      const ph = portrait.naturalHeight * state.portraitScale;
      ctx.drawImage(portrait, state.portraitX, state.portraitY, pw, ph);
      lastBounds.portrait = { x: state.portraitX, y: state.portraitY, w: pw, h: ph };
      drawStrokeText(state.title, state.titleX, state.titleY, state.titleSize);
      if (state.subtitle) {
        drawSubtitle(state.subtitle, state.subtitleX, state.subtitleY, state.subtitleSize, state.subtitleCurve);
      }
      drawSelection();
      syncControls();
    }

    function drawSelection() {
      const b = lastBounds[selected];
      if (!b) return;
      ctx.save();
      ctx.strokeStyle = "rgba(20, 59, 44, .55)";
      ctx.setLineDash([10, 8]);
      ctx.lineWidth = 2;
      ctx.strokeRect(b.x - 10, b.y - 10, b.w + 20, b.h + 20);
      ctx.restore();
    }

    function hitTest(x, y) {
      for (const name of ["subtitle", "title", "portrait"]) {
        const b = lastBounds[name];
        if (b && x >= b.x - 14 && x <= b.x + b.w + 14 && y >= b.y - 14 && y <= b.y + b.h + 14) return name;
      }
      return selected;
    }

    function canvasPoint(event) {
      const rect = canvas.getBoundingClientRect();
      return {
        x: (event.clientX - rect.left) * canvas.width / rect.width,
        y: (event.clientY - rect.top) * canvas.height / rect.height
      };
    }

    canvas.addEventListener("pointerdown", event => {
      const p = canvasPoint(event);
      selected = hitTest(p.x, p.y);
      setActiveButton();
      drag = { x: p.x, y: p.y, selected };
      canvas.setPointerCapture(event.pointerId);
      render();
    });
    canvas.addEventListener("pointermove", event => {
      if (!drag) return;
      const p = canvasPoint(event);
      const dx = p.x - drag.x;
      const dy = p.y - drag.y;
      moveSelected(dx, dy);
      drag.x = p.x;
      drag.y = p.y;
      render();
    });
    canvas.addEventListener("pointerup", () => { drag = null; });

    function moveSelected(dx, dy) {
      if (selected === "title") {
        state.titleX += dx;
        state.titleY += dy;
      } else if (selected === "subtitle") {
        state.subtitleX += dx;
        state.subtitleY += dy;
      } else {
        state.portraitX += dx;
        state.portraitY += dy;
      }
    }

    function setActiveButton() {
      document.querySelectorAll("#targetButtons button").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.target === selected);
      });
    }

    function syncControls() {
      document.getElementById("titleText").value = state.title;
      document.getElementById("subtitleText").value = state.subtitle;
      document.getElementById("titleSize").value = state.titleSize;
      document.getElementById("subtitleSize").value = state.subtitleSize;
      document.getElementById("subtitleCurve").value = state.subtitleCurve;
      document.getElementById("portraitScale").value = state.portraitScale;
      document.getElementById("solidColor").value = state.solidColor;
      document.getElementById("backgroundMode").value = state.backgroundMode;
    }

    document.querySelectorAll("#targetButtons button").forEach(btn => {
      btn.addEventListener("click", () => {
        selected = btn.dataset.target;
        setActiveButton();
        render();
      });
    });
    for (const id of ["titleText", "subtitleText"]) {
      document.getElementById(id).addEventListener("input", event => {
        state[id === "titleText" ? "title" : "subtitle"] = event.target.value;
        render();
      });
    }
    for (const id of ["titleSize", "subtitleSize", "subtitleCurve", "portraitScale"]) {
      document.getElementById(id).addEventListener("input", event => {
        state[id] = Number(event.target.value);
        render();
      });
    }
    document.getElementById("solidColor").addEventListener("input", event => {
      state.solidColor = event.target.value;
      state.backgroundMode = "solid";
      render();
    });
    document.getElementById("backgroundMode").addEventListener("change", event => {
      state.backgroundMode = event.target.value;
      render();
    });
    document.getElementById("exportBtn").addEventListener("click", () => {
      const previous = selected;
      selected = "";
      render();
      const link = document.createElement("a");
      link.download = "xhs-cover.png";
      link.href = canvas.toDataURL("image/png");
      link.click();
      selected = previous;
      render();
    });
    window.addEventListener("keydown", event => {
      if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const amount = event.shiftKey ? 10 : 1;
      const dx = event.key === "ArrowLeft" ? -amount : event.key === "ArrowRight" ? amount : 0;
      const dy = event.key === "ArrowUp" ? -amount : event.key === "ArrowDown" ? amount : 0;
      moveSelected(dx, dy);
      render();
    });
    Promise.all([photoBg.decode(), solidBg.decode(), portrait.decode()]).then(render);
  </script>
</body>
</html>
"""
)


def write_editor(
    out_dir: Path,
    title: str,
    subtitle: str,
    solid_color: str,
    photo_bg: Image.Image,
    solid_bg: Image.Image,
    sticker: Image.Image,
    config: dict[str, object],
) -> None:
    font_data = data_uri(TITLE_FONT_PATH, "font/ttf") if TITLE_FONT_PATH.exists() else ""
    html = EDITOR_TEMPLATE.substitute(
        font_data=font_data,
        photo_bg_data=image_data_uri(photo_bg),
        solid_bg_data=image_data_uri(solid_bg),
        portrait_data=image_data_uri(sticker),
        state_json=json.dumps(config, ensure_ascii=False),
        title_value=title.replace('"', "&quot;"),
        subtitle_value=subtitle.replace('"', "&quot;"),
        title_size=config["titleSize"],
        subtitle_size=config["subtitleSize"],
        subtitle_curve=config["subtitleCurve"],
        portrait_scale=config["portraitScale"],
        solid_color=solid_color,
    )
    (out_dir / "interactive-editor.html").write_text(html, encoding="utf-8")


def build_cover(args: argparse.Namespace) -> None:
    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    source = Image.open(args.image).convert("RGB")
    photo_bg = make_photo_background(source)
    solid_bg = make_solid_background(args.solid_color)
    sticker = make_portrait_sticker(source, args.crop_bottom, args.portrait_height)

    config: dict[str, object] = {
        "title": args.title,
        "subtitle": args.subtitle or "",
        "titleX": 70,
        "titleY": 34,
        "titleSize": args.title_size,
        "subtitleX": 450,
        "subtitleY": 238,
        "subtitleSize": args.subtitle_size,
        "subtitleCurve": args.subtitle_curve,
        "portraitX": int((CANVAS_W - sticker.width * args.portrait_scale) / 2 - 10),
        "portraitY": args.portrait_y,
        "portraitScale": args.portrait_scale,
        "backgroundMode": args.background_mode,
        "solidColor": args.solid_color,
    }

    photo_bg.save(out_dir / "background-photo.png")
    solid_bg.save(out_dir / "background-solid.png")
    sticker.save(out_dir / "portrait-sticker.png")
    (out_dir / "cover-config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    preview_bg = solid_bg if args.background_mode == "solid" else photo_bg
    preview = draw_preview(preview_bg, sticker, config)
    preview.convert("RGB").save(out_dir / "preview.png", quality=96)
    write_editor(out_dir, args.title, args.subtitle or "", args.solid_color, photo_bg, solid_bg, sticker, config)
    print(f"Wrote interactive cover kit to {out_dir}")
    print(f"Open {out_dir / 'interactive-editor.html'}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create an editable XHS cover HTML kit.")
    parser.add_argument("--image", required=True, help="Input selfie/photo path.")
    parser.add_argument("--title", required=True, help="Main cover title.")
    parser.add_argument("--subtitle", default="", help="Optional subtitle.")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--background-mode", choices=["solid", "photo"], default="solid")
    parser.add_argument("--solid-color", default="#dce8cf")
    parser.add_argument("--crop-bottom", type=float, default=0.555, help="Bottom crop ratio for foreground portrait.")
    parser.add_argument("--portrait-height", type=int, default=900)
    parser.add_argument("--portrait-y", type=int, default=332)
    parser.add_argument("--portrait-scale", type=float, default=1.0)
    parser.add_argument("--title-size", type=int, default=168)
    parser.add_argument("--subtitle-size", type=int, default=44)
    parser.add_argument("--subtitle-curve", type=int, default=12)
    return parser.parse_args()


def main() -> None:
    build_cover(parse_args())


if __name__ == "__main__":
    main()
