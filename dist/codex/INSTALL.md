# Install for Codex

The Codex build is `dist/codex/skills/manim-math-video/`. It includes `agents/openai.yaml` for the Codex/ChatGPT skill interface.

Run the commands from the repository root and replace `path-to-project` with your project path. If you are reading this inside an installed skill, it is already installed; the update and uninstall sections still apply.

## Personal install

Current Agent Skills location.

macOS / Linux:

```bash
cd path-of-knowledge
mkdir -p ~/.agents/skills
cp -R dist/codex/skills/manim-math-video ~/.agents/skills/
```

Windows PowerShell:

```powershell
cd path-of-knowledge
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse -Force "dist\codex\skills\manim-math-video" "$HOME\.agents\skills\"
```

Codex desktop builds that use the `.codex` directory can install there instead:

```bash
mkdir -p ~/.codex/skills
cp -R dist/codex/skills/manim-math-video ~/.codex/skills/
```

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.codex\skills" | Out-Null
Copy-Item -Recurse -Force "dist\codex\skills\manim-math-video" "$HOME\.codex\skills\"
```

One-step alternative from the repository root:

```bash
python platforms/build.py --platform codex --install
```

This replaces `~/.codex/skills/manim-math-video/` with the generated build. Copy to `~/.agents/skills/` manually if that is your Codex skill root.

## Project install

Commit the skill with the repository:

```bash
cd path-to-project
mkdir -p .agents/skills
cp -R path-to-path-of-knowledge/dist/codex/skills/manim-math-video .agents/skills/
```

```powershell
cd path-to-project
New-Item -ItemType Directory -Force -Path ".agents\skills" | Out-Null
Copy-Item -Recurse -Force "path-to-path-of-knowledge\dist\codex\skills\manim-math-video" ".agents\skills\"
```

## Runtime dependencies

The skill is instructions and scripts; it needs the video toolchain. From the repository root, the easiest setup is:

```bash
python scripts/setup.py
```

This creates `.venv`, installs `requirements.txt`, and runs the environment check. Alternatively install into your own environment:

```bash
python -m pip install manim edge-tts av pillow numpy
```

LaTeX + `dvisvgm` are needed only for equation beats. `check_env.py` and `render.py` look for Manim in the active environment, a local `.venv`, and `MANIM_BIN` before falling back to PATH.

## Verify

In Codex CLI or the IDE extension:

```text
$manim-math-video Why does the derivative of x² equal 2x?
```

Or open `/skills` and choose **Manim Video Studio**. In the ChatGPT desktop app, type `@` and select the skill. If it does not appear, restart Codex and confirm that `SKILL.md` is in one of the skill roots listed above.

## Update

From the repository root:

```bash
python platforms/build.py --platform codex
python platforms/build.py --platform codex --install
```

For a project install, rebuild and copy again, or update the checked-in `.agents/skills/manim-math-video/` directory.

## Uninstall

```bash
rm -rf ~/.codex/skills/manim-math-video
rm -rf ~/.agents/skills/manim-math-video
```

```powershell
Remove-Item -Recurse -Force "$HOME\.codex\skills\manim-math-video"
Remove-Item -Recurse -Force "$HOME\.agents\skills\manim-math-video"
```

For a project install, remove `.agents/skills/manim-math-video/`.

## Notes

- `agents/openai.yaml` controls the display name, short description, and default prompt.
- Set `policy.allow_implicit_invocation: false` in `agents/openai.yaml` to require explicit `$manim-math-video` invocation.
- Codex reads skills from `.agents/skills` and `$HOME/.agents/skills`; some desktop builds also use `$HOME/.codex/skills`.
- Install the complete directory; `SKILL.md` references `scripts/`, `references/`, and `assets/`.
- Restart Codex if a skill update does not appear. Use `[[skills.config]]` in `~/.codex/config.toml` to disable a skill without deleting it.
