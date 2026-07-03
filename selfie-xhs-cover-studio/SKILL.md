---
name: selfie-xhs-cover-studio
description: Use this skill when a user wants to turn a selfie, portrait, product photo, or personal-brand topic into Xiaohongshu / RedNote-ready cover images, including style direction, AI image prompts, deterministic Chinese text overlays, caption hooks, hashtag suggestions, contact sheets, and a reusable creator visual system.
---

# Selfie XHS Cover Studio

## Outcome

Create a ready-to-post Xiaohongshu cover pack from one selfie or portrait:

- 9 cover concepts, usually 3 styles x 3 title angles
- 3:4 cover specs with accurate Chinese typography
- image-generation prompts for portrait/background layers
- caption hooks, hashtags, and reusable creator brand rules
- optional PNG covers and contact sheet via `scripts/render_cover_pack.py`

Sell the finished creator asset pack, not the AI tooling.

## Ask For

Ask only for missing essentials:

- selfie or portrait image
- creator niche or account positioning
- post topic
- target audience
- preferred language: Chinese, English, or bilingual
- desired vibe, if any

If the user does not know the vibe, choose 3 commercially useful styles from `references/style-system.md`.

## Workflow

1. Inspect the input photo.
   - Flag low-resolution, dark, heavily cropped, hidden-face, or multi-person images.
   - If usable, preserve face identity and improve only lighting, styling, background, crop, and polish.
2. Choose 3 post angles.
   - Use pain point, mistake, transformation, checklist, controversial truth, personal story, expert advice, before/after, money saved, or time saved.
3. Choose 3 visual styles.
   - Use style presets from `references/style-system.md`.
   - Match the niche and audience instead of using random aesthetics.
4. Generate or specify the portrait/background layer.
   - Do not ask the image model to render Chinese text.
   - Keep the face visible, flattering, and recognizable.
5. Add text deterministically.
   - Use `scripts/render_cover_pack.py` when producing PNGs from a cover JSON spec.
   - Use HTML/CSS, Playwright, PIL, or another deterministic renderer if adapting the workflow.
6. Package the output.
   - 9 cover files or detailed generation specs
   - contact sheet for fast comparison
   - captions and hashtags
   - reusable creator brand rules

## Output Format

Return:

- buyer-facing summary
- cover grid plan: 9 variants with style, title, subtitle, and visual direction
- exact image-generation prompts for background/portrait layer
- text overlay specs: canvas size, typography, color, placement, safe margins
- caption pack: title, opening line, caption starter, hashtags
- reuse rules: colors, fonts, title rhythm, face crop, layout pattern
- QA checklist

If producing files, save:

- `covers/cover-01.png` through `covers/cover-09.png`
- `covers/contact-sheet.png`
- `caption-pack.md`
- `brand-rules.md`
- optional `cover-spec.json`

## Rendering PNGs

Use the script when a deterministic text layer is needed:

```bash
python3 selfie-xhs-cover-studio/scripts/render_cover_pack.py \
  --spec examples/selfie-xhs-cover-studio/divorce-finance-cover-spec.json \
  --out out/selfie-xhs-cover-studio
```

The script accepts a JSON spec with `canvas`, optional `base_image`, and `variants`. Use it after AI image generation or for demo mockups.

## Quality Bar

- Covers must work at phone thumbnail size.
- Chinese text must be real text rendered by a deterministic layer, not hallucinated inside the generated image.
- Face identity should remain stable. Do not beautify so aggressively that the person becomes unrecognizable.
- Do not create misleading before/after claims, fake credentials, medical claims, legal claims, financial claims, or platform performance guarantees.
- Prefer a cohesive set over 9 unrelated images.

## References

- Read `references/style-system.md` before choosing styles.
- Read `references/output-template.md` before generating final deliverable text.
- Read `references/offer-packaging.md` when preparing marketplace listings, pricing, or sales demos.
- Read `references/demo-cases.md` when creating marketplace screenshots or sample outputs.
