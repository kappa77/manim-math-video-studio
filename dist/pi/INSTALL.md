# Install for Pi

The Pi build is `dist/pi/skills/manim-math-video/`. It uses the Agent Skills standard and Pi's `/skill:name` command.

Run the commands from the repository root and replace `path-to-project` with your project path. If you are reading this inside an installed skill, it is already installed; the update and uninstall sections still apply.

## Personal install

macOS / Linux:

```bash
cd path-of-knowledge
mkdir -p ~/.pi/agent/skills
cp -R dist/pi/skills/manim-math-video ~/.pi/agent/skills/
```

Windows PowerShell:

```powershell
cd path-of-knowledge
New-Item -ItemType Directory -Force -Path "$HOME\.pi\agent\skills" | Out-Null
Copy-Item -Recurse -Force "dist\pi\skills\manim-math-video" "$HOME\.pi\agent\skills\"
```

Pi also supports the Agent Skills standard location:

```bash
mkdir -p ~/.agents/skills
cp -R dist/pi/skills/manim-math-video ~/.agents/skills/
```

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse -Force "dist\pi\skills\manim-math-video" "$HOME\.agents\skills\"
```

One-step alternative from the repository root:

```bash
python platforms/build.py --platform pi --install
```

This replaces `~/.pi/agent/skills/manim-math-video/` with the generated build.

## Project install

Commit the skill with the repository, using `.pi/skills/` or `.agents/skills/`:

```bash
cd path-to-project
mkdir -p .pi/skills
cp -R path-to-path-of-knowledge/dist/pi/skills/manim-math-video .pi/skills/
```

```powershell
cd path-to-project
New-Item -ItemType Directory -Force -Path ".pi\skills" | Out-Null
Copy-Item -Recurse -Force "path-to-path-of-knowledge\dist\pi\skills\manim-math-video" ".pi\skills\"
```

Pi scans directories containing `SKILL.md` recursively.

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

Start Pi and invoke:

```text
/skill:manim-math-video Why does the derivative of x² equal 2x?
```

The skill also appears in the skill picker. If it does not appear, confirm that `SKILL.md` is inside `~/.pi/agent/skills/manim-math-video/` and run `/reload`.

## Update

From the repository root:

```bash
python platforms/build.py --platform pi
python platforms/build.py --platform pi --install
```

For a project install, rebuild and copy again, or update the checked-in `.pi/skills/manim-math-video/` directory. Run `/reload` in an active Pi session after editing the skill.

## Uninstall

```bash
rm -rf ~/.pi/agent/skills/manim-math-video
```

```powershell
Remove-Item -Recurse -Force "$HOME\.pi\agent\skills\manim-math-video"
```

For a project install, remove `.pi/skills/manim-math-video/` or `.agents/skills/manim-math-video/`.

## Notes

- Install the complete directory; `scripts/`, `references/`, and `assets/` are part of the skill.
- Add `disable-model-invocation: true` to the frontmatter to require `/skill:manim-math-video`; Pi still allows the explicit command.
- Pi asks before risky commands. Approve the bundled Python scripts and workspace writes when prompted.
- Run `/reload` after editing the skill in an active session.
