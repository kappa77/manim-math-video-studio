# Pi version

This build is the Agent Skills version for Pi. It keeps the standard `name`, `description`, `license`, and `metadata` fields and uses Pi's `/skill:name` command.

Generated skill: `dist/pi/skills/manim-math-video/`.

## Install

Personal:

```bash
mkdir -p ~/.pi/agent/skills
cp -R dist/pi/skills/manim-math-video ~/.pi/agent/skills/
```

The Agent Skills standard location also works:

```bash
mkdir -p ~/.agents/skills
cp -R dist/pi/skills/manim-math-video ~/.agents/skills/
```

Project scope, either `.pi/skills/` or `.agents/skills/`:

```bash
mkdir -p .pi/skills
cp -R dist/pi/skills/manim-math-video .pi/skills/
```

## Use

```text
/skill:manim-math-video Why does the derivative of x² equal 2x?
```

Pi can also load the skill automatically when the description matches the task. Run `/reload` after editing the skill in an active session.

## Notes

- Keep the installed directory intact; `scripts/`, `references/`, and `assets/` are part of the skill.
- Add `disable-model-invocation: true` to the frontmatter to require `/skill:manim-math-video`; Pi still allows the explicit command.
- Pi asks before risky commands. Approve the bundled Python scripts and workspace writes when prompted.
