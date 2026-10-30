# Install for GitHub Copilot

The GitHub Copilot build is `dist/copilot/skills/manim-math-video/`. Its frontmatter uses only the fields Copilot documents: `name`, `description`, and `argument-hint`.

Run the commands from the repository root and replace `path-to-project` with your project path. If you are reading this inside an installed skill, it is already installed; the update and uninstall sections still apply.

## Project install (recommended)

Copilot in VS Code, the Copilot CLI, the Copilot app, and the cloud agent discover repository skills in `.github/skills/`.

macOS / Linux:

```bash
cd path-to-project
mkdir -p .github/skills
cp -R path-to-path-of-knowledge/dist/copilot/skills/manim-math-video .github/skills/
```

Windows PowerShell:

```powershell
cd path-to-project
New-Item -ItemType Directory -Force -Path ".github\skills" | Out-Null
Copy-Item -Recurse -Force "path-to-path-of-knowledge\dist\copilot\skills\manim-math-video" ".github\skills\"
```

VS Code also discovers `.claude/skills/` and `.agents/skills/`, but `.github/skills/` is the shared location for the Copilot clients.

## Personal install

macOS / Linux:

```bash
cd path-of-knowledge
mkdir -p ~/.copilot/skills
cp -R dist/copilot/skills/manim-math-video ~/.copilot/skills/
```

Windows PowerShell:

```powershell
cd path-of-knowledge
New-Item -ItemType Directory -Force -Path "$HOME\.copilot\skills" | Out-Null
Copy-Item -Recurse -Force "dist\copilot\skills\manim-math-video" "$HOME\.copilot\skills\"
```

One-step alternative from the repository root:

```bash
python platforms/build.py --platform copilot --install
```

This replaces `~/.copilot/skills/manim-math-video/` with the generated build.

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

In Copilot Chat, the Copilot CLI, or the Copilot app:

```text
/manim-math-video Why does the derivative of x² equal 2x?
```

In the Copilot CLI you can also list discovered skills:

```bash
copilot skill list
```

The skill appears under **Personal skills** or **Project skills**. If it does not appear, confirm that the directory name matches the frontmatter `name` and that `SKILL.md` is inside `.github/skills/manim-math-video/`.

## Update

From the repository root:

```bash
python platforms/build.py --platform copilot
```

For a personal install:

```bash
python platforms/build.py --platform copilot --install
```

For a project install, rebuild and copy again, or update the checked-in `.github/skills/manim-math-video/` directory.

## Uninstall

Personal:

```bash
rm -rf ~/.copilot/skills/manim-math-video
copilot skill remove manim-math-video
```

Project:

```bash
rm -rf .github/skills/manim-math-video
```

## Notes

- The directory name must match the frontmatter `name`, or Copilot silently ignores the skill.
- Install the complete directory. Copilot loads supporting files only when `SKILL.md` references them.
- Keep the default inline context. The interview relies on the parent conversation; do not set `context: fork`.
- Add `disable-model-invocation: true` to require `/manim-math-video`; add `user-invocable: false` to hide it from the slash menu while still allowing automatic loading.
- `copilot skill add ./SKILL.md` copies only the Markdown file, which is not enough for this skill. Copy the whole directory or register the directory with `copilot skill add <directory>`.
