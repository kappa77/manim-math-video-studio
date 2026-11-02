# Manim Math Video Studio

Installer for the [manim-math-video Agent Skill](https://github.com/kappa77/manim-math-video-studio) — a portable skill that turns a topic into a storyboarded, narrated Manim video with subtitles.

This package is the **thin installer**: it detects the agent harness, installs the prebuilt skill tree, and prepares one shared Python environment with Manim. The skill files themselves are downloaded from the matching GitHub release tag.

## Install

```bash
uvx manim-math-video-studio --platform claude
```

or with `pipx`:

```bash
pipx run --spec manim-math-video-studio manim-math-video-studio --platform claude
```

Replace `claude` with `codex`, `copilot`, or `pi`. Use `--platform all` to install every harness explicitly.

Supported harnesses:

| Harness | Invocation |
|---|---|
| Claude Code | `/manim-math-video` |
| Codex | `$manim-math-video` |
| GitHub Copilot | `/manim-math-video` |
| Pi | `/skill:manim-math-video` |

## Requirements

Python 3.10+. LaTeX and `dvisvgm` are optional and only needed for equation beats. The installer prints the platform-specific install commands when either is missing.

## Links

- [Install guide](https://github.com/kappa77/manim-math-video-studio/blob/main/INSTALL.md)
- [Usage](https://github.com/kappa77/manim-math-video-studio/blob/main/USAGE.md)
- [Source](https://github.com/kappa77/manim-math-video-studio)
- [Changelog](https://github.com/kappa77/manim-math-video-studio/blob/main/CHANGELOG.md)

MIT licensed.
