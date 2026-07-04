# Output Template

## Buyer Summary

I created a 9-cover Xiaohongshu pack for:

- creator niche:
- post topic:
- audience:
- visual strategy:

For template-driven jobs, use this shorter summary:

- input image:
- exact title:
- selected template style:
- background mode:
- subtitle / badge:
- why this template fits:

## Cover Grid

| # | Style | Angle | Main Title | Subtitle | Visual Direction |
|---|---|---|---|---|---|
| 01 | Pop Tutorial | Beginner Hook |  |  |  |
| 02 | Notebook Job Hunt | Mistake |  |  |  |
| 03 | Creator Skill Launch | Build in Public |  |  |  |
| 04 | Fresh Study Card | Checklist |  |  |  |
| 05 | Bold Viral | Pain Point |  |  |  |
| 06 | AI Side Hustle | Experiment |  |  |  |
| 07 | Template Maker | Workflow |  |  |  |
| 08 | Campus Career | Practical Tip |  |  |  |
| 09 | Data Proof | Tool Review |  |  |  |

## Image Layer Prompt Pattern

Create a polished editorial portrait based on the provided selfie. Preserve the person's facial identity, facial structure, age range, and recognizable features. Improve lighting, styling, crop, and background only. No text in the image. 3:4 vertical composition. Leave clean negative space for a Chinese headline.

Add style-specific details after this base prompt. For AI learning, job-search, and creator-tool content, prefer clean but platform-native XHS styling: portrait cutout, cream/white sticker outline, playful contour title space, light doodles, subtle grid paper, and restrained premium colors.

For final covers, follow `cover-quality-rules.md`: large cutout, thick cream/white person outline, unified title color, no title background blocks by default, and short title chunks placed around the person contour.

## Text Overlay Spec

- canvas:
- template style:
- headline:
- subtitle:
- badge:
- font direction:
- font roles:
  - main title: bold big title font
  - subtitle/support text: thin font, lightly curved along portrait outline when possible
- background mode:
- headline placement:
- headline lockup:
- contour placement plan:
- portrait avoidance plan for main title:
- crop plan:
- subtitle placement:
- solid background color:
- safe margins:
- color palette:

For renderer-based demos, prefer `layout: "contour"` with `contour_chunks`:

```json
{
  "layout": "contour",
  "contour_chunks": [
    {"text": "从硬件", "x": 0.22, "y": 0.27, "size": 132, "angle": -7},
    {"text": "PhD", "x": 0.24, "y": 0.43, "size": 168, "angle": 6},
    {"text": "到AI", "x": 0.78, "y": 0.37, "size": 148, "angle": 7},
    {"text": "Engineer", "x": 0.68, "y": 0.68, "size": 122, "angle": -6}
  ]
}
```

Do not add colored title backgrounds unless the selected style is explicitly loud/pop.

## Caption Pack

Title options:

1.
2.
3.

Opening hooks:

1.
2.
3.
4.
5.

Caption starter:

Hashtags:

## QA Checklist

- face is recognizable
- crop emphasizes head and upper body when lower body distracts from the hook
- no broken text inside the image layer
- Chinese title is readable at thumbnail size
- top title safe space is preserved when requested
- subtitle sits under a top headline when that is the clearest title lockup
- main title chunks orbit the portrait contour and do not overlap the portrait cutout
- provided subtitle is visible and readable
- solid background uses one consistent color unless a split paper/card template was requested
- main title uses one dominant color with strong outline contrast
- post claim is not misleading
- covers feel like one creator brand, not random templates
