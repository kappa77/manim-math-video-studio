# Install Manim Math Video Studio

One command installs the skill for the agents on your machine and prepares a
single shared Python environment. No activation, no manual `pip`, no copying
directories by hand.

## Quick start

One command, identical on macOS, Linux, and Windows:

```bash
python -c "import urllib.request as u;exec(u.urlopen('https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.py').read().decode())"
```

It needs only Python 3.10+ (Windows: `winget install --id Python.Python.3.12 -e`, macOS: `brew install python`, Debian/Ubuntu: `sudo apt install python3`). Use `python` or `py` — the line is the same in PowerShell, `cmd`, bash, and zsh.

Shorter native wrappers, one per platform:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.sh | bash
```

```powershell
# Windows
irm https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.ps1 | iex
```

Two commands at worst, with no download-through-a-pipe at all:

```bash
git clone --depth 1 https://github.com/kappa77/manim-math-video-studio
python manim-math-video-studio/install.py
```

The installer prints a plan, then:

1. copies the prebuilt skill tree into the personal skill root of every agent it detects;
2. creates the shared environment at `~/.manim-math-video/venv` and installs `requirements.txt`;
3. records what it did in `~/.manim-math-video/install.json`;
4. runs `check_env.py` against the installed skill;
5. prints the invocation syntax for each platform.

Restart your agent afterwards so it reloads its skill directory.

## What gets installed where

| Agent | Skill directory | Invoke |
|---|---|---|
| Claude Code | `~/.claude/skills/manim-math-video/` | `/manim-math-video` |
| Codex | `~/.codex/skills/manim-math-video/` (or `~/.agents/skills/`) | `$manim-math-video` |
| GitHub Copilot | `~/.copilot/skills/manim-math-video/` | `/manim-math-video` |
| Pi | `~/.pi/agent/skills/manim-math-video/` | `/skill:manim-math-video` |

Shared environment: `~/.manim-math-video/venv` — one copy of Manim for all four
agents. Installation state: `~/.manim-math-video/install.json`.

Detection uses the agent CLI on `PATH` and its configuration directory. With no
agent detected, the installer falls back to Claude Code and says so; pass
`--platform` to be explicit.

## Options

| Flag | Effect |
|---|---|
| `--platform auto` | default: every agent detected on this machine |
| `--platform claude` | one agent; also `codex`, `copilot`, `pi` |
| `--platform codex,copilot` | a comma list |
| `--platform all` | all four, even if not detected |
| `--root DIR` | install into `DIR/manim-math-video` instead of a personal root |
| `--venv DIR` | use a different environment location |
| `--with-latex` | also install LaTeX + `dvisvgm` for equation beats |
| `--no-deps` | install the skill files only (no Python packages) |
| `--no-uv` | always use `pip`, even when `uv` is available |
| `--dry-run` | print the plan and exit |
| `--uninstall` | remove the installed skills and the shared environment |
| `--source DIR` | use a local checkout instead of downloading |
| `--ref REF` | git ref to download: `main` (default), a branch, or `v0.3.2` |
| `--quiet` / `--verbose` | hide command lines / show full `pip` output |
With the piped installer, pass flags after `bash -s --`. With the universal one-liner, append them after the closing quote:

```bash
curl -fsSL .../install.sh | bash -s -- --platform claude --with-latex
curl -fsSL .../install.sh | bash -s -- --dry-run

python -c "..." --platform claude --with-latex
```

If a shell mangles the trailing flags, use the environment instead: `MMS_ARGS="--platform claude --with-latex"`.

With PowerShell, use the parameter form: `.\install.ps1 -Platform codex -WithLatex`.

Environment overrides: `MMS_REPO=owner/name` installs from a fork,
`MMS_REF=v0.3.2` pins a release, `MMS_REF=<branch>` tracks another branch, and
`MMS_ARCHIVE_URL=<url>` replaces the codeload download (a mirror, or a local
`file://` archive for offline and test runs).

## Verify

```bash
~/.manim-math-video/venv/bin/python ~/.claude/skills/manim-math-video/scripts/check_env.py
```

Windows: `%USERPROFILE%\.manim-math-video\venv\Scripts\python.exe` with the
matching skill path.

You can also call the script from the skill directory with any Python 3.10+; it
switches to the shared environment automatically when it lacks the runtime
dependencies. See [Runtime resolution](#runtime-resolution).

`ok` rows are ready, `warn` rows cover some workflows, `optional` rows are nice
to have, `fail` rows block rendering. LaTeX is the only common `fail`-adjacent
gap: equation beats need it, everything else works without it. When `LaTeX` or
`dvisvgm` is `warn`, the table prints the install commands for your OS.

Maintainers can reproduce the install on every supported harness in clean
containers. The fast suite needs no API keys and no real agent installation:

```bash
python tests/install_matrix.py --scope fast
python tests/install_matrix.py --scope runtime --render

tests/docker/run.sh                              # Python 3.10-3.13 + Alpine
tests/docker/run.sh --scope runtime --render     # real dependencies
```

See [tests/README.md](tests/README.md) for what each scope verifies.

## Platform notes and project installs

| Agent | Detailed guide |
|---|---|
| Claude Code | [platforms/claude/INSTALL.md](platforms/claude/INSTALL.md) |
| Codex | [platforms/codex/INSTALL.md](platforms/codex/INSTALL.md) |
| GitHub Copilot | [platforms/copilot/INSTALL.md](platforms/copilot/INSTALL.md) |
| Pi | [platforms/pi/INSTALL.md](platforms/pi/INSTALL.md) |

Each guide covers personal and project installs, PowerShell commands,
verification, update, and uninstall.

A project install keeps the skill inside the repository, so it is shared with
everyone who works there. Install into a project directory with `--root`:

```bash
python install.py --platform claude --root .claude/skills
python install.py --platform codex --root .agents/skills
python install.py --platform copilot --root .github/skills
python install.py --platform pi --root .pi/skills
```

The skill directory must stay complete: `SKILL.md` references the bundled
`scripts/`, `references/`, and `assets/`. Copying the Markdown file alone does
not work.

## Manual install

Use this route when the installer cannot run: offline machines, restricted
networks, or a hand-built environment.

```bash
git clone https://github.com/kappa77/manim-math-video-studio
cd manim-math-video-studio

# copy the tree for your agent into its skill root
cp -R dist/claude/skills/manim-math-video ~/.claude/skills/
cp -R dist/codex/skills/manim-math-video ~/.codex/skills/
cp -R dist/copilot/skills/manim-math-video ~/.copilot/skills/
cp -R dist/pi/skills/manim-math-video ~/.pi/agent/skills/
```

Then provide a Python environment with `requirements.txt` installed — the
repository-local route is:

```bash
python scripts/setup.py     # creates ./.venv, installs requirements, checks it
```

Rebuild the generated `dist/` trees after editing `manim-math-video/` or
`platforms/<agent>/`:

```bash
python platforms/build.py
python platforms/build.py --check     # fail if dist/ is stale
python platforms/build.py --install   # copy every build into its personal root
```

## Runtime resolution

The scripts pick the first working runtime:

1. `MANIM_BIN`, then the interpreter running the script;
2. `MANIM_STUDIO_VENV`, then the environment recorded in
   `<skill>/.venv-path` by the installer, then `~/.manim-math-video/venv`;
3. a `.venv` or `venv` in the working directory or any parent, or beside the
   skill directory;
4. `manim` on `PATH`.

If the starting interpreter lacks NumPy, Manim, PyAV, or Pillow, the script
re-executes itself once with the shared environment and prints which one it
used. `MANIM_STUDIO_NO_REEXEC=1` disables that behaviour.

This is why `python scripts/render.py ...` works whether or not you activated
anything, and why an existing repository `.venv` still takes precedence.

## Requirements

The installer resolves all of these; the list is here for manual setups:

- Python 3.10+
- Manim Community 0.19+ (0.22+ recommended)
- `edge-tts` (default narration), or Piper / a custom TTS command
- PyAV and Pillow for audio conversion, QA, and contact sheets
- LaTeX + `dvisvgm` only for equation beats

`--with-latex` installs MiKTeX through `winget` on Windows and BasicTeX through
`brew` on macOS. On Fedora, Debian, and Arch:

```bash
sudo apt install texlive texlive-latex-extra dvisvgm   # Debian / Ubuntu
sudo dnf install texlive-scheme-medium dvisvgm         # Fedora
sudo pacman -S texlive-basic texlive-latexextra dvisvgm
```

After a MiKTeX install, open MiKTeX Console → Settings and set **Missing
packages** to **Always install missing packages on-the-fly**.

`ffmpeg` is optional: Manim 0.22 uses PyAV for most media work. Install it only
for subtitle burn-in and audio normalization.

## Update

Run the same one command again — the installer is idempotent. It replaces the
skill trees in place and leaves the shared environment alone when the
requirements are already satisfied:

```bash
python -c "import urllib.request as u;exec(u.urlopen('https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.py').read().decode())"
```

Force a dependency refresh with `--venv` pointing at a new directory, or delete
`~/.manim-math-video/venv` and rerun.

## Uninstall

```bash
python install.py --uninstall           # or: ... | bash -s -- --uninstall
python install.py --uninstall --dry-run # show what would be removed
```

The installer removes the skill directories it recorded, the shared
environment, and the state file. It skips paths it did not create.

Manual removal:

```bash
rm -rf ~/.claude/skills/manim-math-video
rm -rf ~/.codex/skills/manim-math-video
rm -rf ~/.copilot/skills/manim-math-video
rm -rf ~/.pi/agent/skills/manim-math-video
rm -rf ~/.manim-math-video
```

On Windows PowerShell:

```powershell
Remove-Item -Recurse -Force "$HOME\.claude\skills\manim-math-video"
Remove-Item -Recurse -Force "$HOME\.manim-math-video"
```

For a project install, remove the matching directory under `.claude/skills/`,
`.github/skills/`, `.agents/skills/`, or `.pi/skills/`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Python 3.10+ not found` | install Python (Windows: `winget install --id Python.Python.3.12 -e`) and rerun |
| `download failed` | check the network, or clone the repository and run `python install.py` |
| `missing prebuilt trees` | `python platforms/build.py` in a checkout |
| agent does not list the skill | restart the agent; confirm the directory from the table above exists |
| `manim: command not found` in your own shell | the skill uses its environment internally; activate `~/.manim-math-video/venv` if you want `manim` interactively |
| `FileNotFoundError: latex` | run `--with-latex`, or avoid equation beats |

More failure modes: `manim-math-video/references/troubleshooting.md`.
