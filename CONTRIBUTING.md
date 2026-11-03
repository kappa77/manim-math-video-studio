# Contributing

Thanks for looking. This repository is an **Agent Skill**: prose that an agent reads, plus the scripts it runs. Both halves matter.

## Repository layout

```text
manim-math-video/                 # canonical skill — the source of truth
├── SKILL.md                      # routing + workflow the agent follows
├── references/                   # interview, brief, storyboard, graphs, voices, series, accuracy
├── assets/                       # templates, voices.json, schemas, project/manim_lib runtime
├── scripts/                      # check_env, validate, new_episode, tts, render, qa, selftest
└── examples/                     # verified demo series source + preview contact sheet

platforms/                        # per-agent frontmatter and install notes
├── manifest.json                 # platform config: install roots, frontmatter edits
├── build.py                      # build / --check / --install the dist/ trees
└── claude/  codex/  copilot/  pi/

dist/                             # GENERATED skill trees, one per agent — do not edit
install.py                        # installer: detection, skill trees, shared environment
install.sh / install.ps1          # one-command wrappers for macOS/Linux and Windows
pyproject.toml                    # thin PyPI package: console scripts, no skill trees
manim_math_video_studio/          # package shim used by the console scripts
scripts/check_env.py              # repo-root wrapper for the skill environment check
scripts/setup.py                  # repo-only helper: create ./.venv and install requirements
tests/                            # installer + simulated-harness verification
  install_matrix.py               # stdlib-only fast suite and real runtime suite
  tts_providers_smoke.py          # Cartesia/ElevenLabs adapters against a local mock
  docker/                         # Dockerfile and matrix runner
  README.md                       # what each test proves, how to add a harness
docs/                             # GitHub Pages landing page
```

| Path | Role |
|---|---|
| `manim-math-video/` | **Source of truth.** `SKILL.md`, `references/`, `assets/`, `scripts/` |
| `platforms/<agent>/` | Frontmatter variants and per-agent `README.md` / `INSTALL.md` |
| `dist/<agent>/skills/manim-math-video/` | **Generated.** Never edit by hand |
| `install.py`, `install.sh`, `install.ps1` | Installer (stdlib-only Python, plus thin wrappers) |
| `pyproject.toml`, `manim_math_video_studio/` | Thin PyPI package and console-script entry point |
| `tests/` | Installer and harness simulation suite, plus the Docker matrix |
| `docs/` | Landing page published with GitHub Pages |

## Workflow

```bash
python platforms/build.py          # regenerate every dist/ tree
python platforms/build.py --check  # fail if dist/ is stale — run this before a PR
python manim-math-video/scripts/selftest.py
python manim-math-video/scripts/check_env.py
python tests/install_matrix.py --scope fast
```

A change to `manim-math-video/` without rebuilding `dist/` will fail CI-style review, because the generated trees drift. If you only edit `platforms/<agent>/`, rebuild too: the per-platform `README.md` and `INSTALL.md` are copied into `dist/`.

## Installer and harness tests

`tests/install_matrix.py` runs the installer end to end against a simulated
copy of every harness. The fast scope needs only the standard library: it
creates throwaway `HOME` directories, plants the configuration folders and CLI
names each agent uses, then checks install roots, frontmatter, the platform
usage section, state, updates, and uninstall.

```bash
python tests/install_matrix.py --scope fast        # any Python 3.10+, no deps
python tests/install_matrix.py --scope runtime     # real venv + requirements
python tests/install_matrix.py --scope runtime --render
```

The runtime scope creates the shared environment, installs `requirements.txt`,
runs `check_env.py` and `selftest.py` from every installed harness, and can run
a silent Manim render. Docker is the clean, reproducible way to run both:

```bash
tests/docker/run.sh                              # Python 3.10-3.13 + Alpine
tests/docker/run.sh --scope runtime --render     # dependencies + smoke render
tests/docker/run.sh --scope all                  # everything
```

The fast matrix runs `platforms/build.py --check` at image build time, so stale
generated trees fail before tests start. See `tests/README.md` for the checks,
the harness contract, and how to add a platform.

## What belongs where

- **A new reference document** → `manim-math-video/references/<topic>.md`, then link it from `SKILL.md` where the agent must read it. Say *when* to read it; unexplained links do not load.
- **A new beat kind** → implement it in `assets/project/manim_lib/`, document it in `references/storyboard.md`, add it to `assets/storyboard.schema.json`, and mention it in `SKILL.md`'s beat list.
- **A new template** → `assets/templates/<name>.json`, a row in `references/templates.md`, and the selection table in `SKILL.md`.
- **A script flag** → keep the CLI self-documenting (`--help`), and update the command in `SKILL.md`.

## Guidelines

- `SKILL.md` stays lean: procedures and routing, not tutorials. Detail goes in `references/`.
- Prefer explicit, checkable instructions over adjectives. "Ask for the audience before the thesis" beats "be thoughtful".
- Every claim about a tool's behaviour should be true for the version pinned in `requirements.txt`.
- ASCII in scripts; Markdown in prose. Wrap at ~100 columns.
- No emoji in skill files. Emoji in the landing page are not required either.

## Versioning

1. Bump `VERSION` (repo release, e.g. `0.4.0`); it also drives the PyPI package version.
2. Bump `metadata.version` in `manim-math-video/SKILL.md` (skill version, e.g. `1.3.2`).
3. Add a `CHANGELOG.md` entry.
4. Rebuild `dist/`, run package checks, then tag `vX.Y.Z`.

## Installer changes

The installer must stay dependency-free until it has created its own environment:

```bash
python install.py --dry-run                 # plan only
python install.py --uninstall --dry-run     # never removes what it did not create
python -c "import urllib.request as u;exec(u.urlopen('file:///.../install.py').read().decode())" --dry-run
```

That last form exercises the `python -c` path, where `__file__` does not exist.

Installer behaviour has its own suite; run it before changing detection,
copying, state, or uninstall logic:

```bash
python tests/install_matrix.py --scope fast
tests/docker/run.sh
```

Set `MMS_ARCHIVE_URL` to a local archive (`file:///...`) to test the download
path without touching GitHub; the one-liner test in `tests/install_matrix.py`
does exactly that.

## Python package and PyPI

The package is deliberately **thin**: the wheel contains `install.py`, the
`manim_math_video_studio` shim, and metadata. It does not contain `dist/`; at
runtime it downloads the release tag matching its own version. Keep `dist/` for
the generated skill trees and build packages into `release-dist/`:

```bash
python -m build --outdir release-dist
python -m twine check release-dist/*
```

Run the package checks before a release; CI also does this on every push:

```bash
python -m venv /tmp/pkg-venv
/tmp/pkg-venv/bin/pip install release-dist/*.whl
/tmp/pkg-venv/bin/manim-math-video-studio --version
```

Releases are tagged. The `pypi-publish.yml` workflow checks that the tag equals
`v$(cat VERSION)`, builds the wheel and sdist, and publishes with PyPI trusted
publishing (no API token).

One-time PyPI setup:

1. Create the project `manim-math-video-studio` on PyPI and enable 2FA.
2. Add a **pending trusted publisher** with:
   - owner `kappa77`
   - repository `manim-math-video-studio`
   - workflow `pypi-publish.yml`
   - environment `pypi`
3. In GitHub, create the `pypi` environment under Settings → Environments.
4. Push a version tag (`v0.7.1`); the workflow publishes the wheel and sdist.

For a dry run, use TestPyPI or build and install the wheel locally instead of
tagging a release.

## Pull requests

- One topic per PR.
- Describe the user-visible effect, not the diff.
- Include the `--check` output and, for rendering changes, a contact sheet or a short clip.
- Say which agent and platform you tested with.

## Reporting problems

Use the issue templates. For rendering failures, include `scripts/check_env.py` output (it names the actual interpreter and Manim version), the command you ran, and the full traceback. `references/troubleshooting.md` already covers the common cases.
