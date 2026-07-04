---
name: selfie-xhs-cover-studio
description: Use this skill when a user wants to turn a selfie, portrait, product photo, or personal-brand topic into Xiaohongshu / RedNote-ready cover images, especially when they provide one image plus a title and want to choose a reusable template style. Includes template selection, AI image prompts, deterministic Chinese text overlays, caption hooks, hashtag suggestions, contact sheets, and a reusable creator visual system.
---

# Selfie XHS Cover Studio

## Outcome

Create a ready-to-post Xiaohongshu cover pack from one selfie or portrait:

- template-driven single-cover generation from one image, one title, and a selected style
- 9 cover concepts, usually 3 styles x 3 title angles
- 3:4 cover specs with accurate Chinese typography
- image-generation prompts for portrait/background layers
- caption hooks, hashtags, and reusable creator brand rules
- optional PNG covers and contact sheet via `scripts/render_cover_pack.py`

Sell the finished creator asset pack, not the AI tooling.

Primary commercial niches:

- AI learning notes and tool tutorials
- job search, resume, interview, LinkedIn, and career content
- Capafy skill launches and build-in-public posts
- creator workflows, productivity systems, and side-project experiments

## Ask For

Ask only for missing essentials:

- selfie or portrait image
- creator niche or account positioning
- post topic
- exact title text for the cover
- background preference: low-saturation solid color, or retain selfie background
- target audience
- preferred language: Chinese, English, or bilingual
- template style, if any

If the user does not know the template style, read `references/template-style-library.md` and recommend 2-3 options.

## Workflow

1. Understand the buyer and use case.
   - Read `references/buyer-persona.md` when choosing defaults, writing marketplace copy, or judging whether a cover feels sellable.
   - Prioritize speed, platform-native taste, readable Chinese typography, and reusable template choices.
2. Inspect the input photo.
   - Flag low-resolution, dark, heavily cropped, hidden-face, or multi-person images.
   - If usable, preserve face identity and improve only lighting, styling, background, crop, and polish.
3. Choose a template mode.
   - For "one image + one title" requests, use a template style from `references/template-style-library.md`.
   - For broader ideation, choose 3 post angles and 3 styles.
   - Read `references/reference-template-breakdown.md` when learning from provided examples or making template previews.
   - Never remove watermarks from third-party reference images. Use references as moodboards and rebuild clean original templates unless the creator confirms usage rights.
4. Choose 3 post angles when making a pack.
   - Use pain point, mistake, transformation, checklist, controversial truth, personal story, expert advice, before/after, money saved, or time saved.
5. Choose visual styles.
   - Use style presets from `references/style-system.md`.
   - Use template presets from `references/template-style-library.md` when the buyer wants to choose a reusable template.
   - Match the niche and audience instead of using random aesthetics.
6. Generate or specify the portrait/background layer.
   - Do not ask the image model to render Chinese text.
   - Keep the face visible, flattering, and recognizable.
   - Prefer a large portrait cutout with a thick white sticker outline over a small photo card.
   - For casual selfies where the lower body pulls attention away from the hook, crop the foreground to head and upper body first, then place the cutout lower on the canvas so the top third stays open for the title.
   - If preserving the original photo background, crop or blur it so the original small person does not repeat behind the cutout, then add the foreground person again with a thick white sticker outline.
   - If not preserving the original photo background, use a clean low-saturation solid color.
7. Add text deterministically.
   - Use `scripts/render_cover_pack.py` when producing PNGs from a cover JSON spec.
   - Use HTML/CSS, Playwright, PIL, or another deterministic renderer if adapting the workflow.
   - Use only two text roles: bold big main title and thin subtitle/supporting text.
   - Place the bold main title in negative space around the portrait; it must not overlay the person.
   - When the user asks for top negative space, keep the main title horizontal and parallel to the cover edges.
   - If the user provides a subtitle, render it clearly. Do not omit it or hide it as tiny edge decoration.
   - Place the thin subtitle on a slight curve outside the portrait outline when possible. It can follow the white sticker border, but must not touch the person, overlap the outline, or sit at the extreme cover edge.
   - For final covers, prefer contour title placement: short title chunks orbit the person outline instead of sitting in rows.
8. Package the output.
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
  --spec examples/selfie-xhs-cover-studio/ai-career-cover-spec.json \
  --out out/selfie-xhs-cover-studio
```

The script accepts a JSON spec with `canvas`, optional `base_image`, and `variants`. Use it after AI image generation or for demo mockups.

Template preview demo:

```bash
python3 selfie-xhs-cover-studio/scripts/render_cover_pack.py \
  --spec examples/selfie-xhs-cover-studio/template-cover-spec.json \
  --out out/selfie-xhs-cover-studio-templates
```

## Quality Bar

- Covers must work at phone thumbnail size.
- Chinese text must be real text rendered by a deterministic layer, not hallucinated inside the generated image.
- Use only two text roles: bold big main title and thin subtitle/supporting text.
- Use bright fill colors for all readable text by default, with dark strokes/shadows for contrast.
- Main title must not overlay the portrait cutout; subtitle must be present when provided.
- Use only two base background modes: clean low-saturation solid color, or retained selfie background with thick white portrait outline.
- Details sell the image: preserve small labels, edge texture, paper/grid/doodle treatments, portrait sticker edges, type angle, and layer depth when applying a template.
- Use Xiaohongshu-native visual language: bold outlined headlines, large portrait cutouts, contour title stickers, light doodles, and information-rich layouts. Use bright blocks only for explicitly loud/pop variants.
- Main title color should usually be unified across chunks; use black and white outlines for contrast instead of making every word a different color.
- Use 3-5 large title chunks around the portrait contour. Avoid long sentence subtitles and one-line-one-row layouts.
- Do not add colored background blocks behind title chunks by default. Use clean strokes, shadows, and restrained accents unless the user explicitly wants a loud pop style.
- Prefer the bundled ZCOOL KuaiLe font for playful Chinese title stickers. If using another font, verify it supports every Chinese character before rendering.
- Face identity should remain stable. Do not beautify so aggressively that the person becomes unrecognizable.
- Do not create misleading before/after claims, fake credentials, medical claims, legal claims, financial claims, or platform performance guarantees.
- Prefer a cohesive set over 9 unrelated images.

## References

- Read `references/buyer-persona.md` before making product, pricing, template, or marketplace decisions.
- Read `references/style-system.md` before choosing styles.
- Read `references/template-style-library.md` before template-based generation or when learning styles from references.
- Read `references/reference-template-breakdown.md` before using creator-provided reference images as template inspiration.
- Use `assets/template-styles/template-library.json` as the machine-readable starter template list when building UI choices or adding new templates.
- Read `references/cover-quality-rules.md` before designing or rendering final covers.
- Read `references/output-template.md` before generating final deliverable text.
- Read `references/offer-packaging.md` when preparing marketplace listings, pricing, or sales demos.
- Read `references/demo-cases.md` when creating marketplace screenshots or sample outputs.
