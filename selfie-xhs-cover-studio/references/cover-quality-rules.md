# Cover Quality Rules

Use these rules whenever producing final Xiaohongshu covers, especially from a selfie.

## Feed-First Principle

Design for the compressed home feed thumbnail first. The viewer should understand the cover from:

- the face or body silhouette
- 3-5 large title chunks
- one clear emotional or practical hook

If the cover only works when opened full-screen, redesign it.

## Portrait Rules

- Make the person the main subject, not a small photo card.
- Use a real cutout or high-quality image edit when possible.
- Add a thick white sticker outline around the person. This is mandatory when retaining the selfie/photo background.
- Add a thin black outer edge or shadow outside the white outline when the background is busy.
- Let the person overlap the text or background layers; flat separated cards feel less native.
- Preserve the original photo background when it adds context, but crop or blur it so the original small person does not repeat behind the cutout.

## Background Rules

Use only two base background strategies:

- clean low-saturation solid background, usually cream, sage, muted blue, dusty pink, kraft tan, or soft green
- retained background from the user's selfie/photo, with the person cut out again in the foreground and a thick white sticker outline

Do not use busy generated backgrounds, generic gradients, large collage/photo tiles, or decorative background patterns as the default base. Template personality should come from foreground details: stickers, labels, doodles, title shape, and portrait layering.

## Title Rules

- Keep title copy short. Prefer 3-5 chunks, not a sentence.
- Arrange title chunks around the person contour: near head, shoulder, waist, or body edge.
- Do not stack everything in horizontal rows.
- Do not place important text at the extreme image edges.
- Use exactly two text roles:
  - main title: bold, large, chunky, feed-readable
  - subtitle/supporting text: thin font, smaller, preferably curved lightly along the portrait outline
- Use one unified title color per cover. For premium covers, prefer cream, warm white, mint-white, or pale lemon with dark green/charcoal stroke.
- Make the title playful through font shape, rotation, chunky scale, and contour placement; do not rely on colored word backgrounds for energy.
- Do not put a colored background block behind every title word by default. Use text shape, stroke, shadow, and placement first.
- Reserve colored background blocks for deliberately loud pop/variety-show styles only.
- Use bright contrast when the photo background is retained.
- Chinese text must be rendered deterministically with a CJK-capable font.
- Do not use decorative Latin fonts for Chinese; unsupported glyphs become boxes.
- For playful XHS titles, prefer the bundled `assets/fonts/ZCOOLKuaiLe-Regular.ttf` font or another cute CJK font.
- If a font does not support Chinese, do not use it for Chinese even if the Latin letters look cute.

## Typography System

Do not introduce many fonts. Covers should use only:

- Bold title font: the large headline chunks; use bundled `assets/fonts/ZCOOLKuaiLe-Regular.ttf` or another bold CJK display font.
- Thin subtitle font: small labels, subtitle, curved contour text, micro English/Chinese helper text; use a light CJK font such as STHeiti Light, Hiragino, or another thin readable font.

The main title carries impact. The thin subtitle adds polish and can follow the white portrait outline with a slight arc. Avoid multiple decorative fonts in one cover.

## Recommended Contour Title Pattern

For a transformation story such as "从硬件PhD到AI Engineer":

- Chunk 1 near head: 从硬件
- Chunk 2 near upper shoulder: PhD
- Chunk 3 near waist or lower left body edge: 到AI
- Chunk 4 near lower body edge: Engineer

Keep these chunks visually close to the cutout outline. They should feel like stickers orbiting the person.

## Color Rules

- Use one dominant title color.
- For clean premium covers, use restrained palettes such as deep green, charcoal, cream, mint, glass blue, and pale pink.
- A good default is cream or mint-white title text with deep green/charcoal stroke.
- Use red/yellow only when the requested style is explicitly loud, variety-show, or sale/discount oriented.
- Use dark green or charcoal stroke for readability.
- Add a cream or white outside stroke when text sits on a photo background.
- Use accent shapes for energy, but do not give every word a different color.
- Keep small badges secondary and do not let them compete with the title.

## Avoid

- tiny portrait cards
- long subtitles
- one-line-one-row PPT layouts
- many unrelated colors in title text
- more than two font roles
- busy generated backgrounds
- default red/yellow color palettes
- title background blocks behind every word
- dense captions at the bottom
- small text that only works full-screen
- repeated person from the retained background
- random decorative text that does not help the hook

## Default Premium Recipe

When the user does not specify a style, start here:

- retain useful real-photo background context
- add one large portrait cutout with cream/white outline
- use 4 large title chunks arranged around the person contour
- add one thin curved subtitle around the portrait outline when it improves polish
- use one title fill color: cream, warm white, or mint-white
- use deep green or charcoal stroke
- add only 1-3 small accents: soft ring, hand-drawn squiggle, or tiny label
- no colored title background blocks
- no red/yellow default palette
