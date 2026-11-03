# Using Manim Math Video Studio

The skill is written for an agent, but every step is a script you can run yourself. This
guide covers the pipeline, the commands, and what each artifact means. Depth lives in
`manim-math-video/references/` — those files are what the agent reads at runtime.

## Quick start

Run the installer once with `uvx manim-math-video-studio --platform claude` (see
[INSTALL.md](INSTALL.md)); it creates the shared environment and checks it. Then work from
the skill directory: the scripts find that environment on their own.

```bash
cd manim-math-video

# 1. Check the environment (may report an update command)
python scripts/check_env.py

# 2. Scaffold a series and an episode from the example brief
python scripts/new_episode.py --brief assets/brief.example.json --series-dir ../my-series

# 3. Fill the storyboard, or copy the demo storyboard
cp assets/storyboard.example.json ../my-series/episodes/001-why-derivative-x-squared/storyboard.json

# 4. Validate, narrate, render a draft
python scripts/validate.py --episode ../my-series/episodes/001-why-derivative-x-squared
python scripts/storyboard_to_script.py --episode ../my-series/episodes/001-why-derivative-x-squared
python scripts/tts.py --episode ../my-series/episodes/001-why-derivative-x-squared
python scripts/render.py --episode ../my-series/episodes/001-why-derivative-x-squared --quality draft

# 5. Inspect the contact sheet, then render the final
python scripts/render.py --episode ../my-series/episodes/001-why-derivative-x-squared --quality standard
```

## Commands

| Script | Purpose |
|---|---|
| `check_env.py` | Dependency diagnostics: Python, Manim, LaTeX, TTS, PyAV, fonts, assets |
| `validate.py` | Validate a brief, an episode, or a template |
| `new_episode.py` | Scaffold a series and an episode from an approved brief |
| `voice_samples.py` | Generate comparable narration samples before choosing a voice |
| `storyboard_to_script.py` | Human-readable script plus a duration estimate |
| `tts.py` | Narration with edge-tts, Cartesia, ElevenLabs, Piper, a custom command, or silent timing |
| `render.py` | Render with Manim, copy outputs, then run QA |
| `qa.py` | Stream report, audio levels, subtitle coverage, contact sheet |
| `selftest.py` | Asset and runtime checks, optional smoke render |

## How the pipeline works

1. **Interview** — the agent follows `references/interview.md`: the four required parameters (quality, voice, language, template) plus the content core.
2. **Voice selection** — `voice_samples.py` produces numbered, comparable samples; the explicit choice is recorded in `brief.json`.
3. **Brief** — `brief.json` holds the approved thesis, audience, progression, terminology, quality, voice, language, and template.
4. **Scaffold** — `new_episode.py` creates a standalone episode: a copied `manim_lib/`, a `theme.json` snapshot, and a storyboard skeleton.
5. **Storyboard** — `storyboard.json`: one narration segment and one visual idea per beat.
6. **Narration** — `tts.py` writes `voice/*.wav`, `voice/manifest.json`, and a preview SRT; edge-tts word boundaries are captured.
7. **Render** — the generated `episode.py` subclasses `StoryboardScene`, which reads storyboard, theme, and voice manifest, adds sound and captions, and renders the visuals.
8. **QA** — `render.py` copies the MP4/SRT; `qa.py` produces a contact sheet, stream report, audio levels, subtitle coverage, and warnings.

## Beats

`storyboard.json` is a list of beats. The built-in kinds are `title`, `section`, `bullets`,
`compare`, `quote`, `image`, `recap`, and `outro`. Anything else — timelines, maps,
flowcharts, 3D, character animation — is a `custom` beat with your own Manim code, using the
runtime helpers in `assets/project/manim_lib/`. Field-by-field reference:
`references/storyboard.md`; custom code recipes: `references/manim-recipes.md`.

## Templates

| Template | Look | Best for |
|---|---|---|
| `clean-light` | warm off-white, ink, cobalt/amber, precise sans | general explainers, graphs, classroom |
| `dark-board` | deep navy, chalk-bright ink, cyan/violet | calculus, analysis, linear algebra, long-form |
| `paper-editorial` | warm paper, serif, oxblood/olive | history and philosophy of mathematics, essays |

A template locks palette, fonts, layout, graph styling, motion, captions, and narrative
rhythm. Each episode keeps a `theme.json` snapshot, so later catalog changes never restyle
old videos. Details: `references/templates.md`.

## Graphs

The data-driven runtime supports:

- Cartesian plots from safe expressions (`x**2`, `sin(x)/x`, `exp(-x**2)`).
- Parametric curves, data series, and bar charts.
- Vector fields.
- Annotations: points, text, vertical and horizontal lines, tangents, secants, areas, Riemann rectangles, braces, arrows, slope triangles, derivatives.
- Animations: draw, sweep, secant-to-tangent, Riemann refinement, area reveal.
- 3D surfaces through a `custom` beat and `ThreeDScene` (recipe included).

Every graph needs a reason to be seen — a limit, a comparison, a counterexample, a rate, an
area, a transformation. Write that reason in the beat's `notes`. Specs and recipes:
`references/graphs.md`.

## Aspect ratios

`16:9` is the default. `9:16`, `1:1`, and `4:3` are supported with automatic frame sizing;
`render.py` swaps the output dimensions and names the file accordingly. Vertical layouts
stack the `compare` columns. Always review a draft contact sheet for overflow and caption fit.

## Narration

- **edge-tts** (default): many languages, curated voices, style presets, word boundaries.
- **Cartesia**: native adapter, `CARTESIA_API_KEY`, WAV output.
- **ElevenLabs**: native adapter, `ELEVENLABS_API_KEY`, MP3 converted to WAV.
- **Piper**: offline, local model.
- **Custom command**: OpenAI TTS, Azure, or a local model.
- **None**: silently timed draft.

Select a provider at install time with `--tts-provider`, or per episode with
`tts.py --provider cartesia|elevenlabs` and `output.voice.provider` in the brief.
Provider requirements and voice criteria:
[Cartesia](manim-math-video/references/voices-cartesia.md) and
[ElevenLabs](manim-math-video/references/voices-elevenlabs.md).

Language and voice are independent of the template. Subtitles can be translated per beat with
the `caption` field. Voice catalog, pronunciation notes: `references/voices.md`.

## Series consistency

`series.json` locks template, quality, language, voice, title grammar, and narrative rhythm.
`new_episode.py` refuses style drift unless `--allow-style-drift "reason"` is passed, and the
reason is recorded. See `references/series.md`.

## Validation

```bash
python scripts/validate.py --brief brief.json
python scripts/validate.py --episode path/to/episode
python scripts/validate.py --template assets/templates/dark-board.json
```

Validation checks required fields, template existence, quality, voice and locale
compatibility, beat IDs, graph expressions, annotation types, equation and LaTeX
availability, duration drift, and the voice manifest.

## Verified demo

`manim-math-video/examples/demo-series` is a complete 3-minute episode on the derivative of
x² — scaffolded, narrated with edge-tts, rendered at 480p15, and QA'd. See
`manim-math-video/examples/README.md`.

## Where to read more

| Need | Read |
|---|---|
| Workflow rules and routing | `manim-math-video/SKILL.md` |
| Beat grammar, pacing | `references/storyboard.md` |
| Graph specs and annotations | `references/graphs.md` |
| Custom Manim code, 3D, camera | `references/manim-recipes.md` |
| Voices, languages, pronunciation | `references/voices.md` |
| Templates, series catalog | `references/templates.md`, `references/series.md` |
| Verification checklist | `references/accuracy.md`, `references/accuracy-math.md` |
| Failures and fixes | `references/troubleshooting.md` |
