## Using this skill in Claude Code

Requirements: Python 3.10+, Manim Community 0.19+, edge-tts 6+; LaTeX for equation beats; PyAV or ffmpeg for audio conversion. Run `scripts/check_env.py` before rendering. Installing the skill does not install dependencies.

Resolve scripts, assets, and references relative to this `SKILL.md`, even when the working directory is another project. Use absolute paths for briefs and episode directories. Keep generated series and media in the user's workspace, outside the installed skill directory. Ask questions in the user's language; set the narration language separately in the brief.

Before running the pipeline, verify that this directory contains `scripts/`, `references/`, and `assets/`. If it is incomplete, follow `INSTALL.md` in the same directory for personal/project install, update, and uninstall commands.

- **Install:** project `.claude/skills/manim-math-video/`; personal `~/.claude/skills/manim-math-video/`.
- **Invoke:** `/manim-math-video <topic, brief, or episode directory>`. Claude can also load it automatically when the task matches the description.
- **Context:** keep this skill inline. The workflow is interactive, so do not set `context: fork`.
- **Permissions:** this skill does not pre-approve tools. Approve the `Bash` calls that run the bundled Python scripts, and `Write`/`Edit` for files in the user's workspace.
- **Supporting files:** read only the references needed for the current step. The files under `references/`, `assets/`, and `scripts/` are part of the skill and must be installed with it.
