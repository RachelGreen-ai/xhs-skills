# Bilingual Video Subtitler

Offline Chinese-English subtitles for creator videos.

## What It Does

This agent takes a video, transcribes Chinese speech with a local Whisper model, creates English translations, and exports polished bilingual subtitles for Xiaohongshu/RedNote or YouTube.

It can generate:

- A burned-in MP4 ready to post.
- Chinese SRT.
- English SRT.
- Bilingual SRT.
- Styled ASS subtitles.
- Editable bilingual transcript JSON.

## Why It Is Useful

Creators often lose time fixing captions by hand. Generic auto-caption tools also tend to look bland, mistranslate mixed Chinese-English technical terms, or produce subtitles that are too small for mobile feeds.

This workflow is built for creator posts about:

- AI learning
- career transition
- job hunting
- PhD to industry stories
- startup/product demos
- study notes and creator diaries

## Styles

### Tech Official

Clean, high-contrast subtitles for AI, career, and tutorial videos.

### Playful

Brighter Xiaohongshu-style subtitles for personal creator content, learning diaries, and career stories.

## Local First

The default model is `large-v3-turbo` when downloaded locally. This keeps the workflow private and avoids cloud STT costs.

## Example Command

```bash
python3 bilingual-video-subtitler/scripts/add_bilingual_subtitles.py \
  --video /absolute/path/input.mp4 \
  --out-dir out/subtitled-video \
  --style playful \
  --orientation xhs
```

## Notes

Whisper's built-in translation task translates source speech into English. The strongest default workflow is Chinese speech to Chinese-English subtitles.
