---
name: bilingual-video-subtitler
description: Add Chinese-English bilingual subtitles to videos with local Whisper STT, styled subtitle presets, SRT/ASS export, and optional burned-in MP4 output. Use for Xiaohongshu, RedNote, YouTube Shorts, Reels, or longer YouTube videos where the user wants offline transcription plus polished bilingual subtitles.
---

# Bilingual Video Subtitler

## Overview

Use this skill when the user wants to add bilingual Chinese-English subtitles to a video, especially Chinese spoken videos for Xiaohongshu/RedNote today and YouTube later. The default workflow uses the local OpenAI Whisper CLI and prefers the downloaded `large-v3-turbo` model when available.

The skill should produce practical creator-ready outputs:

- Burned-in MP4 with styled Chinese-English subtitles.
- `subtitles.zh.srt`, `subtitles.en.srt`, and `subtitles.bilingual.srt`.
- Styled `.ass` subtitle file for re-rendering or manual polish.
- `transcript.bilingual.json` so the text can be reviewed, corrected, or reused in captions.

## Default Workflow

1. Confirm the input video path and target platform.
2. Pick a subtitle style:
   - `tech`: clean official tech feeling for AI, career, learning, startup, product, and explainer videos.
   - `playful`: brighter Xiaohongshu feeling for lifestyle-learning, career transition, study notes, and personable creator content.
3. Run the helper script:

```bash
python3 bilingual-video-subtitler/scripts/add_bilingual_subtitles.py \
  --video /absolute/path/to/video.mp4 \
  --out-dir out/my-subtitled-video \
  --style tech \
  --orientation xhs
```

4. Review the generated bilingual SRT/JSON. If the text needs correction, edit the JSON/SRT and rerun the burn step using the corrected JSON files.
5. Deliver the burned MP4 plus editable subtitle files.

## Local Model Choice

Prefer local/offline STT over cloud APIs by default. On Rachel's machine, the best available downloaded model is:

```text
~/.cache/whisper/large-v3-turbo.pt
```

Use `large-v3-turbo` as the default because it is a good balance of Chinese accuracy and runtime. Use `small` only when the user explicitly prioritizes speed over accuracy.

For Chinese speech, the script runs Whisper twice:

- `task=transcribe` for the Chinese transcript.
- `task=translate` for English translation.

This is strongest for Chinese speech -> Chinese + English subtitles. If the source audio is mostly English and the user needs Chinese translation, explain that Whisper's built-in translate task only translates into English; use a separate translation pass before final burn-in.

## Dependencies

Required:

- `ffmpeg` and `ffprobe` for video handling.
- OpenAI Whisper CLI, available as `whisper`.
- A downloaded local Whisper model, preferably `large-v3-turbo`.
- `Pillow` for the fallback burn-in renderer.

The script first tries FFmpeg's native `ass` or `subtitles` filter. If the installed FFmpeg was built without subtitle filters, it automatically falls back to rendering frames with Pillow and then reassembling the MP4 with FFmpeg.

## Commands

### Xiaohongshu vertical video

```bash
python3 bilingual-video-subtitler/scripts/add_bilingual_subtitles.py \
  --video /absolute/path/input.mp4 \
  --out-dir out/input-xhs-subtitles \
  --style playful \
  --orientation xhs
```

### YouTube horizontal video

```bash
python3 bilingual-video-subtitler/scripts/add_bilingual_subtitles.py \
  --video /absolute/path/input.mp4 \
  --out-dir out/input-youtube-subtitles \
  --style tech \
  --orientation youtube
```

### Generate subtitle files without burning

```bash
python3 bilingual-video-subtitler/scripts/add_bilingual_subtitles.py \
  --video /absolute/path/input.mp4 \
  --out-dir out/input-subtitles \
  --style tech \
  --orientation auto \
  --no-burn
```

### Reuse corrected Whisper JSON

```bash
python3 bilingual-video-subtitler/scripts/add_bilingual_subtitles.py \
  --video /absolute/path/input.mp4 \
  --cn-json /absolute/path/chinese.json \
  --en-json /absolute/path/english.json \
  --out-dir out/input-final \
  --style playful \
  --orientation xhs
```

## Quality Notes

Short-form subtitles must be readable after feed compression. Keep the Chinese line large, the English line smaller, and avoid placing subtitles too close to the bottom UI area. For Xiaohongshu, prefer vertical `1080x1920` output and keep subtitle contrast high.

Use `references/subtitle-style-guide.md` when tuning visual details.
