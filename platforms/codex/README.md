# Codex version

This build is the Agent Skills version for Codex. It includes `agents/openai.yaml` for the Codex/ChatGPT skill interface and keeps the standard `name`, `description`, `license`, and `metadata` fields.

Generated skill: `dist/codex/skills/manim-math-video/`.

## Install

Personal, current Agent Skills location:

```bash
mkdir -p ~/.agents/skills
cp -R dist/codex/skills/manim-math-video ~/.agents/skills/
```

Codex desktop builds that use the `.codex` directory can install there instead:

```bash
mkdir -p ~/.codex/skills
cp -R dist/codex/skills/manim-math-video ~/.codex/skills/
```

Project scope:

```bash
mkdir -p .agents/skills
cp -R dist/codex/skills/manim-math-video .agents/skills/
```

## Use

```text
$manim-math-video Why does the derivative of x² equal 2x?
```

Or open `/skills` and choose **Manim Video Studio**. In the ChatGPT desktop app, type `@` and select the skill. Codex can also invoke it implicitly when the task matches the description.

## Metadata

`agents/openai.yaml` controls the display name, short description, and default prompt. To require explicit `$manim-math-video` invocation, add:

```yaml
policy:
  allow_implicit_invocation: false
```

Restart Codex if a skill update does not appear. Use `[[skills.config]]` in `~/.codex/config.toml` to disable a skill without deleting it.
