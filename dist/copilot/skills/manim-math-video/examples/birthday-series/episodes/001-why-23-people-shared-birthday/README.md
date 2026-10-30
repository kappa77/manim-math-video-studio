# Path of Knowledge — Why 23 people are enough for a shared birthday

Episode `s01e001` of **Path of Knowledge**. This is the episode used as the README and
landing-page demo, and the second verified example in this directory.

| Setting | Value |
|---|---|
| Template | `clean-light` |
| Quality | `standard` (1080p30) |
| Language | `en-US` |
| Voice | `en-US-AvaMultilingualNeural` (`warm-teacher`, `-3%`) |
| Target duration | 140 s |
| Rendered duration | 144.2 s (video), 135.7 s narration |

## What it demonstrates

- **A data graph that carries the argument.** The probability curve is supplied as exact
  points (`graph.type: "data"`), with point annotations at 23 people (50.7%) and 57 people
  (99.0%) — the two numbers the narration asks the viewer to remember.
- **An equation used as an explanation, not decoration.** The complement product appears
  after the curve, so the formula answers a question the viewer already has.
- **A `compare` beat for the misconception.** Intuition (23 people against 365 days) sits
  next to the count (253 pairs), instead of being debunked in prose.
- **Nine beats, ~2.5 minutes.** The shortest complete episode in the repository, useful as a
  template for single-idea videos.
- **Pacing that slows at the end.** The last three beats carry `hold` values (0.6 s, 1.6 s,
  2.4 s) so the comparison, the recap list, and the closing question stay on screen after the
  narration stops — the frames a viewer needs to read rather than hear.

## Files

- `brief.json` — approved inputs, including the verified claims and their values.
- `storyboard.json` — beat-by-beat script, graph spec, and visual notes.
- `script.md` — human-readable narration script.
- `episode.py` — Manim scene; renders the storyboard.
- `theme.json` — template snapshot.
- `manim_lib/` — standalone runtime.

Rendered narration, video, and the media cache are not committed.

## Verified output

- 1920x1080, 30 fps, 144.2 s, 5.6 MB
- AAC narration present; peak -4.6 dB, RMS -23.1 dB
- 34 subtitle cues, 94% coverage
- QA: no failures, no warnings
- Numbers recomputed during production, not quoted: `P(23) = 0.507297`,
  `P(57) = 0.990122`, `23 x 22 / 2 = 253`, `23 / 365 = 0.063`

## Commands

From the `manim-math-video/` skill directory:

```bash
EP=examples/birthday-series/episodes/001-why-23-people-shared-birthday

python scripts/validate.py --episode "$EP"
python scripts/storyboard_to_script.py --episode "$EP"
python scripts/tts.py --episode "$EP"
python scripts/render.py --episode "$EP" --quality draft      # 480p15, ~15 s
python scripts/render.py --episode "$EP" --quality standard   # 1080p30, ~90 s
```

Always use `render.py` for non-16:9 episodes so the pixel dimensions match the frame aspect
ratio.

## Notes

- The video runs about 8 s longer than the narration: each beat's transition adds ~0.4 s and the
  three closing beats add `hold` time. Per-beat audio is anchored to its own visual start, so sync
  holds throughout.
- Re-rendering after an on-screen edit needs `--no-cache`, or Manim reuses cached partial movies and
  the narration drops out of the reused segments. Editing narration text alone is safe.
- Keep the series voice, language, quality, and template unless the series is deliberately
  restyled.
- For a custom visual, add a `kind: "custom"` beat and override `custom_beat` in
  `episode.py`.
