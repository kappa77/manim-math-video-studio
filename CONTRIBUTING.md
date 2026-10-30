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
scripts/check_env.py              # repo-root wrapper for the skill environment check
scripts/setup.py                  # repo-only helper: create ./.venv and install requirements
docs/                             # GitHub Pages landing page
```

| Path | Role |
|---|---|
| `manim-math-video/` | **Source of truth.** `SKILL.md`, `references/`, `assets/`, `scripts/` |
| `platforms/<agent>/` | Frontmatter variants and per-agent `README.md` / `INSTALL.md` |
| `dist/<agent>/skills/manim-math-video/` | **Generated.** Never edit by hand |
| `install.py`, `install.sh`, `install.ps1` | Installer (stdlib-only Python, plus thin wrappers) |
| `docs/` | Landing page published with GitHub Pages |

## Workflow

```bash
python platforms/build.py          # regenerate every dist/ tree
python platforms/build.py --check  # fail if dist/ is stale — run this before a PR
python manim-math-video/scripts/selftest.py
python manim-math-video/scripts/check_env.py
```

A change to `manim-math-video/` without rebuilding `dist/` will fail CI-style review, because the generated trees drift. If you only edit `platforms/<agent>/`, rebuild too: the per-platform `README.md` and `INSTALL.md` are copied into `dist/`.

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

1. Bump `VERSION` (repo release, e.g. `0.2.0`).
2. Bump `metadata.version` in `manim-math-video/SKILL.md` (skill version, e.g. `1.3.0`).
3. Add a `CHANGELOG.md` entry.
4. Rebuild `dist/`, then tag `v0.2.0`.

## Installer changes

The installer must stay dependency-free until it has created its own environment:

```bash
python install.py --dry-run                 # plan only
python install.py --uninstall --dry-run     # never removes what it did not create
python -c "import urllib.request as u;exec(u.urlopen('file:///.../install.py').read().decode())" --dry-run
```

That last form exercises the `python -c` path, where `__file__` does not exist.

## Pull requests

- One topic per PR.
- Describe the user-visible effect, not the diff.
- Include the `--check` output and, for rendering changes, a contact sheet or a short clip.
- Say which agent and platform you tested with.

## Reporting problems

Use the issue templates. For rendering failures, include `scripts/check_env.py` output (it names the actual interpreter and Manim version), the command you ran, and the full traceback. `references/troubleshooting.md` already covers the common cases.
