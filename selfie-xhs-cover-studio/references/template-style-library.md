# Template Style Library

Use this reference when the buyer wants a template-driven flow: one image, one title, and one selected template style.

When the creator provides reference covers, use them as template sources at the level of craft: layout, color, type hierarchy, foreground/background layering, sticker edges, small labels, texture, doodles, and title motion. Do not reduce them to a broad vibe word.

Do not remove watermarks from third-party reference images or package watermarked references as template assets unless the creator confirms usage rights. Treat references as moodboards by default: extract layout, color, type hierarchy, and composition, then rebuild clean original templates.

## User Entry Flow

Ask for:

- portrait or selfie
- exact title text
- optional subtitle or badge
- template style ID

If the buyer does not know which style to choose, recommend 2-3 based on topic:

- AI learning, career pivot, founder diary: `clean-premium-contour`, `kraft-grid-labels`
- job search, resume, interview: `kraft-grid-labels`, `outdoor-doodle-bigtype`
- tool review, listicle, tutorial: `food-collage-sticker`, `outdoor-doodle-bigtype`
- emotional personal story: `sunlit-editorial-story`, `clean-premium-contour`
- product or skill launch: `food-collage-sticker`, `kraft-grid-labels`

## Template Styles

### clean-premium-contour

Use for AI career pivots, founder notes, higher-trust creator posts, and premium personal branding.

- visual DNA: retained real-photo background, large portrait cutout, thick cream/white outline, 3-5 large title chunks orbiting the person contour
- palette: deep green, cream, mint, glass blue, pale pink accent
- title behavior: no colored title backgrounds; use cream or mint-white fill with deep green/charcoal stroke
- best title rhythm: `从硬件 / PhD / 到AI / Engineer`, `科研背景 / 转AI`, `不是重来 / 是升级`
- avoid: many colors, red/yellow default palette, long subtitles

### food-collage-sticker

Inspired by high-energy Xiaohongshu collage covers. Use for tool lists, recommendations, city guides, comparison posts, product roundups, and "save this list" content.

- visual DNA: several background tiles, sticker-cut portrait in front, thick outlined headline, diagonal bottom banner
- palette: espresso or charcoal frame, cream title, amber/mint/coral/blue collage blocks, orange or coral banner
- title behavior: 2-3 large chunks, heavy black/dark stroke, slight slant for motion
- best title rhythm: `推荐清单`, `这几个工具`, `都藏在这里`
- avoid: actual watermarked food photos unless the buyer owns them; rebuild collage tiles or use buyer-provided assets

### kraft-grid-labels

Inspired by scrapbook / child-fashion / lifestyle label covers. Use for structured notes, career guides, travel planning, campus posts, and "route map" content.

- visual DNA: warm kraft background, white grid-paper area, tape strips, small labels, large cutout portrait, badge stickers
- palette: kraft tan, cream, muted blue, deep brown, sage accent
- title behavior: one strong banner title at top or upper third, small English tag optional
- best title rhythm: `摆脱路人感`, `求职路线图`, `AI学习路线`
- avoid: overdecorating; keep labels small and readable

### outdoor-doodle-bigtype

Inspired by outdoor season / childlike energy covers. Use for motivation, learning diaries, monthly recaps, beginner stories, and optimistic growth content.

- visual DNA: natural green background or soft outdoor blur, oversized title in upper half, hand-drawn white doodles, playful arrows and circles
- palette: forest green, lemon-lime, white, soft yellow, small charcoal details
- title behavior: huge title, 1-2 lines only, playful stroke or glow; title should remain readable in feed
- best title rhythm: `十月你好`, `AI学习第7天`, `今天也要继续`
- avoid: tiny text, too many decorative words, weak contrast over foliage

### sunlit-editorial-story

Inspired by sunny personal-story covers. Use for emotional essays, transformation stories, self-growth, mindset, relationships, and gentle creator posts.

- visual DNA: sunlit outdoor/photo background, portrait on one side, elegant oversized title, minimal handwritten arcs or white line accents
- palette: leaf green, warm sunlight, pale yellow title, white secondary text, muted coral label
- title behavior: editorial title chunks with airy spacing; optional small hashtag or quote label
- best title rhythm: `允许一切发生`, `爱你已经很好了`, `慢慢变好`
- avoid: cluttered captions, low-contrast yellow on bright background, adding too many hashtags

## Template QA

Before final delivery, verify:

- title is readable at a small phone-feed size
- face is not covered by title
- template style is recognizable without copying a watermarked reference
- Chinese text is deterministic and not hallucinated by the image model
- the buyer can reuse the same template with a new title/photo
- at least 5 template-specific details are present, such as sticker outline, tiny label, paper texture, doodle marks, edge microcopy, title slant, or foreground overlap

## Adding New Templates

When the creator provides more reference images:

1. Inspect 1-5 references and extract visual DNA: composition, title hierarchy, palette, person/text relationship, accents, and avoid rules.
2. Do not edit out watermarks from the references. Rebuild a clean original template inspired by the layout.
3. Add a new entry to `assets/template-styles/template-library.json`.
4. Add a matching variant to `examples/selfie-xhs-cover-studio/template-cover-spec.json` when a deterministic preview is useful.
5. Render previews with `scripts/render_cover_pack.py` and save clean preview PNGs under `assets/template-previews/`.
6. Update this file only when the new template adds a meaningfully distinct style, not just a color variation.
