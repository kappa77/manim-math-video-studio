## Using this skill in Pi

Requirements: Python 3.10+, Manim Community 0.19+, edge-tts 6+; LaTeX for equation beats; PyAV or ffmpeg for audio conversion. Run `scripts/check_env.py` before rendering. Installing the skill does not install dependencies.

Resolve scripts, assets, and references relative to this `SKILL.md`, even when the working directory is another project. Use absolute paths for briefs and episode directories. Keep generated series and media in the user's workspace, outside the installed skill directory. Ask questions in the user's language; set the narration language separately in the brief.

Before running the pipeline, verify that this directory contains `scripts/`, `references/`, and `assets/`. If it is incomplete, follow `INSTALL.md` in the same directory for personal/project install, update, and uninstall commands.

- **Install:** personal `~/.pi/agent/skills/manim-math-video/` or `~/.agents/skills/manim-math-video/`; project `.pi/skills/manim-math-video/` or `.agents/skills/manim-math-video/`. Pi scans directories containing `SKILL.md` recursively.
- **Invoke:** `/skill:manim-math-video <topic, brief, or episode directory>`. Pi can also load it automatically when the description matches the task.
- **Reload:** run `/reload` after editing the skill in an active session.
- **Permissions:** Pi asks before risky commands. Approve the bundled Python scripts and workspace writes when prompted.
