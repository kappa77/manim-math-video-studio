---
name: manim-math-video
description: Develop any topic into a storyboarded, narrated animated video with subtitles using Manim. Use for planning, researching, scripting, animating, voicing, rendering, or reviewing educational, historical, scientific, technical, cultural, or narrative videos and series.
license: MIT
metadata:
  version: "1.4.1"
  category: video
---

# Animated video studio for any topic

Produce a finished animated video from any theme: clarify its purpose, develop the content, choose a series template, write a beat-by-beat storyboard, generate narration, animate the appropriate visuals, and QA the result. Mathematics is one supported subject, alongside history, science, technology, literature, philosophy, art, practical tutorials, and fictional storytelling.

The identifier `manim-math-video` is retained for existing invocations. It does not restrict the subject. This skill still produces animated videos with Manim; it does not imply support for arbitrary artifact formats or live-action production.

## Adapt to the subject

- Select a structure that serves the topic: explanation, chronology, comparison, procedure, analysis, or narrative. The central question or narrative promise fills `episode.thesis`; the sequence of ideas, events, or steps fills `episode.key_points`.
- For factual topics, distinguish verified facts, interpretations, disputed accounts, and uncertainty. For fiction, preserve internal consistency and label invented material when it could be mistaken for fact. Do not force a thesis to prove, a misconception, or a counterexample into every video.
- Match visuals to the content: timelines and maps for history; diagrams and causal models for science; workflows and state changes for technology; excerpts and relationships for literature; scenes and character arcs for narrative. Use graphs and equations only when they clarify the subject.
- Standard beats include `title`, `section`, `bullets`, `compare`, `quote`, `image`, `recap`, and `outro`. A timeline, map, flowchart, or character animation may need an implemented `custom_beat`; these are not additional built-in beat kinds. Read `references/storyboard.md` for the actual fields.
- Set `episode.rigor` to `explanation`, `narrative`, `procedure`, or `analysis` for general subjects. Keep `intuition`, `sketch`, `proof`, and `derivation` for mathematical treatments. Empty `misconceptions`, `prerequisites`, or `accuracy.notation` lists are valid when irrelevant.

<!-- platform-usage:start -->
## Using this skill in Codex

Requirements: Python 3.10+, Manim Community 0.19+, edge-tts 6+; LaTeX for equation beats; PyAV or ffmpeg for audio conversion. Run `scripts/check_env.py` before rendering. Installing the skill does not install dependencies.

Resolve scripts, assets, and references relative to this `SKILL.md`, even when the working directory is another project. Use absolute paths for briefs and episode directories. Keep generated series and media in the user's workspace, outside the installed skill directory. Ask questions in the user's language; set the narration language separately in the brief.

Before running the pipeline, verify that this directory contains `scripts/`, `references/`, and `assets/`. If it is incomplete, follow `INSTALL.md` in the same directory for personal/project install, update, and uninstall commands.

- **Install:** personal `~/.agents/skills/manim-math-video/` is the current Agent Skills location; Codex desktop builds may use `~/.codex/skills/manim-math-video/` instead. Project skills go in `<repo>/.agents/skills/manim-math-video/`.
- **Invoke:** `$manim-math-video <topic>` or use `/skills`. In the ChatGPT desktop app, type `@` and choose **Manim Video Studio**. Codex can also load the skill implicitly when the description matches the task.
- **Metadata:** `agents/openai.yaml` supplies the display name, short description, and default prompt. Set `policy.allow_implicit_invocation: false` there if the skill should be explicit-invocation only.
- **Workspace:** keep the series and generated media outside the installed skill directory so an update to the skill never touches the user's videos.
<!-- platform-usage:end -->

Reuse decisions and approvals already supplied by the user. An explicit voice choice for the current video satisfies the voice-selection gate; do not ask again. A saved series default alone does not satisfy it for a new episode. The interview and brief approval below apply only to unresolved choices or a brief that has not already been approved.

This skill is deliberately **interview-first**. A theme is not a brief. Before starting production of each new video or episode, always ask the user to choose the narration provider and voice, and wait for their explicit choice. Edge-tts is the default; Cartesia and ElevenLabs are available when `CARTESIA_API_KEY` / `ELEVENLABS_API_KEY` is set. Read the provider guide for Cartesia or ElevenLabs before offering voices; a configured key is not proof that the account may use a particular voice or tier. Offer short playable samples as described in `references/voices.md`. Until that choice is settled, only interview, source research, environment checks, and voice-sample generation may proceed; do not scaffold, write the full script/storyboard, generate episode narration, or render. An existing explicit choice for the current video counts; a generic "ok", "go ahead", or delegated choice does not select an unidentified voice. Do not scaffold or render until the audience, central focus, content progression, visual approach, and four output parameters are settled.

## Non-negotiables

1. **Collect four parameters before production:** video quality, voice (provider + voice), language, and template. Never guess one silently. Voice samples are the explicit exception: generate them before the voice is chosen. Always obtain an explicit voice choice before production; a recommendation or delegated default is not a choice. For other delegated parameters, propose defaults, state them, and record them in `brief.json`.
2. **One coherent focus per episode.** A central question or narrative promise, a clear progression, and a takeaway or resolution. Split overly broad themes into episodes. Include a misconception only when relevant.
3. **Narration is spoken prose, not slide text.** The storyboard's `narration` is what the viewer hears; on-screen text is short. Use `speech` when a symbol or name needs a pronounceable form.
4. **Graphs must earn their place.** Every graph needs a reason to be seen: a limit, a comparison, a counterexample, a rate, an area, a transformation. Write that reason in the beat's `notes`.
5. **Series consistency is a feature.** Reuse the template, voice, language, quality, palette, fonts, title grammar, episode numbering, and intro/outro rhythm. Do not restyle an episode casually.
6. **Draft before final.** Render `draft` (480p15) first, inspect the contact sheet and audio, then render `standard`/`high`. Never burn a long final render on an unvalidated script.
7. **Verify the content.** Check facts, dates, causal claims, quotations, and sources according to the subject. For mathematics, also re-derive formulas and check domains. Label quantitative axes and units. Do not invent evidence or citations.
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
| Cartesia voice requirements and criteria | `references/voices-cartesia.md` |
| ElevenLabs voice requirements and criteria | `references/voices-elevenlabs.md` |
| Storyboard beat grammar and pacing | `references/storyboard.md` |
| Graph specs and animation recipes | `references/graphs.md` |
| Custom Manim code, 3D, camera, equations | `references/manim-recipes.md` |
| Series registry and continuity | `references/series.md` |
| Content verification and domain-specific checks | `references/accuracy.md` |
| Install and failure modes | `references/troubleshooting.md` |

### 1. Interview the argument

Follow `references/interview.md`. Ask in small rounds, at most 8 numbered questions per message. Start with the four required parameters plus the argument core:

- thesis in one sentence;
- audience and prerequisites;
- target duration and platform;
- the crux or tension;
- the visual approach that carries the explanation or story;
- video quality, voice, language, template.

Then develop the explanation, chronology, procedure, or story, probing examples and accuracy as relevant. If the user says "you choose", choose and state defaults for parameters other than voice. For voice, recommend a sample and wait for explicit selection. Reuse series settings, but ask the user to confirm the saved narrator for each new episode unless they have already selected it for that episode.

### 2. Lock the series template

If a series already exists, read its `series.json` and inherit the template, language, and quality. Offer the saved voice as the recommended option, with a short sample, and ask the user to select it or request alternatives before production. Keep that voice locked once confirmed. If the user requests a style change, explain the series-consistency impact and get explicit confirmation.

If this is a new series, choose a template using `references/templates.md`. State the choice and why in one sentence. The template controls palette, fonts, layout, graph styling, motion, caption style, and narrative rhythm.

### 3. Write and validate the brief

Create `brief.json` from `assets/brief.schema.json` and the example at `assets/brief.example.json`. Required sections: `series`, `episode`, `output`, `accuracy`. Record:

- `output.quality`: `draft`, `standard`, `high`, or `4k`;
- `output.language` and `output.voice` (provider, id, model_id when relevant, style, rate, pitch);
- `series.template`;
- thesis, audience, goals, rigor, key points, misconceptions, visuals, target duration;
- terminology or notation, pronunciations, sources, claims to verify; use empty lists for irrelevant fields.

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

Use `references/storyboard.md`. Keep one narration segment per beat and one visual idea per beat. The following is a mathematical example, not a required outline for other topics; adapt the sequence using the subject guidance above:

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

Verify that the user explicitly selected the exact voice, or confirmed reuse of it, for this video. Record the choice before running TTS; do not infer it from general brief approval.

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

1. Central question, learning goal, or narrative promise in one sentence.
2. Audience and prerequisites.
3. Target duration and platform (16:9 long-form, 9:16 short, classroom).
4. The key challenge, turning point, or surprising idea.
5. The visual approach: what should be shown, ordered, compared, or transformed?
6. Quality: draft / standard (1080p30) / high (1080p60) / 4K?
7. Provider, language, and voice: default to edge-tts or use the installed default; confirm the locale; offer three short playable voice samples, then ask for a numbered or named choice before production. If the locale is already known, generate the samples directly.
8. Template: choose from the catalog, or let me recommend one.

If a series exists, reuse its quality, language, and template. Still ask the user to choose the saved narrator for this episode or request alternatives; include a short playable sample. Do not repeat a voice choice already made for the current episode.

## Command cheat sheet

All paths are relative to this skill directory unless noted.

```bash
# environment + asset checks
python scripts/check_env.py
python scripts/selftest.py
python scripts/selftest.py --full   # optional silent smoke render

# comparable voice samples before the voice-selection gate
python scripts/voice_samples.py --language it-IT --style warm-teacher \
  --text "In questa puntata seguiamo un'idea dalla prima domanda al momento in cui tutto si chiarisce."

# validate a brief
python scripts/validate.py --brief brief.json

# scaffold series/episode from a brief
python scripts/new_episode.py --brief brief.json --series-dir series/

# storyboard -> readable script + duration estimate
python scripts/storyboard_to_script.py --episode series/episodes/001-slug

# narration (edge-tts by default)
python scripts/tts.py --episode series/episodes/001-slug
python scripts/tts.py --episode series/episodes/001-slug --list-voices
python scripts/tts.py --episode series/episodes/001-slug --provider cartesia --model sonic-3.6

# render (draft, standard, high, 4k)
python scripts/render.py --episode series/episodes/001-slug --quality draft
python scripts/render.py --episode series/episodes/001-slug --quality standard

# inspect an existing render
python scripts/qa.py --video output/video.mp4 --srt output/video.srt
```

## Decision rules

- **No series yet:** recommend `clean-light` for accessible explainers and procedures, `dark-board` for technical or dramatic treatments, `paper-editorial` for history, culture, and essays. See `references/templates.md`. Treat templates as visual styles; adapt their suggested beat sequence to the topic.
- **User is unsure about voice:** offer three short samples in the narration language, recommend one suited to the topic, and wait for the user to choose. Never silently default the narrator, even after "you choose". See `references/voices.md`.
- **User is unsure about quality:** `standard` = 1080p30 is the default final; `draft` = 480p15 for review; `high` = 1080p60 for motion-heavy work; `4k` only when requested or when the platform needs it.
- **Topic is too big:** split at a natural question boundary; make this episode's thesis narrow; put the rest in the next-episode hook.
- **Graph would be decorative:** replace it with a diagram, equation transformation, or a concrete example. Do not animate a plot that carries no claim.
- **LaTeX is unavailable:** equation beats fail loudly by default. Install LaTeX (see `references/troubleshooting.md`) or set `output.latex_fallback` for a draft-only Unicode approximation. Never ship the fallback as final math.
- **TTS is unavailable:** use `--provider none` only for a silent timing draft; keep the final narrated.
- **A series exists:** inherit its locked settings, but explicitly confirm the narrator for each new episode using the voice-selection gate. Confirming the existing voice is not a style change; changing it still requires explicit approval and a recorded reason.

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
