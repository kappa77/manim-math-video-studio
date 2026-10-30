# Claude Code version

This build is the Agent Skills version for Claude Code. It keeps the standard `name`, `description`, `license`, and `metadata` fields and adds Claude Code's `argument-hint`. The workflow stays inline because it is interview-driven.

Generated skill: `dist/claude/skills/manim-math-video/`.

## Install

Personal, available in every project:

```bash
mkdir -p ~/.claude/skills
cp -R dist/claude/skills/manim-math-video ~/.claude/skills/
```

Project, committed with the repository:

```bash
mkdir -p .claude/skills
cp -R dist/claude/skills/manim-math-video .claude/skills/
```

On Windows PowerShell, replace the copy step with:

```powershell
Copy-Item -Recurse -Force dist/claude/skills/manim-math-video "$HOME/.claude/skills/"
```

## Use

```text
/manim-math-video Why does the derivative of x² equal 2x?
```

Claude can also choose the skill automatically when the request matches its description. Run `/doctor` if the command does not appear. After editing `SKILL.md`, restart the session.

## Notes

- The skill does not pre-approve tools. Approve the bundled Python scripts and workspace writes when Claude asks. Add `allowed-tools` only if you accept the resulting pre-approval scope.
- Keep `context` unset. A forked context would hide the interview from the main conversation.
- Add `disable-model-invocation: true` to require `/manim-math-video`; add `user-invocable: false` to hide it from the slash menu while still allowing automatic loading.
- The full directory is required: `scripts/`, `references/`, and `assets/` are referenced by `SKILL.md`.
