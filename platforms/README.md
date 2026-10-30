# Platform builds

`manim-math-video/` is the canonical skill. The `platforms/` directory holds only the thin per-platform differences, and `platforms/build.py` generates complete installable copies under `dist/`:

```text
dist/
├── claude/skills/manim-math-video/      # ~/.claude/skills or .claude/skills
├── codex/skills/manim-math-video/       # ~/.codex/skills, ~/.agents/skills, or .agents/skills
├── copilot/skills/manim-math-video/     # ~/.copilot/skills or .github/skills
└── pi/skills/manim-math-video/          # ~/.pi/agent/skills or .pi/skills
```

Every build contains the same scripts, references, assets, and examples. Only the frontmatter, the “Using this skill” section, and the Codex `agents/openai.yaml` differ.

## Build and verify

```bash
python platforms/build.py              # build every platform
python platforms/build.py --check      # fail if dist/ is stale
python platforms/build.py --platform claude --platform pi
python platforms/build.py --install    # copy builds into the local skill roots
```

Per-agent installation commands are in [`../INSTALL.md`](../INSTALL.md) and `platforms/<platform>/INSTALL.md`.

`--check` is suitable for CI. The generated skill directories are not edited by hand: update `manim-math-video/` or `platforms/<platform>/` and rebuild.

`--install` installs to:

| Platform | Destination |
|---|---|
| Claude Code | `~/.claude/skills/manim-math-video/` |
| Codex | `~/.codex/skills/manim-math-video/` |
| GitHub Copilot | `~/.copilot/skills/manim-math-video/` |
| Pi | `~/.pi/agent/skills/manim-math-video/` |

Project installs are also supported; see each platform README. `--install` replaces the destination skill directory with the generated build.

## Platform differences

| Platform | Frontmatter | Agent-specific metadata | Invocation |
|---|---|---|---|
| Claude Code | `name`, `description`, `license`, `metadata`, `argument-hint` | — | `/manim-math-video` |
| Codex | `name`, `description`, `license`, `metadata` | `agents/openai.yaml` | `$manim-math-video` |
| GitHub Copilot | `name`, `description`, `argument-hint` | — | `/manim-math-video` |
| Pi | `name`, `description`, `license`, `metadata` | — | `/skill:manim-math-video` |

Copilot gets a reduced frontmatter on purpose: its documented fields are `name`, `description`, `argument-hint`, `user-invocable`, `disable-model-invocation`, and `context`. The license and version remain in the repository and in the canonical skill.

## Source layout

```text
platforms/
├── manifest.json          # platform names, install roots, frontmatter rules
├── build.py               # build, check, and install
├── claude/{README,INSTALL,usage}.md
├── codex/{README,INSTALL,usage}.md
├── codex/agents/openai.yaml
├── copilot/{README,INSTALL,usage}.md
└── pi/{README,INSTALL,usage}.md
```

The canonical `SKILL.md` marks the platform-specific section with `<!-- platform-usage:start -->` and `<!-- platform-usage:end -->`. The build replaces everything between the markers with `platforms/<platform>/usage.md`, so the canonical file remains a valid, platform-neutral skill on its own.

## Verified against

- Agent Skills specification: <https://agentskills.io/specification>
- Claude Code skills: <https://code.claude.com/docs/en/skills> (Claude Code 2.1.302)
- Codex skills: <https://developers.openai.com/codex/skills>
- GitHub Copilot Agent Skills: <https://code.visualstudio.com/docs/copilot/customization/agent-skills> and Copilot CLI 1.0.103
- Pi skills: the installed Pi documentation for Agent Skills

Re-check the platform documentation when a host changes its discovery paths or frontmatter rules. Only `platforms/` should need an update.
