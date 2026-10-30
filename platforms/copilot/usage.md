## Using this skill in GitHub Copilot

Requirements: Python 3.10+, Manim Community 0.19+, edge-tts 6+; LaTeX for equation beats; PyAV or ffmpeg for audio conversion. Run `scripts/check_env.py` before rendering. Installing the skill does not install dependencies.

Resolve scripts, assets, and references relative to this `SKILL.md`, even when the working directory is another project. Use absolute paths for briefs and episode directories. Keep generated series and media in the user's workspace, outside the installed skill directory. Ask questions in the user's language; set the narration language separately in the brief.

Before running the pipeline, verify that this directory contains `scripts/`, `references/`, and `assets/`. If it is incomplete, follow `INSTALL.md` in the same directory for personal/project install, update, and uninstall commands.

- **Install (project):** `.github/skills/manim-math-video/`; `.claude/skills/` and `.agents/skills/` are also discovered. **Personal:** `~/.copilot/skills/manim-math-video/` or `~/.agents/skills/manim-math-video/`.
- **Invoke:** `/manim-math-video <topic, brief, or episode directory>` in Copilot Chat, the Copilot CLI, or the Copilot app. Copilot can also load it automatically when relevant.
- **Keep the directory name:** it must match the `name` field in the frontmatter, or Copilot silently ignores the skill.
- **Context:** leave the default inline context. Do not set `context: fork`; the interview needs the parent conversation.
- **Copilot CLI:** `copilot skill list` shows discovered skills. `copilot skill add <directory>` registers a directory of skills instead of copying it.
- **Supporting files:** Copilot loads a referenced file only when the instructions point to it. Keep the relative links in `SKILL.md` intact and install the whole skill directory, not just `SKILL.md`.
