#!/usr/bin/env python3
"""Validate a brief, a template, or a complete episode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from _common import (
    find_series_root,
    load_json,
    load_template,
    load_voices,
    resolve_episode,
    validate_brief,
    validate_manifest,
    validate_storyboard,
    validate_template,
)


def _print_report(title: str, errors: list[str], warnings: list[str], strict: bool) -> int:
    print(f"\n{title}")
    print("=" * len(title))
    if errors:
        print(f"ERRORS ({len(errors)})")
        for message in errors:
            print(f"  ✗ {message}")
    if warnings:
        print(f"WARNINGS ({len(warnings)})")
        for message in warnings:
            print(f"  ! {message}")
    if not errors and not warnings:
        print("  ✓ No issues found.")
    status = 1 if errors or (strict and warnings) else 0
    print("\nResult:", "FAIL" if status else "PASS")
    return status


def _validate_episode(path: str, strict: bool, as_json: bool) -> int:
    episode_dir = resolve_episode(path)
    brief = load_json(episode_dir / "brief.json")
    storyboard_path = episode_dir / "storyboard.json"
    errors: list[str] = []
    warnings: list[str] = []
    if not storyboard_path.exists():
        errors.append(f"Missing storyboard: {storyboard_path}")
        storyboard = {"beats": []}
    else:
        storyboard = load_json(storyboard_path)

    brief_errors, brief_warnings = validate_brief(brief)
    errors.extend(brief_errors)
    warnings.extend(brief_warnings)

    story_errors, story_warnings = validate_storyboard(
        storyboard,
        brief,
        episode_dir=episode_dir,
    )
    errors.extend(story_errors)
    warnings.extend(story_warnings)

    theme_path = episode_dir / "theme.json"
    if not theme_path.exists():
        errors.append(f"Missing theme snapshot: {theme_path}")
    else:
        theme = load_json(theme_path)
        template_id = str(brief.get("series", {}).get("template", ""))
        try:
            template = load_template(template_id)
            if theme.get("id") != template.get("id"):
                errors.append(
                    f"theme.json id {theme.get('id')!r} does not match template {template.get('id')!r}."
                )
            if theme.get("version") != template.get("version"):
                warnings.append(
                    f"theme.json version {theme.get('version')!r} differs from catalog version "
                    f"{template.get('version')!r} (theme snapshots are intentional)."
                )
        except Exception as exc:
            errors.append(f"Could not load the catalog template: {exc}")

    for name in ("episode.py", "manim_lib"):
        if not (episode_dir / name).exists():
            errors.append(f"Missing {name} in the episode directory.")

    manifest_path = episode_dir / "voice" / "manifest.json"
    if manifest_path.exists():
        manifest = load_json(manifest_path)
        manifest_errors, manifest_warnings = validate_manifest(manifest, storyboard)
        errors.extend(manifest_errors)
        warnings.extend(manifest_warnings)
        for segment in manifest.get("segments", []):
            audio = segment.get("audio")
            if audio:
                audio_path = Path(str(audio))
                if not audio_path.is_absolute():
                    audio_path = episode_dir / audio_path
                if not audio_path.exists():
                    errors.append(f"Voice audio missing for {segment.get('id')!r}: {audio_path}")
    else:
        warnings.append(
            "No voice/manifest.json yet. Run scripts/tts.py before rendering (or use --provider none for a silent draft)."
        )

    series_root = find_series_root(episode_dir)
    if series_root and (series_root / "series.json").exists():
        series = load_json(series_root / "series.json")
        locked = series.get("defaults", {})
        for field in ("template", "quality", "language"):
            brief_value = (
                brief.get("series", {}).get("template")
                if field == "template"
                else brief.get("output", {}).get(field)
            )
            locked_value = locked.get(field)
            if locked_value and brief_value and brief_value != locked_value:
                warnings.append(
                    f"{field} {brief_value!r} differs from the series lock {locked_value!r}."
                )

    if as_json:
        print(json.dumps({"ok": not errors, "episode": str(episode_dir), "errors": errors, "warnings": warnings}, indent=2))
    status = _print_report(f"Episode {episode_dir.name}", errors, warnings, strict)
    return status


def _validate_brief(path: str, strict: bool, as_json: bool) -> int:
    brief = load_json(path)
    errors, warnings = validate_brief(brief)
    if as_json:
        print(json.dumps({"ok": not errors, "brief": str(path), "errors": errors, "warnings": warnings}, indent=2))
    return _print_report(f"Brief {Path(path).name}", errors, warnings, strict)


def _validate_template_file(path: str, strict: bool, as_json: bool) -> int:
    template = load_json(path)
    errors, warnings = validate_template(template)
    if as_json:
        print(json.dumps({"ok": not errors, "template": str(path), "errors": errors, "warnings": warnings}, indent=2))
    return _print_report(f"Template {path}", errors, warnings, strict)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--brief", help="Path to brief.json")
    group.add_argument("--episode", help="Path to an episode directory")
    group.add_argument("--template", help="Path to a theme/template JSON file")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report")
    args = parser.parse_args(argv)
    if args.brief:
        return _validate_brief(args.brief, args.strict, args.json)
    if args.episode:
        return _validate_episode(args.episode, args.strict, args.json)
    return _validate_template_file(args.template, args.strict, args.json)


if __name__ == "__main__":
    sys.exit(main())
