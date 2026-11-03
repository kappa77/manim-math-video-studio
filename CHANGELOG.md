# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[semantic versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
