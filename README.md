# Manim Math Video Studio

A portable [Agent Skill](https://agentskills.io/specification) for turning a theme into a storyboarded, narrated Manim video — and into a consistent series. Prebuilt for Claude Code, Codex, GitHub Copilot, and Pi.

The agent interviews the user about the **content**, not just the topic: central question or narrative promise, audience, crux or progression, visual approach, and takeaway. It then locks four production parameters (**quality, voice, language, template**), scaffolds the episode, generates narration with timing, renders the selected visuals, and runs a QA pass. Mathematics is one supported subject; the same workflow serves history, science, technology, literature, philosophy, art, tutorials, and narrative videos.

## Install

One command, identical on macOS, Linux, and Windows. It installs the skill for every agent it finds on this machine and prepares a single shared Python environment. The only prerequisite is Python 3.10+ already on the machine.

```bash
python -c "import urllib.request as u;exec(u.urlopen('https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.py').read().decode())"
```

Windows: use `python` or `py` from PowerShell or `cmd` — same line, no edits. No Python yet? `winget install --id Python.Python.3.12 -e` (Windows), `brew install python` (macOS), `sudo apt install python3` (Debian/Ubuntu).

Add options after the closing quote, for example `--platform codex` or `--dry-run`. If your shell mangles them, set `MMS_ARGS="--platform codex"` instead.

Shorter variants, if you prefer a native wrapper:

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.sh | bash
```

```powershell
# Windows
irm https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.ps1 | iex
```

Two commands at worst, without downloading a script from a URL at all:

```bash
git clone --depth 1 https://github.com/kappa77/manim-math-video-studio
python manim-math-video-studio/install.py
```

Then restart your agent and invoke the skill with `/manim-math-video` (Claude Code, Copilot), `$manim-math-video` (Codex), or `/skill:manim-math-video` (Pi). Running the same command again updates an existing installation and is safe to repeat.

What the installer does:

1. copies the prebuilt skill tree into the personal skill root of each agent it detects — `~/.claude/skills/`, `~/.codex/skills/`, `~/.copilot/skills/`, `~/.pi/agent/skills/`;
2. creates one shared environment at `~/.manim-math-video/venv` and installs `requirements.txt` (Manim, edge-tts, PyAV, Pillow, NumPy), using `uv` when it is available to keep the install near a minute;
3. records `~/.manim-math-video/install.json`, runs `check_env.py`, and prints the invocation syntax per agent.

Options — append them to the one-liner, pass them after `bash -s --` for the wrapper, or set `MMS_ARGS`:

```bash
... --platform claude          # one agent; also: codex, copilot, pi, all
... --with-latex               # also install LaTeX + dvisvgm for equation beats
... --root ./skills            # install into a directory of your choice
... --dry-run                  # print the plan, change nothing
... --uninstall                # remove the skills and the shared environment
```

PowerShell takes the same options as parameters: `.\install.ps1 -Platform codex -WithLatex`.

Pin a release with `--ref v0.1.0` (or `MMS_REF=v0.1.0`), or install from a fork with `MMS_REPO=owner/name`. Set the ref to a branch name to track it deliberately.

## What is in this repository

```text
install.sh / install.ps1          # one-command installers: macOS/Linux, Windows
install.py                        # installer logic: skill trees + one shared environment
VERSION                           # release version, used for pinning and updates
INSTALL.md                        # install guide: options, layout, update, uninstall

scripts/
├── check_env.py                  # repo-root wrapper for the skill env check
└── setup.py                      # repo-only helper: create .venv and install requirements

manim-math-video/
├── SKILL.md                     # routing description + workflow instructions
├── references/
│   ├── interview.md             # content interview question bank
│   ├── brief.md                 # brief schema, defaults, quality presets
│   ├── templates.md             # template catalog and series rules
│   ├── voices.md                # voice/language selection and pronunciation
│   ├── storyboard.md            # beat grammar and pacing
│   ├── graphs.md                # graph specs, annotations, animations
│   ├── manim-recipes.md         # custom beats, 3D, camera, equations
│   ├── series.md                # series registry and consistency
│   ├── accuracy.md              # content verification checklist
│   ├── accuracy-math.md         # optional math specialization
│   └── troubleshooting.md       # installation and failure modes
├── agents/
│   └── openai.yaml              # Codex/ChatGPT interface metadata
├── assets/
│   ├── templates/               # clean-light, dark-board, paper-editorial
│   ├── project/                 # standalone manim_lib runtime + episode template
│   ├── voices.json              # curated edge-tts voices and styles
│   ├── brief.schema.json
│   ├── storyboard.schema.json
│   ├── brief.example.json
│   └── storyboard.example.json
├── scripts/
│   ├── check_env.py             # dependency diagnostics
│   ├── validate.py              # brief/storyboard/template validation
│   ├── new_episode.py           # scaffold a series episode
│   ├── storyboard_to_script.py  # readable script + duration estimate
│   ├── tts.py                   # edge-tts / Piper / custom / silent
│   ├── voice_samples.py         # comparable samples for voice selection
│   ├── render.py                # Manim render + copy + QA
│   ├── qa.py                    # streams, audio, subtitles, contact sheet
│   └── selftest.py              # asset checks + optional smoke render
└── examples/                    # verified demo series source + preview contact sheet

platforms/                       # per-platform frontmatter, usage, and install notes
├── manifest.json
├── build.py                     # build/check/install dist copies
├── claude/
├── codex/
├── copilot/
└── pi/

dist/                            # generated installable skill trees
├── claude/skills/manim-math-video/
├── codex/skills/manim-math-video/
├── copilot/skills/manim-math-video/
└── pi/skills/manim-math-video/
```

`manim-math-video/` is the canonical skill. `dist/` contains the same scripts, references, assets, and examples with platform-specific frontmatter and usage instructions. Regenerate it after editing the canonical skill:

```bash
python platforms/build.py
python platforms/build.py --check
```

## Requirements

`install.py` provides all of this. The list matters only if you set up an environment by hand.

- Python 3.10+
- Manim Community 0.19+ (0.22+ recommended)
- `edge-tts` (default narration), or Piper / a custom TTS command
- PyAV (audio conversion and QA) and Pillow (contact sheets)
- A LaTeX distribution for equation beats (`latex` + `dvisvgm`)

Manual setup, on top of an existing skill installation:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# Windows cmd:        .venv\Scripts\activate.bat
# macOS / Linux:      source .venv/bin/activate
python -m pip install -r requirements.txt

# from the repository root (wrapper)
python scripts/check_env.py

# or from the skill directory
cd manim-math-video
python scripts/check_env.py
```

The check colors `ok`, `warn`, `optional`, and `fail` in a terminal. Use `--color always` to force color in captured output, `--no-color` to disable it, and `--json` for machine-readable output.

### Which Python and Manim the scripts use

The scripts resolve the runtime in this order, so a plain `python scripts/render.py` works without activating anything:

1. `MANIM_BIN`, then the interpreter running the script;
2. `MANIM_STUDIO_VENV`, then the environment recorded in `<skill>/.venv-path` by the installer, then the shared `~/.manim-math-video/venv`;
3. a `.venv` or `venv` in the working directory or any parent (so a repository `.venv` still wins), or beside the skill directory;
4. `manim` on `PATH`.

If the interpreter that starts a script lacks NumPy, Manim, PyAV, or Pillow, the script re-executes itself once with the shared environment and says so. Disable that with `MANIM_STUDIO_NO_REEXEC=1`.

## Install LaTeX + dvisvgm

LaTeX is only needed for **equation beats**. Graphs, narration, captions, and titles work without it. Manim uses the `latex` compiler and `dvisvgm` to turn equations into SVG.

`install.py --with-latex` installs MiKTeX through `winget` on Windows and BasicTeX through `brew` on macOS, then verifies both commands. The manual routes below cover Linux and custom setups.

### Windows (recommended: MiKTeX)

```powershell
winget install --id MiKTeX.MiKTeX -e --accept-package-agreements --accept-source-agreements
```

Then open **MiKTeX Console** → **Settings** and set **Missing packages** to **Always install missing packages on-the-fly**. Close and reopen the terminal.

Verify:

```powershell
where latex
where dvisvgm
latex --version
dvisvgm --version
```

If `dvisvgm` is missing, install it from MiKTeX Console → **Packages**, or run:

```powershell
mpm --install=dvisvgm
```

Chocolatey alternative: `choco install miktex -y`.

### Windows (lightweight: TinyTeX)

Download the latest **TinyTeX-1 Windows** installer from [rstudio/tinytex-releases](https://github.com/rstudio/tinytex-releases/releases). It is a 7-Zip SFX archive; extract it to a tools directory:

```powershell
TinyTeX-1-windows.exe -y -o C:\tools\TinyTeX
$env:PATH = "C:\tools\TinyTeX\TinyTeX\bin\windows;$env:PATH"
```

Install the common Manim requirements:

```powershell
tlmgr update --self
tlmgr install dvisvgm standalone amsmath amsfonts
# optional broader coverage:
tlmgr install collection-latexrecommended collection-fontsrecommended
```

Add `C:\tools\TinyTeX\TinyTeX\bin\windows` to the persistent **Path** environment variable. If a render reports a missing `.sty` file, install it with `tlmgr install <package-name>`.

### macOS

```bash
brew install --cask mactex-no-gui
# or, for a smaller install:
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install dvisvgm standalone amsmath amsfonts
```

### Linux

```bash
# Debian / Ubuntu
sudo apt update
sudo apt install texlive texlive-latex-extra texlive-fonts-recommended dvisvgm

# Fedora
sudo dnf install texlive-scheme-medium dvisvgm

# Arch
sudo pacman -S texlive-basic texlive-latexextra dvisvgm
```

### Verify the installation

```bash
manim checkhealth
```

Both of these should say `PASSED`:

```text
- Checking whether latex is available ... PASSED
- Checking whether dvisvgm is available ... PASSED
```

Then verify the skill environment:

```bash
cd manim-math-video
python scripts/check_env.py
```

`LaTeX` and `dvisvgm` should both show `ok`. More installation and failure notes are in `manim-math-video/references/troubleshooting.md`.

## Manual install per agent

The installer covers this section. It stays here for project installs, for pinning a build by hand, and for machines where you cannot run a script. The repository ships installable builds for Claude Code, Codex, GitHub Copilot, and Pi: pick the matching tree from `dist/` and copy its `manim-math-video` directory into a skill root. Detailed per-agent guides are in [INSTALL.md](INSTALL.md).

### Claude Code

```bash
# Personal
mkdir -p ~/.claude/skills
cp -R dist/claude/skills/manim-math-video ~/.claude/skills/

# Project
mkdir -p .claude/skills
cp -R dist/claude/skills/manim-math-video .claude/skills/
```

Invoke with `/manim-math-video <topic>`. See `platforms/claude/README.md`.

### Codex

```bash
# Current Agent Skills location
mkdir -p ~/.agents/skills
cp -R dist/codex/skills/manim-math-video ~/.agents/skills/

# Codex desktop app location, if that is where Codex looks
mkdir -p ~/.codex/skills
cp -R dist/codex/skills/manim-math-video ~/.codex/skills/

# Project
mkdir -p .agents/skills
cp -R dist/codex/skills/manim-math-video .agents/skills/
```

Invoke with `$manim-math-video <topic>` or choose it from `/skills`. See `platforms/codex/README.md`.

### GitHub Copilot

```bash
# Project, shared with the repository
mkdir -p .github/skills
cp -R dist/copilot/skills/manim-math-video .github/skills/

# Personal
mkdir -p ~/.copilot/skills
cp -R dist/copilot/skills/manim-math-video ~/.copilot/skills/
```

Invoke with `/manim-math-video <topic>` in Copilot Chat, the Copilot CLI, or the Copilot app. VS Code also discovers `.claude/skills/` and `.agents/skills/`. See `platforms/copilot/README.md`.

### Pi

```bash
# Personal
mkdir -p ~/.pi/agent/skills
cp -R dist/pi/skills/manim-math-video ~/.pi/agent/skills/

# Project
mkdir -p .pi/skills
cp -R dist/pi/skills/manim-math-video .pi/skills/
```

Invoke with `/skill:manim-math-video <topic>`. See `platforms/pi/README.md`.

On Windows PowerShell, create directories with `New-Item -ItemType Directory -Force -Path <dir>` and copy with `Copy-Item -Recurse -Force <source> <destination>`. All builds require the complete directory; `SKILL.md` references the bundled scripts, references, and assets.

To install every platform into its personal skill root at once, and to verify that `dist/` is current:

```bash
python platforms/build.py --install
python platforms/build.py --check
```

See `platforms/README.md` for the differences between frontmatter, metadata, and invocation syntax.

## Quick start

Run the installer once; it creates the shared environment and checks it. Then work from the skill directory; the scripts find that environment on their own.

```bash
cd manim-math-video

# 1. Check the environment
python scripts/check_env.py

# 2. Scaffold a series + episode from the example brief
python scripts/new_episode.py --brief assets/brief.example.json --series-dir ../my-series

# 3. Fill the storyboard, or copy the demo storyboard
cp assets/storyboard.example.json ../my-series/episodes/001-why-derivative-x-squared/storyboard.json

# 4. Validate, narrate, render a draft
python scripts/validate.py --episode ../my-series/episodes/001-why-derivative-x-squared
python scripts/storyboard_to_script.py --episode ../my-series/episodes/001-why-derivative-x-squared
python scripts/tts.py --episode ../my-series/episodes/001-why-derivative-x-squared
python scripts/render.py --episode ../my-series/episodes/001-why-derivative-x-squared --quality draft
```

## How the pipeline works

1. **Interview** — the agent follows `references/interview.md` and asks for the four required parameters plus the content core.
2. **Voice selection** — `voice_samples.py` generates numbered, comparable samples; the explicit choice is recorded in `brief.json`.
3. **Brief** — `brief.json` records the approved thesis, audience, progression, terminology, quality, voice, language, and template.
4. **Scaffold** — `new_episode.py` creates a standalone episode with a copied `manim_lib/`, a theme snapshot, and a storyboard skeleton.
5. **Storyboard** — `storyboard.json` has one narration segment per beat and one visual idea per beat.
6. **Narration** — `tts.py` writes `voice/*.wav`, `voice/manifest.json`, and a preview SRT. Edge TTS word boundaries are captured.
7. **Render** — the generated `episode.py` subclasses `StoryboardScene`, which reads the storyboard, theme, and voice manifest, adds sound and captions, and renders the selected visuals (graphs, equations, diagrams, and custom beats).
8. **QA** — `render.py` copies the MP4/SRT and `qa.py` produces a contact sheet, stream report, audio levels, subtitle coverage, and warnings.

## The templates

| Template | Look | Best for |
|---|---|---|
| `clean-light` | warm off-white, ink, cobalt/amber, precise sans | general explainers, graphs, classroom |
| `dark-board` | deep navy, chalk-bright ink, cyan/violet | calculus, analysis, linear algebra, long-form |
| `paper-editorial` | warm paper, serif, oxblood/olive | history/philosophy of math, essays |

A template locks palette, fonts, layout, graph styling, motion, captions, and narrative rhythm. The episode keeps a `theme.json` snapshot so later catalog changes do not silently restyle old videos.

## Verified demo

The `manim-math-video/examples/demo-series` source is a complete 3-minute episode on the derivative of x². It was scaffolded, narrated with edge-tts, rendered at 480p15, and QA'd. See `manim-math-video/examples/README.md` and the preview contact sheet:

![Demo contact sheet](manim-math-video/examples/demo-preview.jpg)

## Graph support

The data-driven runtime supports:

- Cartesian plots from safe expressions (`x**2`, `sin(x)/x`, `exp(-x**2)`).
- Parametric curves.
- Data series and bar charts.
- Vector fields.
- Annotations: points, text, vertical/horizontal lines, tangents, secants, areas, Riemann rectangles, braces, arrows, slope triangles, derivatives.
- Animations: draw, sweep, secant-to-tangent, Riemann refinement, area reveal.
- 3D surfaces via a `custom` beat and `ThreeDScene` (recipe included).

## Aspect ratios

`16:9` is the default. The runtime also supports `9:16`, `1:1`, and `4:3` with automatic frame sizing; `render.py` swaps the output dimensions and names the file accordingly. Vertical layouts stack the `compare` columns. Always review a draft contact sheet for overflow and caption fit.

## Narration support

- **edge-tts** (default): many languages, curated voices, style presets, word boundaries.
- **Piper**: offline, local model.
- **Custom command**: ElevenLabs, OpenAI TTS, Azure, or a local model.
- **None**: silent timing draft.

Language and voice are independent of the template. Subtitles can be translated per beat with the `caption` field.

## Series consistency

`series.json` locks the template, quality, language, voice, title grammar, and narrative rhythm. `new_episode.py` refuses style drift unless `--allow-style-drift "reason"` is passed. See `references/series.md`.

## Validation

```bash
python scripts/validate.py --brief brief.json
python scripts/validate.py --episode path/to/episode
python scripts/validate.py --template assets/templates/dark-board.json
```

Validation checks required fields, template existence, quality, voice/locale compatibility, beat IDs, graph expressions, annotation types, equation/LaTeX availability, duration drift, and the voice manifest.

## License

MIT. See `LICENSE`.

## Notes

- This project is not affiliated with Manim Community or Microsoft edge-tts.
- The `dark-board` template is an original visual style, not a reproduction of any existing channel's branding.
- Always verify the mathematics and the rights to images, music, fonts, and quotations.
