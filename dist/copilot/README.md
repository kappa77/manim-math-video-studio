# GitHub Copilot version

This build is the Agent Skills version for GitHub Copilot in VS Code, the Copilot CLI, the Copilot app, and the Copilot cloud agent. The frontmatter keeps the fields Copilot documents: `name`, `description`, and `argument-hint`.

Generated skill: `dist/copilot/skills/manim-math-video/`.

## Install

Project scope, shared with everyone who uses the repository:

```bash
mkdir -p .github/skills
cp -R dist/copilot/skills/manim-math-video .github/skills/
```

Personal scope:

```bash
mkdir -p ~/.copilot/skills
cp -R dist/copilot/skills/manim-math-video ~/.copilot/skills/
```

VS Code also discovers `.claude/skills/` and `.agents/skills/`. In a repository, prefer `.github/skills/` so Copilot CLI and the Copilot app see the same skill.

## Use

```text
/manim-math-video Why does the derivative of x² equal 2x?
```

The skill is also available for automatic loading when the request matches its description. In the Copilot CLI:

```bash
copilot skill list
```

`copilot skill add <directory>` registers a directory of skills in place. To install only the `SKILL.md` from a file, use `copilot skill add ./SKILL.md`; that does not copy the supporting scripts and references, so prefer copying the whole directory.

## Notes

- The directory name must match the frontmatter `name`, or Copilot silently ignores the skill.
- Keep the default inline context. The interview relies on the parent conversation; do not set `context: fork`.
- Add `disable-model-invocation: true` to require `/manim-math-video`; add `user-invocable: false` to hide it from the slash menu while still allowing automatic loading.
- Copilot opens supporting files only when `SKILL.md` references them. Install the complete directory.
