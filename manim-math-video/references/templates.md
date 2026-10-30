# Templates and series consistency

A template is a visual and narrative contract. It is not a decoration. It fixes the palette, typography, spacing, graph styling, motion language, caption behavior, and the rhythm of the episode.

Choose one template per series. Episodes inherit it. A one-off restyle is a new series unless the user explicitly asks for a deliberate change.

## Catalog

### `clean-light` — Clarity

**Look:** warm off-white background, dark ink, cobalt primary, amber secondary, generous white space, precise sans-serif type.

**Best for:** general explainers, classroom material, graph-led episodes, accessibility-first work, daylight viewing.

**Motion:** write/fade, short transitions, calm pacing.

**Avoid:** dramatic reveals that need a dark canvas; very long formal proofs without visual breathing room.

### `dark-board` — Nocturne

**Look:** deep navy-black background, chalk-white ink, cyan and violet accents, amber highlights, monospace-flavored equations, high contrast.

**Best for:** science, technology, mathematical explanations, dramatic treatments, long-form technical videos, nocturnal viewing.

**Motion:** create/draw, glow-like accent reveals, slower holds, more dramatic emphasis.

**Avoid:** printing-heavy handouts, low-contrast projectors, brand palettes that clash with cyan/violet.

### `paper-editorial` — Marginalia

**Look:** warm paper, dark brown ink, oxblood and olive accents, serif headings and body, ruled lines and margin notes.

**Best for:** history, philosophy, literature, culture, essayistic explanations, biographies, gentle long-form.

**Motion:** fade/write, page-like transitions, restrained camera movement.

**Avoid:** fast social-media edits, neon data viz, highly kinetic animation.

## Selection matrix

| Signal | Recommendation |
|---|---|
| General audience, unknown style | `clean-light` |
| First-year calculus or linear algebra | `dark-board` |
| Proof-heavy but not dramatic | `clean-light` |
| History, philosophy, biography | `paper-editorial` |
| Classroom projector with washed-out colors | `clean-light` |
| YouTube long-form, evening viewing | `dark-board` |
| Series already has a template | Inherit it |
| User wants a new look for one episode | Warn; use a template for a new series or get explicit approval |

If two templates fit, choose the one that makes the **graphs** clearest for the audience, not the one that looks best in isolation.

## What the template controls

- background, surface, ink, muted text, grid, axis;
- semantic roles: `primary`, `secondary`, `success`, `danger`, `warning`;
- heading/body/mono font stacks and sizes;
- margins, graph dimensions, bullet spacing;
- graph stroke width, tick size, label size, area opacity;
- motion style and transition duration;
- caption behavior and maximum characters per cue;
- intro/outro rhythm;
- narrative beat structure and words-per-minute target.

The template files live in `assets/templates/<id>.json`. The scaffold copies the chosen file to the episode as `theme.json`, so later edits to the catalog do not silently restyle an old episode.

## Series consistency rules

1. **Lock the template and its version.** Record `template` and `template_version` in `series.json`. Do not edit the episode's `theme.json` unless the user wants a new visual identity.
2. **Lock the voice and language.** Same narrator, same locale, same rate/pitch. A guest voice must be a deliberate format choice, not a convenience.
3. **Lock the quality.** Standard final quality for the series; drafts are temporary.
4. **Lock the title grammar.** Examples: "Why <claim>?", "<Object> is <surprise>", "The <concept> behind <phenomenon>". Use the same title card layout.
5. **Lock the narrative rhythm.** Same beat order, same average length, same recap/outro placement.
6. **Lock color semantics.** Primary = the object under study; secondary = comparison; danger = misconception; success = conclusion. Do not recolor roles per episode.
7. **Reuse the notation glossary.** `series.json` or `glossary.json` keeps symbols, units, and pronunciations consistent.
8. **Number episodes deterministically.** `s01e001`, zero-padded, with a slug. Never renumber published episodes.
9. **Keep a series bible.** In `series.json`, record the title, one-line premise, audience, visual motif, and episode list.
10. **Allow deliberate evolution only through a versioned template.** Add `dark-board-v2` rather than editing `dark-board` in place.

## Adding a template

1. Copy an existing JSON file and change the `id`, `name`, and `version`.
2. Keep the required keys. Validate with:

   ```bash
   python scripts/validate.py --template assets/templates/my-template.json
   ```

3. Test one 15-second scene with a title, a graph, and a caption before using it for a full episode.
4. Add it to this catalog and to the selection matrix.
5. Never rename an existing template id. Use a new version.

## Template anatomy

Required top-level keys:

```json
{
  "schema_version": 1,
  "id": "clean-light",
  "name": "Clarity",
  "version": "1.0.0",
  "description": "...",
  "best_for": ["..."],
  "aspect_ratio": "16:9",
  "background": "#F7F5F0",
  "surface": "#FFFFFF",
  "ink": "#1F2937",
  "muted": "#6B7280",
  "roles": {
    "primary": "#2563EB",
    "secondary": "#D97706",
    "success": "#059669",
    "warning": "#D97706",
    "danger": "#DC2626",
    "grid": "#D1D5DB",
    "axis": "#6B7280"
  },
  "fonts": {
    "heading": ["Inter", "Segoe UI", "DejaVu Sans"],
    "body": ["Inter", "Segoe UI", "DejaVu Sans"],
    "mono": ["JetBrains Mono", "Consolas", "DejaVu Sans Mono"]
  },
  "sizes": {
    "title": 58,
    "heading": 44,
    "body": 30,
    "bullet": 30,
    "caption": 24,
    "equation": 46,
    "label": 22,
    "tick": 18
  },
  "layout": {
    "margin": 0.7,
    "heading_top_buff": 0.45,
    "graph_width": 9.6,
    "graph_height": 5.0,
    "graph_center_y": -0.75,
    "text_max_width": 11.5,
    "bullet_spacing": 0.35,
    "column_gap": 0.9
  },
  "graph": {
    "stroke_width": 5,
    "axis_stroke_width": 2.5,
    "tick_size": 18,
    "label_size": 22,
    "tick_label_buff": 0.12,
    "area_opacity": 0.22,
    "dot_radius": 0.07,
    "grid_opacity": 0.25
  },
  "motion": {
    "style": "write",
    "transition": "fade",
    "transition_time": 0.28,
    "default_hold": 0.25,
    "reveal_lag": 0.18
  },
  "captions": {
    "enabled": true,
    "max_chars": 84,
    "tail_pad": 0.15
  },
  "story": {
    "beats": ["title", "section", "graph", "equation", "bullets", "compare", "recap", "outro"],
    "words_per_minute": 145
  }
}
```

`motion.style` accepts `write`, `fade`, or `draw`. `motion.transition` accepts `fade`, `slide`, or `none`. The runtime currently implements `fade` and `none` transitions; `slide` falls back to a short fade.

## Template drift check

`new_episode.py` compares the brief's template, voice, language, and quality with `series.json`. A mismatch is an error unless `--allow-style-drift` is passed. Use that flag only after the user has explicitly approved the change and you have recorded the reason in the brief under `series.consistency_note`.

## Previewing a template

Use a tiny storyboard with a title, one graph, one equation, and an outro. Render at `draft` and inspect:

- Is the heading legible at 480p?
- Do axis labels collide with the graph?
- Does the caption fit?
- Does the accent color carry the meaning?
- Does the intro set the right tone in 3 seconds?
