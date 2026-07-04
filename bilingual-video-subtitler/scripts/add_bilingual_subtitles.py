#!/usr/bin/env python3
"""Create bilingual Chinese-English subtitles for a video with local Whisper."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


DEFAULT_MODEL_DIR = Path.home() / ".cache" / "whisper"
DEFAULT_INITIAL_PROMPT = (
    "这是一段面向小红书或 YouTube 的中文口播内容。请准确保留中文专有名词、AI、PhD、offer、"
    "resume、interview 等中英混合表达，并使用自然的标点。"
)


@dataclass
class Segment:
    start: float
    end: float
    cn: str
    en: str


STYLE_PRESETS = {
    "tech": {
        "font": "PingFang SC",
        "cn_size_xhs": 74,
        "en_size_xhs": 42,
        "cn_size_youtube": 58,
        "en_size_youtube": 34,
        "cn_color": "&H00FFFFFF",
        "en_color": "&H00E9F6FF",
        "outline": "&H00201610",
        "shadow": "&H80000000",
        "outline_width": 4,
        "shadow_depth": 1,
        "bold": 1,
    },
    "playful": {
        "font": "PingFang SC",
        "cn_size_xhs": 82,
        "en_size_xhs": 43,
        "cn_size_youtube": 62,
        "en_size_youtube": 35,
        "cn_color": "&H009EF7FF",
        "en_color": "&H00FFFFFF",
        "outline": "&H003A2631",
        "shadow": "&H80491C8F",
        "outline_width": 5,
        "shadow_depth": 2,
        "bold": 1,
    },
}


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    print("+ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_text(text: str) -> str:
    return " ".join((text or "").replace("\n", " ").split()).strip()


def srt_time(seconds: float) -> str:
    milliseconds = int(round(max(seconds, 0) * 1000))
    hours, rem = divmod(milliseconds, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, ms = divmod(rem, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def ass_time(seconds: float) -> str:
    centiseconds = int(round(max(seconds, 0) * 100))
    hours, rem = divmod(centiseconds, 360_000)
    minutes, rem = divmod(rem, 6_000)
    secs, cs = divmod(rem, 100)
    return f"{hours:d}:{minutes:02}:{secs:02}.{cs:02}"


def ass_escape(text: str) -> str:
    return normalize_text(text).replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}")


def ffmpeg_filter_path(path: Path) -> str:
    escaped = str(path.resolve())
    for old, new in [
        ("\\", r"\\"),
        (":", r"\:"),
        ("'", r"\'"),
        (",", r"\,"),
        ("[", r"\["),
        ("]", r"\]"),
    ]:
        escaped = escaped.replace(old, new)
    return escaped


def video_resolution(video: Path) -> tuple[int, int] | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        str(video),
    ]
    try:
        out = subprocess.check_output(cmd, text=True).strip()
        width, height = out.split("x", 1)
        return int(width), int(height)
    except Exception:
        return None


def video_fps(video: Path) -> str:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return "25"
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=r_frame_rate",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video),
    ]
    try:
        value = subprocess.check_output(cmd, text=True).strip()
        return value if value and value != "0/0" else "25"
    except Exception:
        return "25"


def has_audio(video: Path) -> bool:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return True
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=index",
        "-of",
        "csv=p=0",
        str(video),
    ]
    try:
        return bool(subprocess.check_output(cmd, text=True).strip())
    except Exception:
        return False


def target_resolution(video: Path, orientation: str) -> tuple[int, int]:
    if orientation == "xhs":
        return (1080, 1920)
    if orientation == "youtube":
        return (1920, 1080)
    return video_resolution(video) or (1080, 1920)


def ffmpeg_has_filter(name: str) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    try:
        out = subprocess.check_output([ffmpeg, "-hide_banner", "-filters"], text=True)
    except Exception:
        return False
    return any(line.split()[1:2] == [name] for line in out.splitlines() if line.strip())


def font_file(font_name: str) -> str | None:
    fc_match = shutil.which("fc-match")
    if not fc_match:
        return None
    try:
        out = subprocess.check_output([fc_match, "-f", "%{file}\n", font_name], text=True).strip()
        return out or None
    except Exception:
        return None


def whisper_output_path(video: Path, output_dir: Path) -> Path:
    return output_dir / f"{video.stem}.json"


def run_whisper(
    *,
    video: Path,
    output_dir: Path,
    task: str,
    model: str,
    model_dir: Path,
    language: str,
    whisper_bin: str,
    device: str,
    initial_prompt: str,
    threads: int | None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        whisper_bin,
        str(video),
        "--model",
        model,
        "--model_dir",
        str(model_dir.expanduser()),
        "--language",
        language,
        "--task",
        task,
        "--output_format",
        "json",
        "--output_dir",
        str(output_dir),
        "--fp16",
        "False",
        "--verbose",
        "False",
        "--condition_on_previous_text",
        "False",
    ]
    if device:
        cmd.extend(["--device", device])
    if initial_prompt:
        cmd.extend(["--initial_prompt", initial_prompt])
    if threads:
        cmd.extend(["--threads", str(threads)])
    run(cmd)
    result = whisper_output_path(video, output_dir)
    if not result.exists():
        candidates = sorted(output_dir.glob("*.json"))
        if candidates:
            return candidates[-1]
        raise FileNotFoundError(f"Whisper did not produce JSON in {output_dir}")
    return result


def closest_segment(time_mid: float, segments: list[dict]) -> dict | None:
    if not segments:
        return None
    return min(
        segments,
        key=lambda item: abs(((float(item.get("start", 0)) + float(item.get("end", 0))) / 2) - time_mid),
    )


def merge_segments(cn_payload: dict, en_payload: dict) -> list[Segment]:
    cn_segments = cn_payload.get("segments") or []
    en_segments = en_payload.get("segments") or []
    merged: list[Segment] = []

    for idx, cn_item in enumerate(cn_segments):
        start = float(cn_item.get("start", 0))
        end = float(cn_item.get("end", start + 1.8))
        if idx < len(en_segments):
            en_item = en_segments[idx]
        else:
            en_item = closest_segment((start + end) / 2, en_segments) or {}

        cn_text = normalize_text(cn_item.get("text", ""))
        en_text = normalize_text(en_item.get("text", ""))
        if not cn_text and not en_text:
            continue
        merged.append(Segment(start=start, end=max(end, start + 0.45), cn=cn_text, en=en_text))

    if not merged and normalize_text(cn_payload.get("text", "")):
        merged.append(
            Segment(
                start=0,
                end=10,
                cn=normalize_text(cn_payload.get("text", "")),
                en=normalize_text(en_payload.get("text", "")),
            )
        )
    return merged


def write_srt(path: Path, segments: list[Segment], mode: str) -> None:
    blocks: list[str] = []
    for idx, segment in enumerate(segments, 1):
        if mode == "cn":
            text = segment.cn
        elif mode == "en":
            text = segment.en
        else:
            text = "\n".join(line for line in [segment.cn, segment.en] if line)
        blocks.append(
            f"{idx}\n{srt_time(segment.start)} --> {srt_time(segment.end)}\n{text}".rstrip()
        )
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def ass_style_line(
    name: str,
    *,
    font: str,
    size: int,
    primary: str,
    outline: str,
    shadow: str,
    bold: int,
    margin_v: int,
    outline_width: int,
    shadow_depth: int,
) -> str:
    return (
        f"Style: {name},{font},{size},{primary},&H00FFFFFF,{outline},{shadow},"
        f"{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow_depth},2,80,80,{margin_v},1"
    )


def write_ass(path: Path, segments: list[Segment], *, style: str, orientation: str, video: Path) -> None:
    preset = STYLE_PRESETS[style]
    width, height = target_resolution(video, orientation)
    if height >= width:
        cn_size = preset["cn_size_xhs"]
        en_size = preset["en_size_xhs"]
        cn_margin = 214
        en_margin = 142
    else:
        cn_size = preset["cn_size_youtube"]
        en_size = preset["en_size_youtube"]
        cn_margin = 128
        en_margin = 78

    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "ScaledBorderAndShadow: yes",
        f"PlayResX: {width}",
        f"PlayResY: {height}",
        "WrapStyle: 2",
        "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,"
        "Alignment,MarginL,MarginR,MarginV,Encoding",
        ass_style_line(
            "CN",
            font=preset["font"],
            size=cn_size,
            primary=preset["cn_color"],
            outline=preset["outline"],
            shadow=preset["shadow"],
            bold=preset["bold"],
            margin_v=cn_margin,
            outline_width=preset["outline_width"],
            shadow_depth=preset["shadow_depth"],
        ),
        ass_style_line(
            "EN",
            font=preset["font"],
            size=en_size,
            primary=preset["en_color"],
            outline=preset["outline"],
            shadow=preset["shadow"],
            bold=0,
            margin_v=en_margin,
            outline_width=max(2, preset["outline_width"] - 1),
            shadow_depth=preset["shadow_depth"],
        ),
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    events: list[str] = []
    for segment in segments:
        start = ass_time(segment.start)
        end = ass_time(segment.end)
        if segment.cn:
            events.append(f"Dialogue: 0,{start},{end},CN,,0,0,0,,{ass_escape(segment.cn)}")
        if segment.en:
            events.append(f"Dialogue: 1,{start},{end},EN,,0,0,0,,{ass_escape(segment.en)}")

    path.write_text("\n".join(header + events) + "\n", encoding="utf-8")


def text_width(draw, text: str, font) -> int:
    left, _top, right, _bottom = draw.textbbox((0, 0), text, font=font)
    return right - left


def wrap_for_width(draw, text: str, font, max_width: int) -> list[str]:
    text = normalize_text(text)
    if not text:
        return []
    if text_width(draw, text, font) <= max_width:
        return [text]

    tokens: list[str] = []
    latin_buffer = ""
    for char in text:
        if char.isascii() and (char.isalnum() or char in "'-.+/&"):
            latin_buffer += char
            continue
        if latin_buffer:
            tokens.append(latin_buffer)
            latin_buffer = ""
        tokens.append(char)
    if latin_buffer:
        tokens.append(latin_buffer)

    lines: list[str] = []
    current = ""
    for token in tokens:
        candidate = current + token
        if current and text_width(draw, candidate, font) > max_width:
            lines.append(current.rstrip())
            current = token.lstrip()
        else:
            current = candidate
    if current.strip():
        lines.append(current.strip())
    return lines


def active_segment(segments: list[Segment], timestamp: float) -> Segment | None:
    for segment in segments:
        if segment.start <= timestamp <= segment.end:
            return segment
    return None


def draw_centered_lines(
    draw,
    lines: list[str],
    *,
    y: int,
    font,
    fill: str,
    stroke_fill: str,
    stroke_width: int,
    canvas_width: int,
    line_gap: int,
) -> int:
    for line in lines:
        left, top, right, bottom = draw.textbbox((0, 0), line, font=font, stroke_width=stroke_width)
        x = (canvas_width - (right - left)) // 2
        draw.text((x, y), line, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        y += bottom - top + line_gap
    return y


def burn_subtitles_with_pillow(
    video: Path,
    output_path: Path,
    segments: list[Segment],
    *,
    style: str,
    orientation: str,
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to render video frames.")

    preset = STYLE_PRESETS[style]
    fps_string = video_fps(video)
    fps_float = float(Fraction(fps_string))
    frame_size = video_resolution(video) or target_resolution(video, orientation)
    width, height = frame_size
    scale = height / 1920 if height >= width else width / 1920

    font_path = font_file(preset["font"]) or font_file("PingFang SC") or font_file("Arial Unicode MS")
    if not font_path:
        raise RuntimeError("Could not find a CJK-capable font for Pillow subtitle rendering.")

    cn_size = int((preset["cn_size_xhs"] if height >= width else preset["cn_size_youtube"]) * scale)
    en_size = int((preset["en_size_xhs"] if height >= width else preset["en_size_youtube"]) * scale)
    cn_font = ImageFont.truetype(font_path, cn_size)
    en_font = ImageFont.truetype(font_path, en_size)

    if style == "playful":
        cn_fill = "#fff79e"
        en_fill = "#ffffff"
        stroke_fill = "#31263a"
    else:
        cn_fill = "#ffffff"
        en_fill = "#fff6e9"
        stroke_fill = "#101620"

    stroke_width = max(3, int(preset["outline_width"] * scale))
    max_width = int(width * 0.86)
    bottom_margin = int((118 if height >= width else 58) * scale)
    line_gap = int(10 * scale)
    block_gap = int(8 * scale)

    with tempfile.TemporaryDirectory(prefix="bilingual-subtitle-frames-") as tmp:
        tmp_dir = Path(tmp)
        frame_pattern = tmp_dir / "frame_%06d.png"
        rendered_pattern = tmp_dir / "rendered_%06d.png"
        run([ffmpeg, "-y", "-i", str(video), "-fps_mode", "passthrough", str(frame_pattern)])

        frames = sorted(tmp_dir.glob("frame_*.png"))
        for idx, frame_path in enumerate(frames, 1):
            timestamp = (idx - 1) / fps_float
            segment = active_segment(segments, timestamp)
            if segment:
                with Image.open(frame_path).convert("RGB") as image:
                    draw = ImageDraw.Draw(image)
                    cn_lines = wrap_for_width(draw, segment.cn, cn_font, max_width)
                    en_lines = wrap_for_width(draw, segment.en, en_font, max_width)

                    cn_heights = [
                        draw.textbbox((0, 0), line, font=cn_font, stroke_width=stroke_width)[3]
                        - draw.textbbox((0, 0), line, font=cn_font, stroke_width=stroke_width)[1]
                        for line in cn_lines
                    ]
                    en_heights = [
                        draw.textbbox((0, 0), line, font=en_font, stroke_width=max(2, stroke_width - 1))[3]
                        - draw.textbbox((0, 0), line, font=en_font, stroke_width=max(2, stroke_width - 1))[1]
                        for line in en_lines
                    ]
                    total_height = (
                        sum(cn_heights)
                        + max(0, len(cn_lines) - 1) * line_gap
                        + (block_gap if cn_lines and en_lines else 0)
                        + sum(en_heights)
                        + max(0, len(en_lines) - 1) * line_gap
                    )
                    y = height - bottom_margin - total_height
                    y = max(int(height * 0.58), y)
                    y = draw_centered_lines(
                        draw,
                        cn_lines,
                        y=y,
                        font=cn_font,
                        fill=cn_fill,
                        stroke_fill=stroke_fill,
                        stroke_width=stroke_width,
                        canvas_width=width,
                        line_gap=line_gap,
                    )
                    y += block_gap
                    draw_centered_lines(
                        draw,
                        en_lines,
                        y=y,
                        font=en_font,
                        fill=en_fill,
                        stroke_fill=stroke_fill,
                        stroke_width=max(2, stroke_width - 1),
                        canvas_width=width,
                        line_gap=line_gap,
                    )
                    image.save(tmp_dir / f"rendered_{idx:06d}.png")
            else:
                shutil.copy(frame_path, tmp_dir / f"rendered_{idx:06d}.png")

        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            fps_string,
            "-i",
            str(rendered_pattern),
        ]
        if has_audio(video):
            cmd.extend(["-i", str(video), "-map", "0:v:0", "-map", "1:a:0"])
        cmd.extend(
            [
                "-c:v",
                "libx264",
                "-crf",
                "18",
                "-preset",
                "medium",
                "-pix_fmt",
                "yuv420p",
            ]
        )
        if has_audio(video):
            cmd.extend(["-c:a", "aac", "-b:a", "192k", "-shortest"])
        cmd.append(str(output_path))
        run(cmd)


def burn_subtitles(video: Path, ass_path: Path, output_path: Path, segments: list[Segment], *, style: str, orientation: str) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required to burn subtitles into video.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not ffmpeg_has_filter("ass") and not ffmpeg_has_filter("subtitles"):
        print("ffmpeg has no ass/subtitles filter; falling back to Pillow frame rendering.")
        burn_subtitles_with_pillow(video, output_path, segments, style=style, orientation=orientation)
        return

    filter_name = "ass" if ffmpeg_has_filter("ass") else "subtitles"
    filter_arg = f"{filter_name}=filename={ffmpeg_filter_path(ass_path)}"
    cmd = [
        ffmpeg,
        "-y",
        "-i",
        str(video),
        "-vf",
        filter_arg,
        "-c:v",
        "libx264",
        "-crf",
        "18",
        "-preset",
        "medium",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        str(output_path),
    ]
    run(cmd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Chinese-English bilingual subtitles with local Whisper and optional burn-in."
    )
    parser.add_argument("--video", required=True, type=Path, help="Input video file.")
    parser.add_argument("--out-dir", type=Path, default=Path("out/bilingual-video-subtitler"))
    parser.add_argument("--style", choices=sorted(STYLE_PRESETS), default="tech")
    parser.add_argument("--orientation", choices=["xhs", "youtube", "auto"], default="xhs")
    parser.add_argument("--model", default="large-v3-turbo")
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--language", default="zh")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=None)
    parser.add_argument("--whisper-bin", default=shutil.which("whisper") or "/opt/homebrew/bin/whisper")
    parser.add_argument("--initial-prompt", default=DEFAULT_INITIAL_PROMPT)
    parser.add_argument("--cn-json", type=Path, help="Existing Whisper transcribe JSON; skips Chinese STT.")
    parser.add_argument("--en-json", type=Path, help="Existing Whisper translate JSON; skips English translation.")
    parser.add_argument("--no-burn", action="store_true", help="Only write SRT/ASS/transcript files.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    video = args.video.expanduser().resolve()
    out_dir = args.out_dir.expanduser().resolve()
    if not video.exists():
        raise FileNotFoundError(video)

    work_dir = out_dir / "work"
    out_dir.mkdir(parents=True, exist_ok=True)

    cn_json = args.cn_json.expanduser().resolve() if args.cn_json else None
    en_json = args.en_json.expanduser().resolve() if args.en_json else None
    if not cn_json:
        cn_json = run_whisper(
            video=video,
            output_dir=work_dir / "zh",
            task="transcribe",
            model=args.model,
            model_dir=args.model_dir,
            language=args.language,
            whisper_bin=args.whisper_bin,
            device=args.device,
            initial_prompt=args.initial_prompt,
            threads=args.threads,
        )
    if not en_json:
        en_json = run_whisper(
            video=video,
            output_dir=work_dir / "en",
            task="translate",
            model=args.model,
            model_dir=args.model_dir,
            language=args.language,
            whisper_bin=args.whisper_bin,
            device=args.device,
            initial_prompt=args.initial_prompt,
            threads=args.threads,
        )

    cn_payload = read_json(cn_json)
    en_payload = read_json(en_json)
    segments = merge_segments(cn_payload, en_payload)
    if not segments:
        raise RuntimeError("No subtitle segments were generated.")

    transcript_payload = {
        "source_video": str(video),
        "style": args.style,
        "orientation": args.orientation,
        "model": args.model,
        "language": args.language,
        "segments": [segment.__dict__ for segment in segments],
    }
    write_json(out_dir / "transcript.bilingual.json", transcript_payload)
    write_srt(out_dir / "subtitles.zh.srt", segments, "cn")
    write_srt(out_dir / "subtitles.en.srt", segments, "en")
    write_srt(out_dir / "subtitles.bilingual.srt", segments, "bilingual")
    ass_path = out_dir / f"subtitles.{args.style}.{args.orientation}.ass"
    write_ass(ass_path, segments, style=args.style, orientation=args.orientation, video=video)

    video_output = out_dir / f"{video.stem}.bilingual.{args.style}.mp4"
    if not args.no_burn:
        burn_subtitles(video, ass_path, video_output, segments, style=args.style, orientation=args.orientation)

    print("\nDone.")
    print(f"Transcript JSON: {out_dir / 'transcript.bilingual.json'}")
    print(f"Bilingual SRT:   {out_dir / 'subtitles.bilingual.srt'}")
    print(f"Styled ASS:      {ass_path}")
    if not args.no_burn:
        print(f"Burned video:    {video_output}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}", file=sys.stderr)
        raise SystemExit(exc.returncode)
