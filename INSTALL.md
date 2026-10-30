# Install Manim Math Video Studio

The skill ships as complete Agent Skills trees. Install the whole directory: `SKILL.md` references `scripts/`, `references/`, and `assets/`, so copying only the Markdown file is not enough.

## Choose your agent

| Agent | Detailed guide | Personal root | Project root | Invoke |
|---|---|---|---|---|
| Claude Code | [platforms/claude/INSTALL.md](platforms/claude/INSTALL.md) | `~/.claude/skills/` | `.claude/skills/` | `/manim-math-video` |
| Codex | [platforms/codex/INSTALL.md](platforms/codex/INSTALL.md) | `~/.agents/skills/` or `~/.codex/skills/` | `.agents/skills/` | `$manim-math-video` |
| GitHub Copilot | [platforms/copilot/INSTALL.md](platforms/copilot/INSTALL.md) | `~/.copilot/skills/` | `.github/skills/` | `/manim-math-video` |
| Pi | [platforms/pi/INSTALL.md](platforms/pi/INSTALL.md) | `~/.pi/agent/skills/` | `.pi/skills/` | `/skill:manim-math-video` |

Each guide includes:

- personal and project installs;
- bash and Windows PowerShell commands;
- verification of the installed skill;
- update and uninstall steps;
- platform-specific notes about frontmatter and context.

## Install everything locally

From the repository root:

```bash
python platforms/build.py --install
```

This builds all four versions and copies them to the personal roots configured in `platforms/manifest.json`:

| Agent | Destination used by `--install` |
|---|---|
| Claude Code | `~/.claude/skills/manim-math-video/` |
| Codex | `~/.codex/skills/manim-math-video/` |
| GitHub Copilot | `~/.copilot/skills/manim-math-video/` |
| Pi | `~/.pi/agent/skills/manim-math-video/` |

`--install` replaces the destination directory with the generated build. For Codex, the current Agent Skills location `~/.agents/skills/` is also supported; copy there manually if your build uses it.

To install one agent only:

```bash
python platforms/build.py --platform claude --install
python platforms/build.py --platform codex --install
python platforms/build.py --platform copilot --install
python platforms/build.py --platform pi --install
```

To verify that the generated builds are current:

```bash
python platforms/build.py --check
```

## Install by copying

From the repository root, pick the matching tree:

```text
dist/claude/skills/manim-math-video/
dist/codex/skills/manim-math-video/
dist/copilot/skills/manim-math-video/
dist/pi/skills/manim-math-video/
```

Then copy it into the personal or project root shown above. The per-agent guides show the exact commands.

## Requirements

Installing the skill does not install its runtime dependencies. You need:

- Python 3.10+
- Manim Community 0.19+ (0.22+ recommended)
- `edge-tts` (default narration), or Piper / a custom TTS command
- PyAV and Pillow for audio conversion, QA, and contact sheets
- LaTeX + `dvisvgm` only for equation beats

Recommended, from the repository root:

```bash
python scripts/setup.py
```

This creates `.venv`, installs all requirements, and runs the environment check. Manual setup:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd:        .venv\Scripts\activate.bat
# macOS / Linux:      source .venv/bin/activate
python -m pip install -r requirements.txt

# from the repository root
python scripts/check_env.py

# or from the skill directory
cd manim-math-video
python scripts/check_env.py
```

`check_env.py` and `render.py` find Manim in the active environment, a local `.venv`, or `MANIM_BIN` before falling back to PATH. On Windows, the Manim CLI is often installed in `%APPDATA%\Python\Python314\Scripts`; add that directory to PATH if you want `manim` available outside the venv.

Full installation and troubleshooting notes are in [README.md](README.md) and `manim-math-video/references/troubleshooting.md`.

## Update

Rebuild the generated trees, then reinstall:

```bash
python platforms/build.py
python platforms/build.py --install
```

Or copy the rebuilt agent directory again. Do not edit files inside an installed skill directly; update the canonical `manim-math-video/` or `platforms/<agent>/` and rebuild.

## Uninstall

Remove the installed skill directory for your agent, for example:

```bash
rm -rf ~/.claude/skills/manim-math-video
rm -rf ~/.codex/skills/manim-math-video
rm -rf ~/.copilot/skills/manim-math-video
rm -rf ~/.pi/agent/skills/manim-math-video
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$HOME\.claude\skills\manim-math-video"
Remove-Item -Recurse -Force "$HOME\.codex\skills\manim-math-video"
Remove-Item -Recurse -Force "$HOME\.copilot\skills\manim-math-video"
Remove-Item -Recurse -Force "$HOME\.pi\agent\skills\manim-math-video"
```

For a project install, remove the matching directory under `.claude/skills/`, `.github/skills/`, `.agents/skills/`, or `.pi/skills/`.
