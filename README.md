# Manim Math Video Studio

[![release](https://img.shields.io/github/v/release/kappa77/manim-math-video-studio?color=blue)](https://github.com/kappa77/manim-math-video-studio/releases/latest)
[![license](https://img.shields.io/github/license/kappa77/manim-math-video-studio)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-yellow)](INSTALL.md)
[![agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex%20%7C%20Copilot%20%7C%20Pi-blueviolet)](INSTALL.md)

A portable [Agent Skill](https://agentskills.io/specification) that turns a topic into a storyboarded, narrated Manim video — and into a consistent series. Prebuilt for Claude Code, Codex, GitHub Copilot, and Pi.

```bash
python -c "import urllib.request as u;exec(u.urlopen('https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.py').read().decode())"
```

It finds the agents on your machine, installs the skill for each, prepares one shared environment at `~/.manim-math-video/venv` (with `uv` when available), and verifies it. Same command on macOS, Linux, and Windows; needs Python 3.10+.

Other routes — `curl -fsSL …/install.sh | bash`, `irm …/install.ps1 | iex`, or `git clone` + `python install.py` — are in [INSTALL.md](INSTALL.md).

![Contact sheet: frames from the generated demo episode on the derivative of x squared](manim-math-video/examples/demo-preview.jpg)

*Frames from the demo episode in `manim-math-video/examples/` — generated end to end by the skill, from brief to render.*

## What it does

- **Interview first.** It asks about the content — central question, audience, crux, visual approach, takeaway — then locks quality, voice, language, and template. A theme is not a brief.
- **Narration drives the clock.** Each beat gets a measured TTS duration and the animation follows it, so nothing is cut off mid-sentence and subtitles stay in sync.
- **Beats and visuals.** `title`, `section`, `bullets`, `compare`, `quote`, `image`, `recap`, `outro`, plus custom beats, graphs, equations, camera, and 3D.
- **Built for series.** A series registry keeps template, palette, typography, and narration identity stable, so episode 12 still looks like episode 1.
- **Verified, not vibes.** JSON-schema validation for brief and storyboard, environment checks, contact-sheet QA, and a self-test.
- **Any subject.** History, science, technology, literature, philosophy, art, tutorials — mathematics is one supported domain, not the whole product.

## Documentation

| Doc | Covers |
|---|---|
| [INSTALL.md](INSTALL.md) | one-command install, options, LaTeX, manual install, runtime resolution, update, uninstall, troubleshooting |
| [USAGE.md](USAGE.md) | quick start, command reference, pipeline, beats, templates, graphs, narration, series, validation |
| [CONTRIBUTING.md](CONTRIBUTING.md) | repository layout, source of truth vs `dist/`, adding beats and templates, versioning |
| [CHANGELOG.md](CHANGELOG.md) | what changed, release by release |
| [manim-math-video/SKILL.md](manim-math-video/SKILL.md) | the workflow the agent follows; the detailed manual is `manim-math-video/references/` |
| [Landing page](https://kappa77.github.io/manim-math-video-studio/) | one-page overview with the copy-paste install |

## Invoke

| Agent | Command |
|---|---|
| Claude Code | `/manim-math-video` |
| Codex | `$manim-math-video` |
| GitHub Copilot | `/manim-math-video` |
| Pi | `/skill:manim-math-video` |

Then ask for a video, for example: *"Make a 90-second video on why the derivative of x² is 2x."*

## Requirements

Python 3.10+, Manim Community 0.19+ (0.22+ recommended), `edge-tts`, PyAV, Pillow, and NumPy. The installer provides all of them. LaTeX plus `dvisvgm` is needed only for equation beats (`--with-latex` automates MiKTeX on Windows and BasicTeX on macOS).

## License and notes

- MIT — see [LICENSE](LICENSE).
- Not affiliated with Manim Community or Microsoft `edge-tts`. The `dark-board` template is an original visual style, not a reproduction of any channel's branding.
- Verify the mathematics, and the rights to any images, music, fonts, and quotations you use.
