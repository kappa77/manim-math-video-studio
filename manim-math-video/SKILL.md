---
name: manim-math-video
description: Turn a math theme into a storyboarded, narrated Manim video with graphs and subtitles, and keep a consistent series template. Use when planning, scripting, animating, voicing, rendering, or QA-ing a mathematical explainer video, episode, or video series.
license: MIT
compatibility: Python 3.10+, Manim Community 0.19+, edge-tts 6+; LaTeX for equation beats; PyAV or ffmpeg for audio conversion.
metadata:
  version: "1.0.0"
  category: video
---

# Manim math video studio

Produce a finished math explainer from a theme: interrogate the argument, lock the output parameters, choose a series template, write a beat-by-beat storyboard, generate narration, render graphs and equations, and QA the result.

This skill is deliberately **interview-first**. A theme is not a brief. Do not scaffold or render until the viewer, the thesis, the argument chain, the visual evidence, and the four output parameters are settled.

## Non-negotiables

1. **Collect four parameters before generating anything:** video quality, voice, language, and template. Never guess one silently. If the user delegates, propose a default, state it, and record it in `brief.json`.
2. **One argument per episode.** A thesis, a chain of 3-7 claims, one crux, one misconception, one takeaway. Split anything larger into episodes.
3. **Narration is spoken prose, not slide text.** The storyboard's `narration` is what the viewer hears; on-screen text is short. Use `speech` when a symbol or name needs a pronounceable form.
4. **Graphs must earn their place.** Every graph needs a reason to be seen: a limit, a comparison, a counterexample, a rate, an area, a transformation. Write that reason in the beat's `notes`.
5. **Series consistency is a feature.** Reuse the template, voice, language, quality, palette, fonts, title grammar, episode numbering, and intro/outro rhythm. Do not restyle an episode casually.
6. **Draft before final.** Render `draft` (480p15) first, inspect the contact sheet and audio, then render `standard`/`high`. Never burn a long final render on an unvalidated script.
7. **Verify the mathematics.** Re-derive every nontrivial formula, check domains and edge cases, and label axes and units. Do not invent citations or historical claims.
8. **Accessibility by default.** Keep captions, high contrast, large type, and redundant color/shape cues. Captions are generated from the narration unless explicitly disabled.

## Workflow

### 0. Load the right references

Read only what the current step needs:

| Need | Read |
|---|---|
| How to interview the user | `references/interview.md` |
| Brief fields, quality presets, defaults | `references/brief.md` |
| Template catalog and series consistency | `references/templates.md` |
| Voice/language selection and pronunciation | `references/voices.md` |
| Storyboard beat grammar and pacing | `references/storyboard.md` |
| Graph specs and animation recipes | `references/graphs.md` |
| Custom Manim code, 3D, camera, equations | `references/manim-recipes.md` |
| Series registry and continuity | `references/series.md` |
| Math verification and notation | `references/accuracy.md` |
| Install and failure modes | `references/troubleshooting.md` |

### 1. Interview the argument

Follow `references/interview.md`. Ask in small rounds, at most 8 numbered questions per message. Start with the four required parameters plus the argument core:

- thesis in one sentence;
- audience and prerequisites;
- target duration and platform;
- the crux or tension;
- the one visual that carries the intuition;
- video quality, voice, language, template.

Then probe the argument chain, misconceptions, examples, and accuracy. If the user says "you choose", choose and say what you chose. Do not ask questions whose answer is already in the series registry.

### 2. Lock the series template

If a series already exists, read its `series.json` and inherit the template, voice, language, and quality. Ask only for episode-specific content. If the user requests a style change, warn that it breaks the series and get explicit confirmation.

If this is a new series, choose a template using `references/templates.md`. State the choice and why in one sentence. The template controls palette, fonts, layout, graph styling, motion, caption style, and narrative rhythm.

### 3. Write and validate the brief

Create `brief.json` from `assets/brief.schema.json` and the example at `assets/brief.example.json`. Required sections: `series`, `episode`, `output`, `accuracy`. Record:

- `output.quality`: `draft`, `standard`, `high`, or `4k`;
- `output.language` and `output.voice` (provider, id, style, rate, pitch);
- `series.template`;
- thesis, audience, goals, rigor, key points, misconceptions, visuals, target duration;
- notation, pronunciations, sources, claims to verify.

Run:

```bash
python scripts/validate.py --brief <path/to/brief.json>
```

Present a compact confirmation block: thesis, audience, duration, template, quality, voice, language, beat outline, and what the viewer will see. **Wait for approval.**

### 4. Scaffold the episode

```bash
python scripts/new_episode.py --brief <brief.json> --series-dir <series-root>
```

This creates a series registry (first run), an episode directory, a theme snapshot, a standalone `manim_lib/`, a storyboard skeleton, a script template, and the `Episode` scene. It refuses to silently drift from an existing series.

### 5. Write the script and storyboard

Use `references/storyboard.md`. Keep one narration segment per beat and one visual idea per beat. Typical 5-9 minute episode:

1. `title` — hook and promise.
2. `section`/`bullets` — the question and why it matters.
3. `graph` or `equation` — intuition.
4. `equation`/`section` — formal statement.
5. `graph` or `equation` — worked example.
6. `compare` — misconception and correction.
7. `recap` — the chain in 3-4 lines.
8. `outro` — next question and series continuity.

Write `storyboard.json`; use `narration` for the voice track and `caption` for translated or differently formatted subtitles. Then:

```bash
python scripts/storyboard_to_script.py --episode <episode-dir>
python scripts/validate.py --episode <episode-dir>
```

Check the estimated duration against the target. Cut, don't rush. Target roughly 135-155 spoken words per minute.

### 6. Generate narration

```bash
python scripts/tts.py --episode <episode-dir>
```

This produces `voice/*.wav`, `voice/manifest.json`, and a preview `voice/captions.srt`. Listen to at least the first, middle, and last segments. Check pronunciation, pacing, and segment durations. If a word is wrong, add it to `accuracy.pronunciations` or add a `speech` form to that beat and rerun with `--only <beat-id>` (or `--force` for every segment).

Do not proceed if the audio and storyboard disagree about content.

### 7. Render a draft and QA

```bash
python scripts/render.py --episode <episode-dir> --quality draft
```

Review:

- `qa/contact_sheet.jpg` for layout, overflow, and contrast;
- `output/*.srt` for caption coverage;
- `qa/report.md` for stream, duration, loudness, and subtitle warnings;
- the full draft at 1x speed for pacing and sync.

Fix the storyboard or `custom_beat` code, rerun `tts.py` only if narration changed, and rerun the draft. Use Manim caching while iterating.

### 8. Render the final

```bash
python scripts/render.py --episode <episode-dir> --quality standard
```

Use the brief's quality unless the user explicitly asks for a different final. The renderer:

- checks the environment and TTS manifest;
- renders the `Episode` scene at the requested resolution/fps;
- copies the MP4 and SRT to `output/`;
- writes `qa/report.json` and `qa/report.md`;
- names the file deterministically, e.g. `s01e001-why-derivative-is-2x-1080p30.mp4`.

### 9. Deliver

Report the output paths, duration, quality, voice/language, template, and any warnings. Include the editable `brief.json`, `storyboard.json`, `script.md`, and scene code. If this is part of a series, update the episode registry and state the next episode hook.

## First response behavior

When the user gives only a theme, reply with a short framing and **one** round of numbered questions. Do not dump the entire question bank. A good first round is:

1. One-sentence thesis — what should the viewer believe or be able to do?
2. Audience and prerequisites.
3. Target duration and platform (16:9 long-form, 9:16 short, classroom).
4. The crux: what is surprising, hard, or commonly misunderstood?
5. The visual evidence: what should be plotted or transformed?
6. Quality: draft / standard (1080p30) / high (1080p60) / 4K?
7. Voice and language: choose a style and locale, or describe the voice you want.
8. Template: choose from the catalog, or let me recommend one.

If a series exists, replace 6-8 with "reuse series settings?" and ask only for the episode title/thesis.

## Command cheat sheet

All paths are relative to this skill directory unless noted.

```bash
# environment + asset checks
python scripts/check_env.py
python scripts/selftest.py
python scripts/selftest.py --full   # optional silent smoke render

# validate a brief
python scripts/validate.py --brief brief.json

# scaffold series/episode from a brief
python scripts/new_episode.py --brief brief.json --series-dir series/

# storyboard -> readable script + duration estimate
python scripts/storyboard_to_script.py --episode series/episodes/001-slug

# narration (edge-tts by default)
python scripts/tts.py --episode series/episodes/001-slug
python scripts/tts.py --episode series/episodes/001-slug --list-voices

# render (draft, standard, high, 4k)
python scripts/render.py --episode series/episodes/001-slug --quality draft
python scripts/render.py --episode series/episodes/001-slug --quality standard

# inspect an existing render
python scripts/qa.py --video output/video.mp4 --srt output/video.srt
```

## Decision rules

- **No series yet:** recommend `clean-light` for general audiences and graphs, `dark-board` for calculus/linear algebra/long-form, `paper-editorial` for history/philosophy/essayistic episodes. See `references/templates.md`.
- **User is unsure about voice:** default to a warm teacher style in the narration language. State the exact voice id.
- **User is unsure about quality:** `standard` = 1080p30 is the default final; `draft` = 480p15 for review; `high` = 1080p60 for motion-heavy work; `4k` only when requested or when the platform needs it.
- **Topic is too big:** split at a natural question boundary; make this episode's thesis narrow; put the rest in the next-episode hook.
- **Graph would be decorative:** replace it with a diagram, equation transformation, or a concrete example. Do not animate a plot that carries no claim.
- **LaTeX is unavailable:** equation beats fail loudly by default. Install LaTeX (see `references/troubleshooting.md`) or set `output.latex_fallback` for a draft-only Unicode approximation. Never ship the fallback as final math.
- **TTS is unavailable:** use `--provider none` only for a silent timing draft; keep the final narrated.
- **A series exists:** inherit its locked settings. Do not change template, voice, language, or quality without explicit user confirmation and a recorded reason.

## Deliverables

A completed episode contains:

```text
episodes/001-slug/
  brief.json            # approved inputs and series lock
  storyboard.json       # machine-readable beats
  script.md             # human-readable narration/visual script
  episode.py            # Manim scene (data-driven, editable)
  theme.json            # template snapshot
  manim_lib/            # standalone runtime
  voice/
    manifest.json       # segment durations, audio paths, captions
    *.wav               # narration used by Manim
    captions.srt        # preview subtitles
  output/
    s01e001-slug-1080p30.mp4
    s01e001-slug.srt
  qa/
    contact_sheet.jpg
    report.md
    report.json
```

## Editing generated scenes

The default `episode.py` renders the whole storyboard. For a visual that the data-driven beat types cannot express, add a `kind: "custom"` beat and override `custom_beat` in `episode.py`:

```python
from manim_lib.runtime import StoryboardScene

class Episode(StoryboardScene):
    def custom_beat(self, beat, vo):
        # vo.duration, vo.remaining, vo.elapsed are available
        ...
```

Keep custom code inside the voiceover budget so audio and visuals stay aligned. See `references/manim-recipes.md`.
