# Install for Claude Code

The Claude Code build is `dist/claude/skills/manim-math-video/`. It uses the standard `name`, `description`, `license`, and `metadata` fields plus Claude Code's `argument-hint`.

Run the commands from the repository root and replace `path-to-project` with your project path. If you are reading this inside an installed skill, it is already installed; the update and uninstall sections still apply.

## Personal install

Available in every project.

macOS / Linux:

```bash
cd path-of-knowledge
mkdir -p ~/.claude/skills
cp -R dist/claude/skills/manim-math-video ~/.claude/skills/
```

Windows PowerShell:

```powershell
cd path-of-knowledge
New-Item -ItemType Directory -Force -Path "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force "dist\claude\skills\manim-math-video" "$HOME\.claude\skills\"
```

One-step alternative from the repository root:

```bash
python platforms/build.py --platform claude --install
```

This replaces `~/.claude/skills/manim-math-video/` with the generated build.

## Project install

Commit the skill with the repository so every Claude Code session in the project sees it.

macOS / Linux:

```bash
cd path-to-project
mkdir -p .claude/skills
cp -R path-to-path-of-knowledge/dist/claude/skills/manim-math-video .claude/skills/
```

Windows PowerShell:

```powershell
cd path-to-project
New-Item -ItemType Directory -Force -Path ".claude\skills" | Out-Null
Copy-Item -Recurse -Force "path-to-path-of-knowledge\dist\claude\skills\manim-math-video" ".claude\skills\"
```

Claude Code prefers the more specific project skill when both personal and project copies exist.

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

Start Claude Code and run:

```text
/manim-math-video Why does the derivative of x² equal 2x?
```

The skill also appears in the `/` menu. If it does not appear, run `/doctor`, check that `SKILL.md` is at `~/.claude/skills/manim-math-video/SKILL.md`, and restart the session.

## Update

From the repository root:

```bash
python platforms/build.py --platform claude
python platforms/build.py --platform claude --install
```

For a project install, rebuild and copy again, or update the checked-in `.claude/skills/manim-math-video/` directory.

## Uninstall

```bash
rm -rf ~/.claude/skills/manim-math-video
```

```powershell
Remove-Item -Recurse -Force "$HOME\.claude\skills\manim-math-video"
```

For a project install, remove `.claude/skills/manim-math-video/`.

## Notes

- Install the complete directory. The skill runs the Python scripts in `scripts/` and reads `references/` and `assets/`.
- Keep `context` unset. The workflow is interactive and should stay in the main conversation.
- The skill does not pre-approve tools. Approve `Bash` for the bundled scripts and `Write`/`Edit` for the user's workspace.
- Add `disable-model-invocation: true` to require `/manim-math-video`; add `user-invocable: false` to hide it from the slash menu while still allowing automatic loading.
