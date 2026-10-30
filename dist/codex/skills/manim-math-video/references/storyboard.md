# The storyboard

The mathematical examples below demonstrate the format. For other topics, use a chronology, explanation, procedure, comparison, analysis, or narrative. Graphs, equations, and misconceptions are optional. Use an `image` beat for an existing illustration and implement `custom_beat` for animated timelines, maps, flowcharts, or character scenes; those are not built-in beat kinds.

`storyboard.json` is the bridge between the argument and the render. It is machine-readable, so the default `Episode` scene can render every standard beat without handwritten Manim code, and it is human-readable, so the voice, pacing, and visuals can be reviewed before a single frame is rendered.

The schema is `assets/storyboard.schema.json`. A filled example is `assets/storyboard.example.json`.

## Top level

```json
{
  "schema_version": 1,
  "episode_id": "s01e001",
  "episode_slug": "why-derivative-x-squared",
  "title": "Why the derivative of x² is 2x",
  "language": "en-US",
  "template": "clean-light",
  "target_duration_seconds": 360,
  "beats": []
}
```

- `episode_id` uses `s<season two digits>e<episode three digits>`.
- `language` must match `brief.output.language`.
- `template` must match the episode theme.
- `beats` is ordered. Each beat has one narration segment, one visual idea, and one audio file.

## Common beat fields

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | Unique, lowercase, hyphens/underscores. Used for audio file names. |
| `kind` | yes | One of the beat kinds below. |
| `narration` | yes | Spoken script for this beat. Can be empty only if `silent` is true. |
| `speech` | no | Spoken form sent to TTS when it differs from `narration`. |
| `caption` | no | Subtitle text when it differs from `narration` (translation, cleaner notation). |
| `notes` | no | Why this beat exists, visual intent, math checks. Not rendered. |
| `silent` | no | If true, no narration. Requires `duration_hint`. |
| `duration_hint` | no | Seconds for a silent beat, or a target for a narrated beat. |
| `clear` | no | Fade out the visual at the end. Default `true`. Set `false` to carry visuals into the next beat. |
| `hold` | no | Extra seconds the beat stays on screen after its narration ends. Use it for recaps, conclusions, and any frame that needs reading time. |

The runtime adds a small tail pad after each narration segment (from `theme.captions.tail_pad`), so do not add "..." or trailing silence to the script.

## Beat kinds

### `title`

The hook and promise. One per episode, first beat.

```json
{
  "id": "title",
  "kind": "title",
  "narration": "What does the slope of a curve at a single point even mean?",
  "title": "Why the derivative of x² is 2x",
  "subtitle": "A limit you can see",
  "kicker": "Path of Knowledge · S01E001"
}
```

The runtime adds the series title and episode label when `kicker` is omitted.

### `section`

A chapter card. Use sparingly: 2-4 per episode.

```json
{
  "id": "the-question",
  "kind": "section",
  "narration": "Let's start with the question that the formula hides.",
  "heading": "The question",
  "subheading": "Average slope versus instantaneous slope"
}
```

### `bullets`

A short list of claims, steps, or observations. Keep items under ~12 words.

```json
{
  "id": "chain",
  "kind": "bullets",
  "narration": "The argument has three moves: average, limit, and cancellation.",
  "heading": "Three moves",
  "items": [
    "Measure the average slope over h.",
    "Shrink h toward zero.",
    "Cancel h before taking the limit."
  ],
  "reveal": "one_by_one"
}
```

Items may be strings or objects:

```json
{"text": "The h cancels.", "emphasis": true}
```

`reveal` accepts `one_by_one` (default) or `all`.

### `equation`

A typeset equation or derivation. Requires LaTeX.

```json
{
  "id": "definition",
  "kind": "equation",
  "narration": "The derivative is the limit of the secant slope as h approaches zero.",
  "speech": "The derivative is the limit of the secant slope as h approaches zero.",
  "heading": "The definition",
  "latex": "f'(x) = \\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}",
  "highlight": ["h"],
  "notes": "This is the formal bridge from geometry to algebra."
}
```

`steps` transforms through a sequence:

```json
"steps": [
  "f'(x) = \\lim_{h \\to 0} \\frac{(x+h)^2 - x^2}{h}",
  "f'(x) = \\lim_{h \\to 0} \\frac{2xh + h^2}{h}",
  "f'(x) = \\lim_{h \\to 0} (2x + h) = 2x"
]
```

If each step needs its own explanation, use separate beats with `clear: false` instead of one long beat with `steps`. The audio is one segment per beat, so multiple steps in one beat share one narration budget.

`highlight` is a list of substrings to color with the primary role. If a substring appears more than once, all occurrences are colored.

### `graph`

A 2D graph, plot, or diagram. The graph spec is documented in `references/graphs.md`.

```json
{
  "id": "secant",
  "kind": "graph",
  "narration": "Two points on the parabola define a secant line. Its slope is the average rate over that interval.",
  "heading": "Average slope",
  "notes": "The secant is the average; the tangent is the limit.",
  "graph": {
    "type": "cartesian",
    "x_range": [-1, 4, 1],
    "y_range": [-1, 10, 2],
    "x_label": "x",
    "y_label": "f(x)",
    "plots": [
      {"expr": "x**2", "color_role": "primary", "label": "f(x) = x²"}
    ],
    "annotations": [
      {"type": "point", "x": 1, "y": 1, "label": "P"},
      {"type": "point", "x": 3, "y": 9, "label": "Q"},
      {"type": "secant", "x1": 1, "x2": 3, "expr": "x**2", "label": "average slope = 4"}
    ],
    "animation": "draw"
  }
}
```

The graph must answer a question. In `notes`, write the sentence "This graph shows ___ because ___." If you cannot fill both blanks, cut the graph.

### `compare`

A side-by-side correction: misconception vs. correct move, before vs. after, two interpretations.

```json
{
  "id": "misconception",
  "kind": "compare",
  "narration": "The common mistake is to set h equal to zero before cancelling. That turns the difference quotient into zero over zero.",
  "heading": "The trap",
  "left": {
    "heading": "Common mistake",
    "items": ["Set h = 0 immediately.", "Get 0/0.", "Conclude the slope is undefined."],
    "role": "danger"
  },
  "right": {
    "heading": "Correct move",
    "items": ["Cancel h first.", "Then let h approach 0.", "Read off 2x."],
    "role": "success"
  }
}
```

### `recap`

The chain in 3-4 lines. One per episode, near the end.

```json
{
  "id": "recap",
  "kind": "recap",
  "narration": "So the derivative is not a new formula. It is the limit of an average slope, and the algebra is what survives the limit.",
  "heading": "What we established",
  "items": [
    "A secant slope is an average rate.",
    "The limit turns it into an instantaneous rate.",
    "Cancelling h is the step that makes the limit finite."
  ]
}
```

### `outro`

The next question and series continuity.

```json
{
  "id": "outro",
  "kind": "outro",
  "narration": "Next time: what happens when the curve is not a parabola?",
  "heading": "Next question",
  "next": "What happens when the function is not a parabola?",
  "cta": "Subscribe for the next path."
}
```

### `quote`

A historical or conceptual quote. Use real quotes only.

```json
{
  "id": "quote",
  "kind": "quote",
  "narration": "Newton described fluxions as quantities flowing, not as formulas.",
  "quote": "I consider mathematical quantities ... as described by a continual motion.",
  "attribution": "Isaac Newton, Method of Fluxions"
}
```

### `image`

A static image, diagram, portrait, or scan.

```json
{
  "id": "portrait",
  "kind": "image",
  "narration": "Euler worked on this identity while losing his sight.",
  "path": "assets/euler.jpg",
  "alt": "Portrait of Leonhard Euler",
  "label": "Leonhard Euler (1707-1783)",
  "width": 5.0
}
```

`path` is relative to the episode directory. Keep image rights and attribution in `brief.accuracy.sources` or the label.

### `custom`

An escape hatch for a visual the standard beats cannot express. The generated `episode.py` must override `custom_beat`.

```json
{
  "id": "camera-zoom",
  "kind": "custom",
  "narration": "Now zoom into the point where the secant becomes a tangent.",
  "notes": "Move the camera toward (1,1) and reveal the local linearity.",
  "duration_hint": 12
}
```

The default implementation raises a clear error so a missing override cannot silently produce an empty beat.

## Pacing

- Spoken English: 135-155 words per minute. Other languages vary; use the voice sample to calibrate.
- One beat: 6-25 seconds. If a beat exceeds ~30 seconds, split it.
- Equation beats: 10-20 seconds. Graph beats: 12-25 seconds. Title: 5-10. Recap: 12-20. Outro: 6-12.
- Leave 0.3-0.8 seconds of visual pause between major sections. The runtime's `clear` fade and tail pad provide this.
- Do not narrate every pixel. Narrate the claim; animate the evidence.

## Duration estimate

Before TTS, estimate:

```text
duration ≈ (words / wpm) * 60 + 0.5 * number_of_beats + silent_beats
```

The validator uses the template's `story.words_per_minute` unless the brief overrides it. After TTS, the manifest's exact durations replace the estimate.

## Narrative structures

### Concept explainer (5-8 min)

```text
title -> question -> intuition graph -> definition -> worked example ->
misconception -> recap -> next question
```

### Proof walkthrough (6-12 min)

```text
title -> claim -> why it matters -> definitions -> assumptions ->
step 1 -> crux -> step 2 -> conclusion -> recap -> limits of the result
```

### History / essay (6-10 min)

```text
title -> hook -> historical question -> quote/image -> the idea ->
the obstacle -> the resolution -> why it still matters -> recap
```

### Short (45-90 s)

```text
title/hook -> one visual -> one equation or comparison -> takeaway -> next
```

## Review checklist

- Does the first 10 seconds state the question and promise?
- Does each beat advance the chain, not just decorate it?
- Is the crux given the most time and the clearest visual?
- If a misconception is relevant, is its correction supported and clear?
- Does the recap use the same words as the chain?
- Does the outro ask a real next question?
- Is every graph necessary?
- Are factual claims, quotations, chronology, and any equations checked as appropriate?
- Does the estimated duration match the target?
- Are the spoken forms of symbols and names correct?
