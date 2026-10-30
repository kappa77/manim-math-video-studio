#!/usr/bin/env python3
"""Build and install platform-specific copies of the skill.

The canonical skill lives in ``manim-math-video/``. Each platform gets a
complete copy under ``dist/<platform>/skills/manim-math-video/`` with a
platform-specific frontmatter and usage section. Everything else is shared.

Examples:
    python platforms/build.py
    python platforms/build.py --check
    python platforms/build.py --platform claude --platform pi
    python platforms/build.py --install
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS_DIR = ROOT / "platforms"
MANIFEST_PATH = PLATFORMS_DIR / "manifest.json"
SOURCE = ROOT / "manim-math-video"
DIST = ROOT / "dist"

USAGE_START = "<!-- platform-usage:start -->"
USAGE_END = "<!-- platform-usage:end -->"

EXCLUDED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".tmp_manim",
    ".venv",
    "media",
    "output",
    "qa",
    "voice",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".part"}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db"}
TEXT_SUFFIXES = {
    ".md",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".tmpl",
    ".txt",
    ".srt",
    ".css",
    ".html",
}


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


MANIFEST = load_manifest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def split_frontmatter(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with a YAML frontmatter block")
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return lines[1:index], lines[index + 1 :]
    raise ValueError("SKILL.md frontmatter is not closed with ---")


def parse_fields(lines: list[str]) -> list[tuple[str, list[str]]]:
    fields: list[tuple[str, list[str]]] = []
    for line in lines:
        if line.strip() and not line[0].isspace() and ":" in line:
            key = line.split(":", 1)[0].strip()
            fields.append((key, [line]))
        else:
            if not fields:
                raise ValueError(f"frontmatter line without a key: {line!r}")
            fields[-1][1].append(line)
    return fields


def render_frontmatter(
    original: list[str],
    drop: list[str],
    add: list[str],
) -> list[str]:
    fields = parse_fields(original)
    rendered = ["---\n"]
    for key, block in fields:
        if key in drop:
            continue
        rendered.extend(block)
    for line in add:
        rendered.append(line.rstrip("\n") + "\n")
    rendered.append("---\n")
    return rendered


def replace_usage(text: str, usage: str) -> str:
    start = text.find(USAGE_START)
    end = text.find(USAGE_END)
    if start < 0 or end < 0 or end < start:
        raise ValueError("SKILL.md is missing the platform-usage markers")
    end += len(USAGE_END)
    return (
        text[:start]
        + USAGE_START
        + "\n"
        + usage.strip()
        + "\n"
        + USAGE_END
        + text[end:]
    )


def iter_source_files(include_examples: bool):
    for path in sorted(SOURCE.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(SOURCE)
        if any(part in EXCLUDED_DIRS for part in relative.parts):
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if path.name in EXCLUDED_FILES:
            continue
        if not include_examples and relative.parts[0] == "examples":
            continue
        yield path, relative


def copy_skill(
    platform: str,
    config: dict[str, Any],
    destination: Path,
    *,
    include_examples: bool,
) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    for source, relative in iter_source_files(include_examples):
        if relative.parts[0] == "agents" and not config.get("include_agents"):
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        if target.suffix.lower() in TEXT_SUFFIXES:
            data = target.read_bytes().replace(b"\r\n", b"\n")
            target.write_bytes(data)

    license_source = ROOT / "LICENSE"
    if license_source.exists():
        shutil.copy2(license_source, destination / "LICENSE")

    platform_install = PLATFORMS_DIR / platform / "INSTALL.md"
    if platform_install.exists():
        target = destination / "INSTALL.md"
        shutil.copy2(platform_install, target)
        data = target.read_bytes().replace(b"\r\n", b"\n")
        target.write_bytes(data)

    # The platform may ship its own agents/openai.yaml.
    platform_agents = PLATFORMS_DIR / platform / "agents" / "openai.yaml"
    if config.get("include_agents") and platform_agents.exists():
        target = destination / "agents" / "openai.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(platform_agents, target)
        data = target.read_bytes().replace(b"\r\n", b"\n")
        target.write_bytes(data)

    skill_path = destination / "SKILL.md"
    text = read_text(skill_path)
    frontmatter, body = split_frontmatter(text)
    fields = parse_fields(frontmatter)
    declared_name = next(
        (block[0].split(":", 1)[1].strip().strip('"') for key, block in fields if key == "name"),
        "",
    )
    expected_name = config_name(config)
    if declared_name != expected_name:
        raise ValueError(
            f"{platform}: frontmatter name {declared_name!r} does not match {expected_name!r}"
        )

    usage_path = PLATFORMS_DIR / platform / "usage.md"
    usage = read_text(usage_path)

    rendered_frontmatter = render_frontmatter(
        frontmatter,
        list(config.get("frontmatter_drop", [])),
        list(config.get("frontmatter_add", [])),
    )
    rendered = "".join(rendered_frontmatter) + "".join(body)
    rendered = replace_usage(rendered, usage)
    skill_path.write_text(rendered, encoding="utf-8", newline="\n")


def config_name(config: dict[str, Any]) -> str:
    return str(config.get("skill_name") or MANIFEST["skill"])


def render_readme(platform: str, config: dict[str, Any]) -> str:
    source = PLATFORMS_DIR / platform / "README.md"
    text = read_text(source)
    return text.replace("{{SKILL}}", MANIFEST["skill"])


def build_platforms(
    platforms: list[str],
    target_root: Path,
    *,
    include_examples: bool,
) -> None:
    for platform in platforms:
        if platform not in MANIFEST["platforms"]:
            raise SystemExit(f"Unknown platform: {platform}")
        config = MANIFEST["platforms"][platform]
        skill_dir = target_root / platform / "skills" / MANIFEST["skill"]
        copy_skill(platform, config, skill_dir, include_examples=include_examples)
        platform_root = target_root / platform
        (platform_root / "README.md").write_text(
            render_readme(platform, config),
            encoding="utf-8",
            newline="\n",
        )
        platform_install = PLATFORMS_DIR / platform / "INSTALL.md"
        if platform_install.exists():
            target = platform_root / "INSTALL.md"
            shutil.copy2(platform_install, target)
            data = target.read_bytes().replace(b"\r\n", b"\n")
            target.write_bytes(data)

    rows = [
        "# Platform builds",
        "",
        "Generated by `python platforms/build.py`. Edit `manim-math-video/` and "
        "`platforms/<platform>/`, then rebuild; do not edit these copies by hand.",
        "",
        "| Platform | Skill directory | Invocation |",
        "|---|---|---|",
    ]
    invocations = {
        "claude": "`/manim-math-video`",
        "codex": "`$manim-math-video`",
        "copilot": "`/manim-math-video`",
        "pi": "`/skill:manim-math-video`",
    }
    for platform in MANIFEST["platforms"]:
        config = MANIFEST["platforms"][platform]
        rows.append(
            f"| {config['label']} | `{platform}/skills/{MANIFEST['skill']}/` | "
            f"{invocations.get(platform, '')} |"
        )
    rows.extend(
        [
            "",
            "Install the `skills/` tree into the platform's skill root. Each "
            "platform directory includes `README.md` (overview) and `INSTALL.md` "
            "(personal/project commands, verification, update, and uninstall).",
            "",
        ]
    )
    (target_root / "README.md").write_text("\n".join(rows), encoding="utf-8", newline="\n")


def snapshot(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        values[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def check_build(platforms: list[str], *, include_examples: bool) -> int:
    if not DIST.exists():
        print("dist/ does not exist. Run: python platforms/build.py", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory(prefix="manim-platforms-") as temporary:
        expected_root = Path(temporary) / "dist"
        build_platforms(platforms, expected_root, include_examples=include_examples)
        expected = snapshot(expected_root)
        actual = snapshot(DIST)
        prefixes = tuple(f"{platform}/" for platform in platforms)
        if len(platforms) != len(MANIFEST["platforms"]):
            expected = {
                path: digest
                for path, digest in expected.items()
                if path.startswith(prefixes) or path == "README.md"
            }
            actual = {
                path: digest
                for path, digest in actual.items()
                if path.startswith(prefixes) or path == "README.md"
            }
        if expected == actual:
            print("Platform builds are up to date.")
            for platform in platforms:
                print(f"  ok {platform}")
            return 0
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        changed = sorted(
            path for path in set(expected) & set(actual) if expected[path] != actual[path]
        )
        for path in missing:
            print(f"  missing {path}")
        for path in extra:
            print(f"  extra   {path}")
        for path in changed:
            print(f"  changed {path}")
        print("Rebuild with: python platforms/build.py", file=sys.stderr)
        return 1


def install(platforms: list[str], install_root: str | None) -> int:
    failures = 0
    for platform in platforms:
        source = DIST / platform / "skills" / MANIFEST["skill"]
        if not source.exists():
            print(f"Missing build for {platform}; run build first.", file=sys.stderr)
            failures += 1
            continue
        if install_root:
            root = Path(install_root).expanduser()
        else:
            root = Path(MANIFEST["platforms"][platform]["install_root"]).expanduser()
        target = root / MANIFEST["skill"]
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
        print(f"installed {platform}: {target}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--platform",
        action="append",
        choices=sorted(MANIFEST["platforms"]),
        help="Build only this platform (repeatable; default: all)",
    )
    parser.add_argument("--check", action="store_true", help="Verify dist/ is current")
    parser.add_argument("--clean", action="store_true", help="Remove dist/")
    parser.add_argument("--install", action="store_true", help="Copy builds into skill roots")
    parser.add_argument(
        "--install-root",
        help="Override the skill root for --install (useful for tests)",
    )
    parser.add_argument(
        "--no-examples",
        action="store_true",
        help="Exclude the examples/ directory from generated builds",
    )
    args = parser.parse_args(argv)

    platforms = args.platform or list(MANIFEST["platforms"])
    include_examples = not args.no_examples

    if args.clean:
        if DIST.exists():
            shutil.rmtree(DIST)
            print(f"removed {DIST}")
        return 0

    if args.check:
        return check_build(platforms, include_examples=include_examples)

    build_platforms(platforms, DIST, include_examples=include_examples)
    for platform in platforms:
        print(f"built {platform}: {DIST / platform / 'skills' / MANIFEST['skill']}")

    if args.install:
        return install(platforms, args.install_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
