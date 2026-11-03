# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.1] — 2026-11-03

### Changed

- The PyPI publish workflow now also creates a GitHub Release from the pushed
  tag, so tags and releases no longer drift. Existing missing releases were
  created retroactively.

## [0.7.0] — 2026-11-03

### Added

- **Periodic update check.** `scripts/check_env.py` compares the installed
  release in `~/.manim-math-video/install.json` with PyPI at most once every
  24 hours (cached in `~/.manim-math-video/update-check.json`) and prints the
  latest version plus a matching `uvx manim-math-video-studio --platform ...`
  command. Offline checks are silent. `MANIM_STUDIO_NO_UPDATE_CHECK=1` disables
  it; `MANIM_STUDIO_UPDATE_URL` overrides the endpoint. No keys are sent.

### Changed

- `manim-math-video/SKILL.md` version is now `1.6.0`.
- README and INSTALL explain the update check and opt-out.

## [0.6.0] — 2026-11-03

### Added

- **Installer default voice.** `install.py --tts-voice <id>` stores a default
  provider voice in `~/.manim-math-video/tts.json` without storing API keys.
  The conversation can still override it per series or episode.

### Changed

- Split Cartesia and ElevenLabs voice requirements/criteria into dedicated
  `references/voices-cartesia.md` and `references/voices-elevenlabs.md` guides.
- `--list-voices` now shows `Access` and `Languages`; native-provider errors
  point to the provider guide; display names are rejected where a provider voice
  id is required.
- The ElevenLabs guide now explains how to create an owned voice with Voice
  Design (free), Instant Voice Cloning (Starter), or Professional Voice Cloning
  (Creator), and how to verify `Access: own` before selecting it.
- README and landing page link the provider-specific voice guides.
- `manim-math-video/SKILL.md` version is now `1.5.0`.

## [0.5.1] — 2026-11-03

### Fixed

- **Cartesia streaming WAV durations.** Cartesia returns WAV files with a
  streaming RIFF header (`0xFFFFFFFF` sizes); the wave module read them as
  ~48,695 seconds per segment. `wav_duration()` now reads the real duration via
  PyAV and falls back to a file-size sanity check. Added a regression in the
  native TTS smoke test.
- `manim-math-video/SKILL.md` version is now `1.4.1`.

## [0.5.0] — 2026-11-03

### Added

- **Native Cartesia and ElevenLabs narration.** Select `cartesia` or
  `elevenlabs` with `install.py --tts-provider`, `tts.py --provider`, or
  `output.voice.provider` in the brief. API keys stay in `CARTESIA_API_KEY` /
  `ELEVENLABS_API_KEY`; `~/.manim-math-video/tts.json` stores only the provider
  and model. Voice listing, samples, manifest metadata, and `check_env.py`
  diagnostics are included.

### Changed

- README, INSTALL, USAGE, and the landing page now lead with the `uvx`/PyPI
  install and keep the long fallback routes collapsed. The landing page lists
  the explicit per-agent commands.
- The landing page follows the system light/dark preference, uses AA text
  contrast, stacks the install table on small screens, and shows the page
  version and date in the footer.
- Refreshed the birthday demo: verified the four numerical claims, rerendered
  1080p with no QA warnings, replaced the GIF with a title-led sequence, and
  attached the MP4/SRT to the v0.4.0 GitHub release.
- `manim-math-video/SKILL.md` version is now `1.4.0`.

## [0.4.0] — 2026-11-03

### Added

- **Standard Python package.** `pyproject.toml`, a `manim_math_video_studio`
  entry point, and `manim-math-video-studio` / `manim-math-video-install`
  console scripts. The thin wheel contains only the installer; it downloads the
  release tag matching its own version and keeps the skill trees out of the
  package. Ready for `uvx` and `pipx` after the PyPI release.
- **PyPI publishing workflow.** Trusted publishing on `v*` tags, with a build
  and artifact upload step shared by the package checks.

### Changed

- `install.py` gains `--version`. When installed from a wheel it defaults to the
  release tag matching the package version instead of `main`, and the console
  script reports its own name in `--help`.

## [0.3.2] — 2026-11-01

### Fixed

- `install.py --uninstall` now normalizes symlinked HOME paths before deciding
  whether it owns the shared environment. This fixes the venv being left behind
  on macOS temp paths and Windows short paths. The native Windows/macOS CI jobs
  caught it.

## [0.3.1] — 2026-11-01

### Changed

- `check_env.py` now prints OS-specific install commands when `LaTeX` or
  `dvisvgm` is missing.
- `manim-math-video/SKILL.md` version is now `1.3.2`.

## [0.3.0] — 2026-11-01

### Added

- **Docker-based install verification.** `tests/install_matrix.py` simulates the
  Claude Code, Codex, GitHub Copilot, and Pi skill roots in throwaway HOME
  directories, then checks detection, personal and project installs, frontmatter,
  state, reinstall, uninstall, the shell wrapper, and the download path. The
  runtime scope builds the shared environment, installs `requirements.txt`, and
  runs `check_env.py`, re-exec, and `selftest.py` for every harness, plus an
  optional Manim smoke render from one installed copy.
- **A test image and matrix runner.** `tests/docker/run.sh` covers Python
  3.10-3.13 on Debian and Python 3.12 on Alpine; `--scope runtime --render`
  verifies real rendering. GitHub Actions runs the matrix, plus native
  Windows/macOS fast jobs.
- **`MMS_ARCHIVE_URL`** overrides the installer download for mirrors and offline
  tests (including `file://` archives); the one-liner test uses it.

### Fixed

- **Linux/macOS runtime re-exec.** `ensure_runtime()` compared resolved paths, so
  a venv's `bin/python` symlink looked like the base interpreter and the switch
  to `~/.manim-math-video/venv` never happened. It now compares absolute paths
  without following the symlink. The runtime test matrix caught this.

### Changed

- `manim-math-video/SKILL.md` version is now `1.3.1`.

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
[0.3.0]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.3.0
[0.3.1]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.3.1
[0.3.2]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.3.2
[0.4.0]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.4.0
[0.5.0]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.5.0
[0.5.1]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.5.1
[0.6.0]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.6.0
[0.7.0]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.7.0
[0.7.1]: https://github.com/kappa77/manim-math-video-studio/releases/tag/v0.7.1
