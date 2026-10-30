# Path of Knowledge — Why the derivative of x² is 2x

Episode `s01e001` of **Path of Knowledge**.

| Setting | Value |
|---|---|
| Template | `clean-light` |
| Quality | `standard` |
| Language | `en-US` |
| Voice | `en-US-AvaMultilingualNeural` (warm-teacher) |
| Target duration | 180 s |

## Files

- `brief.json` — approved inputs.
- `storyboard.json` — beat-by-beat script and visual specs.
- `script.md` — human-readable narration script.
- `episode.py` — Manim scene; renders the storyboard.
- `theme.json` — template snapshot.
- `manim_lib/` — standalone runtime.
- `voice/` — narration audio and manifest.
- `output/` — final MP4 and SRT.
- `qa/` — contact sheet and reports.

## Commands

```bash
# From the skill directory:
python scripts/validate.py --episode "C:\source\path-of-knowledge\manim-math-video\examples\demo-series\episodes\001-why-derivative-x-squared"
python scripts/storyboard_to_script.py --episode "C:\source\path-of-knowledge\manim-math-video\examples\demo-series\episodes\001-why-derivative-x-squared"
python scripts/tts.py --episode "C:\source\path-of-knowledge\manim-math-video\examples\demo-series\episodes\001-why-derivative-x-squared"
python scripts/render.py --episode "C:\source\path-of-knowledge\manim-math-video\examples\demo-series\episodes\001-why-derivative-x-squared" --quality draft
python scripts/render.py --episode "C:\source\path-of-knowledge\manim-math-video\examples\demo-series\episodes\001-why-derivative-x-squared" --quality standard
```

## Notes

- Fill every `TODO` in `storyboard.json` before rendering.
- Keep the series voice, language, quality, and template unless the series is deliberately restyled.
- The runtime adds captions from the narration. Use `caption` for translated or reformatted subtitles.
- For a custom visual, add a `kind: "custom"` beat and override `custom_beat` in `episode.py`.
