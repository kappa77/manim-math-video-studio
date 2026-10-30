# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] — 2026-10-30

### Added

- **`hold` on any beat.** Extra seconds a beat stays on screen after its narration ends, for recaps,
  conclusions, and frames that need reading time. The only previous lever was longer narration.
- **`--ref` / `MMS_REF`** pin a release from the one-liner (`--ref v0.2.0`); `MMS_ARGS` passes flags
  when a shell mangles trailing arguments.
- **Landing page** in `docs/`, published with GitHub Pages: hero GIF, copy-paste install, per-agent
  table. README gained badges and the same hero.
- **`USAGE.md`**: quick start, command reference, pipeline, beats, templates, graphs, aspect ratios,
  narration, series consistency, validation. The README now carries the essentials only.
- **`CONTRIBUTING.md`**, **`CHANGELOG.md`**, and issue templates for bug reports and feature requests.
- **A generated demo episode**, *Why 23 people are enough for a shared birthday* — 9 beats, 1080p30,
  subtitle SRT, and a `data`-graph beat built from exact probabilities. Published as a release asset
  and in the repository as `examples/birthday-series` (source, no media).

### Changed

- The demo's closing beats were too quick to read: narration expanded, and the comparison, recap and
  outro now carry `hold` time (118 s → 144 s total).
- `manim-math-video/SKILL.md` version is now `1.3.0`.

### Fixed

- **Silent renders after a re-render.** Reusing Manim's cached partial movies could drop the per-beat
  sound, producing a video that looked correct but had long silent stretches. Documented in
  `references/troubleshooting.md` with the `--no-cache` remedy.

## [0.1.0] — first public release

### Added

- **Agent Skill** that turns a topic into a storyboarded, narrated Manim video and into a
  consistent series, with prebuilt trees for Claude Code, Codex, GitHub Copilot, and Pi.
- **Interview-first workflow**: content, audience, crux, visual approach, and takeaway are
  settled before scaffolding; quality, voice, language, and template are locked as the four
  production parameters.
- **Beat grammar**: `title`, `section`, `bullets`, `compare`, `quote`, `image`, `recap`,
  `outro`, plus a custom-beat hook, graph specs, equations, camera and 3D recipes.
- **Narration pipeline**: edge-tts, Piper, or a custom command; per-beat durations; SRT and
  VTT output; per-language pronunciation notes.
- **Series registry** so template, palette, typography, and narration identity stay stable
  across episodes.
- **Validation and QA**: JSON schemas for the brief and storyboard, `check_env.py`,
  contact-sheet generation, and a self-test.
- **One-command installer** working identically on macOS, Linux, and Windows:
  `install.py`, plus `install.sh` and `install.ps1` wrappers. Detects installed agents,
  prepares a single shared environment at `~/.manim-math-video/venv`, verifies it, and
  records state for `--uninstall`. Uses `uv` when available.
- **Runtime resolution**: scripts find `MANIM_BIN`, `MANIM_STUDIO_VENV`, the environment
  recorded in `<skill>/.venv-path`, `~/.manim-math-video/venv`, a local `.venv`, or `PATH`,
  and re-exec into the shared environment when the starting interpreter lacks dependencies.
- **Three templates**: `clean-light`, `dark-board`, `paper-editorial`.
- **Docs**: `INSTALL.md` (options, layout, update, uninstall, troubleshooting),
  `CONTRIBUTING.md`, a demo series under `manim-math-video/examples/`, and a landing page in
  `docs/`.
- **Release assets**: per-platform zips plus an all-in-one archive that mirrors `dist/`.

### Known gaps

- No rendered demo video in the repository yet; the README shows a contact sheet.
- `--with-latex` automates MiKTeX (Windows) and BasicTeX (macOS) only; Linux instructions are
  printed rather than executed.

[0.1.0]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.1.0
[0.2.0]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.2.0
