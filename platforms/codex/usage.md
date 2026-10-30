## Using this skill in Codex

Requirements: Python 3.10+, Manim Community 0.19+, edge-tts 6+; LaTeX for equation beats; PyAV or ffmpeg for audio conversion. Run `scripts/check_env.py` before rendering. Installing the skill does not install dependencies.

Resolve scripts, assets, and references relative to this `SKILL.md`, even when the working directory is another project. Use absolute paths for briefs and episode directories. Keep generated series and media in the user's workspace, outside the installed skill directory. Ask questions in the user's language; set the narration language separately in the brief.

Before running the pipeline, verify that this directory contains `scripts/`, `references/`, and `assets/`. If it is incomplete, follow `INSTALL.md` in the same directory for personal/project install, update, and uninstall commands.

- **Install:** personal `~/.agents/skills/manim-math-video/` is the current Agent Skills location; Codex desktop builds may use `~/.codex/skills/manim-math-video/` instead. Project skills go in `<repo>/.agents/skills/manim-math-video/`.
- **Invoke:** `$manim-math-video <topic>` or use `/skills`. In the ChatGPT desktop app, type `@` and choose **Manim Video Studio**. Codex can also load the skill implicitly when the description matches the task.
- **Metadata:** `agents/openai.yaml` supplies the display name, short description, and default prompt. Set `policy.allow_implicit_invocation: false` there if the skill should be explicit-invocation only.
- **Workspace:** keep the series and generated media outside the installed skill directory so an update to the skill never touches the user's videos.
