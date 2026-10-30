#!/usr/bin/env python3
"""Create a series and scaffold a new episode from an approved brief."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

from _common import (
    ASSETS,
    ID_RE,
    PROJECT_DIR,
    QUALITY_PRESETS,
    atomic_write_json,
    default_voice,
    episode_dir_name,
    episode_id,
    load_json,
    load_template,
    load_voices,
    now_iso,
    resolve_output,
    slugify,
    validate_brief,
    write_text,
)


def _skeleton_beat(kind: str, index: int, brief: dict[str, Any]) -> dict[str, Any]:
    beat: dict[str, Any] = {
        "id": f"{kind}-{index}" if index > 1 else kind,
        "kind": kind,
        "narration": "",
        "notes": f"TODO: write the {kind} beat and its visual intent.",
    }
    if kind == "title":
        beat.update(
            {
                "title": brief.get("episode", {}).get("title", "TODO: episode title"),
                "subtitle": "TODO: subtitle or promise",
                "narration": "",
            }
        )
    elif kind == "section":
        beat.update({"heading": "TODO: section heading", "narration": ""})
    elif kind == "bullets":
        beat.update({"heading": "TODO: heading", "items": ["TODO: first point"], "narration": ""})
    elif kind == "equation":
        beat.update(
            {
                "heading": "TODO: equation heading",
                "latex": "TODO",
                "narration": "",
            }
        )
    elif kind == "graph":
        beat.update(
            {
                "heading": "TODO: graph heading",
                "graph": {
                    "type": "cartesian",
                    "x_range": [-3, 3, 1],
                    "y_range": [-1, 9, 1],
                    "x_label": "x",
                    "y_label": "f(x)",
                    "plots": [{"expr": "x**2", "color_role": "primary", "label": "f(x) = x²"}],
                    "annotations": [],
                    "animation": "draw",
                },
                "narration": "",
            }
        )
    elif kind == "compare":
        beat.update(
            {
                "heading": "TODO: comparison heading",
                "left": {"heading": "TODO: left", "items": ["TODO"], "role": "danger"},
                "right": {"heading": "TODO: right", "items": ["TODO"], "role": "success"},
                "narration": "",
            }
        )
    elif kind == "recap":
        beat.update({"heading": "TODO: recap heading", "items": ["TODO: takeaway"], "narration": ""})
    elif kind == "outro":
        beat.update(
            {
                "heading": "Next question",
                "next": "TODO: next episode question",
                "cta": "TODO: call to action",
                "narration": "",
            }
        )
    elif kind == "quote":
        beat.update({"quote": "TODO: real quote", "attribution": "TODO: attribution", "narration": ""})
    elif kind == "custom":
        beat.update({"notes": "TODO: custom visual; override custom_beat in episode.py.", "narration": ""})
    return beat


def _storyboard_skeleton(brief: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    series = brief["series"]
    episode = brief["episode"]
    kinds = list(template.get("story", {}).get("beats") or ["title", "section", "graph", "recap", "outro"])
    if episode.get("rigor") in {"explanation", "narrative", "procedure", "analysis"}:
        # Templates define a visual style; general subjects do not require math beats.
        kinds = [{"equation": "bullets", "graph": "section"}.get(kind, kind) for kind in kinds]
    counts: dict[str, int] = {}
    beats: list[dict[str, Any]] = []
    for kind in kinds:
        counts[kind] = counts.get(kind, 0) + 1
        beats.append(_skeleton_beat(kind, counts[kind], brief))
    return {
        "schema_version": 1,
        "episode_id": episode_id(series["season"], series["episode_number"]),
        "episode_slug": episode["slug"],
        "title": episode["title"],
        "language": brief["output"]["language"],
        "template": series["template"],
        "target_duration_seconds": episode.get("target_duration_seconds", 420),
        "beats": beats,
    }


def _script_template(brief: dict[str, Any]) -> str:
    series = brief["series"]
    episode = brief["episode"]
    return f"""# {episode['title']}

**Series:** {series['title']} · S{int(series['season']):02d}E{int(series['episode_number']):03d}
**Thesis:** {episode.get('thesis', 'TODO')}
**Audience:** {episode.get('audience', 'TODO')}
**Target:** {episode.get('target_duration_seconds', 0)} seconds
**Template:** {series.get('template', 'TODO')}
**Quality:** {brief['output'].get('quality', 'standard')}
**Language:** {brief['output'].get('language', 'TODO')}
**Voice:** {brief['output'].get('voice', {}).get('id', 'TODO')}

## Content progression

{chr(10).join(f"{i}. {point}" for i, point in enumerate(episode.get('key_points', []), start=1))}

## Script

TODO: fill `storyboard.json`; then run:
```bash
python scripts/storyboard_to_script.py --episode .
```

## Accuracy checklist

- [ ] Facts, quotations, and claims verified; interpretations clearly identified.
- [ ] Chronology, process steps, or narrative continuity checked as applicable.
- [ ] Terminology consistent with the series; formulas checked when present.
- [ ] Sources real and cited.
- [ ] Pronunciations checked.
"""


def _merge_series_defaults(brief: dict[str, Any], series: dict[str, Any]) -> dict[str, Any]:
    defaults = series.get("defaults", {})
    output = brief.setdefault("output", {})
    if not output.get("quality") and defaults.get("quality"):
        output["quality"] = defaults["quality"]
    if not output.get("language") and defaults.get("language"):
        output["language"] = defaults["language"]
    voice = output.setdefault("voice", {})
    locked_voice = defaults.get("voice") or {}
    for key in ("provider", "id", "style", "rate", "pitch", "volume"):
        if not voice.get(key) and locked_voice.get(key):
            voice[key] = locked_voice[key]
    return brief


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief", required=True, help="Path to the approved brief.json")
    parser.add_argument("--series-dir", required=True, help="Series root directory")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing episode scaffold")
    parser.add_argument(
        "--allow-style-drift",
        metavar="REASON",
        help="Allow a template/voice/language/quality mismatch with the series, recording REASON",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    args = parser.parse_args(argv)

    brief_path = Path(args.brief).resolve()
    brief = load_json(brief_path)
    brief.setdefault("series", {})
    brief.setdefault("episode", {})
    brief.setdefault("output", {})
    brief.setdefault("accuracy", {})

    series = brief["series"]
    episode = brief["episode"]

    series_root = Path(args.series_dir).resolve()
    series_json_path = series_root / "series.json"
    existing_series = load_json(series_json_path) if series_json_path.exists() else None

    series.setdefault("season", 1)
    series.setdefault("episode_number", 1)
    series.setdefault("title", "Untitled series")
    series.setdefault("visual_motif", None)
    series.setdefault("consistency_note", None)
    episode.setdefault("title", "Untitled episode")

    # Inherit missing series-level settings before resolving defaults.
    if existing_series:
        locked_series = existing_series.get("series", {})
        if series.get("title") in (None, "", "Untitled series"):
            series["title"] = locked_series.get("title", series["title"])
        if not series.get("premise"):
            series["premise"] = locked_series.get("premise", series.get("premise", ""))
        if not series.get("audience"):
            series["audience"] = locked_series.get("audience", series.get("audience", ""))
        if not series.get("visual_motif"):
            series["visual_motif"] = locked_series.get("visual_motif")
        if not series.get("template"):
            series["template"] = locked_series.get("template")
        brief = _merge_series_defaults(brief, existing_series)

    if not series.get("premise"):
        series["premise"] = episode.get("thesis", "")
    if not series.get("audience"):
        series["audience"] = episode.get("audience", "")
    if not episode.get("slug"):
        episode["slug"] = slugify(episode["title"])
    if not series.get("slug"):
        series["slug"] = slugify(series["title"])
    if not series.get("template"):
        series["template"] = "clean-light"
    if not ID_RE.match(str(series["template"])):
        print(
            f"Invalid template id {series['template']!r}; use lowercase letters, numbers, and hyphens.",
            file=sys.stderr,
        )
        return 2

    try:
        template = load_template(str(series["template"]))
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    brief["output"] = resolve_output(brief)
    voices = load_voices()
    locale = brief["output"]["language"]
    if not brief["output"]["voice"].get("id"):
        brief["output"]["voice"]["id"] = default_voice(locale, voices)

    errors, warnings = validate_brief(brief)
    if errors:
        print("The brief is not ready:\n", file=sys.stderr)
        for message in errors:
            print(f"  ✗ {message}", file=sys.stderr)
        return 2
    for message in warnings:
        print(f"  ! {message}")

    episode_name = episode_dir_name(brief)
    episode_dir = series_root / "episodes" / episode_name

    if existing_series:
        defaults = existing_series.get("defaults", {})
        locked_series = existing_series.get("series", {})
        mismatches: list[str] = []
        locked_template = locked_series.get("template") or defaults.get("template")
        if locked_template and locked_template != series["template"]:
            mismatches.append(f"template {series['template']!r} vs series {locked_template!r}")
        if defaults.get("quality") and defaults["quality"] != brief["output"]["quality"]:
            mismatches.append(f"quality {brief['output']['quality']!r} vs series {defaults['quality']!r}")
        if defaults.get("language") and defaults["language"] != brief["output"]["language"]:
            mismatches.append(f"language {brief['output']['language']!r} vs series {defaults['language']!r}")
        locked_voice = (defaults.get("voice") or {}).get("id")
        if locked_voice and locked_voice != brief["output"]["voice"]["id"]:
            mismatches.append(f"voice {brief['output']['voice']['id']!r} vs series {locked_voice!r}")
        if mismatches and not args.allow_style_drift:
            print("This brief drifts from the series lock:", file=sys.stderr)
            for mismatch in mismatches:
                print(f"  ✗ {mismatch}", file=sys.stderr)
            print(
                "\nReuse the series settings, start a new series, or pass --allow-style-drift "
                '"reason" after explicit approval.',
                file=sys.stderr,
            )
            return 2
        if mismatches and args.allow_style_drift:
            series["consistency_note"] = args.allow_style_drift
            brief.setdefault("series", {})["consistency_note"] = args.allow_style_drift
            existing_series.setdefault("changes", []).append(
                {
                    "at": now_iso(),
                    "episode": episode_id(series["season"], series["episode_number"]),
                    "reason": args.allow_style_drift,
                    "mismatches": mismatches,
                }
            )
            print(f"  ! Allowing deliberate style drift: {args.allow_style_drift}")

        for registered in existing_series.get("episodes", []):
            if registered.get("id") == episode_id(series["season"], series["episode_number"]):
                registered_path = Path(registered.get("path", ""))
                if registered_path.resolve() != episode_dir and not args.force:
                    print(
                        f"Episode id {episode_id(series['season'], series['episode_number'])} "
                        f"is already registered at {registered_path}.",
                        file=sys.stderr,
                    )
                    return 2

    if episode_dir.exists() and any(episode_dir.iterdir()) and not args.force:
        print(f"Episode directory already exists: {episode_dir}. Use --force to overwrite the scaffold.", file=sys.stderr)
        return 2

    actions = [
        f"series root: {series_root}",
        f"episode: {episode_dir}",
        f"template: {template['id']} v{template.get('version', '?')}",
        f"quality: {brief['output']['quality']}",
        f"language: {brief['output']['language']}",
        f"voice: {brief['output']['voice']['id']} ({brief['output']['voice'].get('style', '')})",
    ]
    print("Scaffolding:")
    for action in actions:
        print(f"  - {action}")
    if args.dry_run:
        print("\nDry run: no files written.")
        return 0

    episode_dir.mkdir(parents=True, exist_ok=True)
    for subdir in ("voice", "output", "qa", "assets"):
        (episode_dir / subdir).mkdir(parents=True, exist_ok=True)

    # Standalone runtime, copied so the episode remains renderable if the skill moves.
    target_lib = episode_dir / "manim_lib"
    if target_lib.exists():
        shutil.rmtree(target_lib)
    shutil.copytree(
        PROJECT_DIR / "manim_lib",
        target_lib,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    atomic_write_json(episode_dir / "brief.json", brief)
    theme_snapshot = dict(template)
    theme_snapshot["aspect_ratio"] = str(episode.get("aspect_ratio", template.get("aspect_ratio", "16:9")))
    atomic_write_json(episode_dir / "theme.json", theme_snapshot)
    atomic_write_json(episode_dir / "storyboard.json", _storyboard_skeleton(brief, template))
    write_text(episode_dir / "script.md", _script_template(brief))
    write_text(episode_dir / "episode.py", (PROJECT_DIR / "episode.py.tmpl").read_text(encoding="utf-8"))
    readme = (PROJECT_DIR / "README.md.tmpl").read_text(encoding="utf-8")
    replacements = {
        "{{SERIES_TITLE}}": str(series["title"]),
        "{{EPISODE_TITLE}}": str(episode["title"]),
        "{{EPISODE_ID}}": episode_id(series["season"], series["episode_number"]),
        "{{TEMPLATE}}": str(series["template"]),
        "{{QUALITY}}": str(brief["output"]["quality"]),
        "{{LANGUAGE}}": str(brief["output"]["language"]),
        "{{VOICE}}": str(brief["output"]["voice"]["id"]),
        "{{VOICE_STYLE}}": str(brief["output"]["voice"].get("style", "")),
        "{{TARGET_DURATION}}": str(episode.get("target_duration_seconds", "")),
        "{{EPISODE_PATH}}": str(episode_dir),
    }
    for source, target in replacements.items():
        readme = readme.replace(source, target)
    write_text(episode_dir / "README.md", readme)

    # Series registry.
    if existing_series is None:
        existing_series = {
            "schema_version": 1,
            "created_at": now_iso(),
            "series": {
                "title": series["title"],
                "slug": series["slug"],
                "season": series["season"],
                "premise": series.get("premise", ""),
                "audience": series.get("audience", ""),
                "visual_motif": series.get("visual_motif"),
                "template": series["template"],
                "template_version": template.get("version"),
            },
            "defaults": {
                "quality": brief["output"]["quality"],
                "language": brief["output"]["language"],
                "voice": {
                    key: brief["output"]["voice"].get(key)
                    for key in ("provider", "id", "style", "rate", "pitch", "volume")
                },
            },
            "episodes": [],
        }
    existing_series.setdefault("episodes", [])
    existing_series["updated_at"] = now_iso()
    existing_series["episodes"] = [
        entry
        for entry in existing_series["episodes"]
        if entry.get("id") != episode_id(series["season"], series["episode_number"])
    ]
    existing_series["episodes"].append(
        {
            "id": episode_id(series["season"], series["episode_number"]),
            "season": series["season"],
            "number": series["episode_number"],
            "title": episode["title"],
            "slug": episode["slug"],
            "path": str(episode_dir.relative_to(series_root)).replace("\\", "/"),
            "template": series["template"],
            "quality": brief["output"]["quality"],
            "language": brief["output"]["language"],
            "voice": brief["output"]["voice"]["id"],
            "status": "draft",
            "created_at": now_iso(),
        }
    )
    existing_series["episodes"].sort(key=lambda entry: (entry.get("season", 0), entry.get("number", 0)))
    atomic_write_json(series_json_path, existing_series)

    print(f"\nCreated {episode_dir}")
    print("\nNext:")
    print(f"  1. Fill {episode_dir / 'storyboard.json'} and script.md")
    print(f"  2. python scripts/validate.py --episode \"{episode_dir}\"")
    print(f"  3. python scripts/tts.py --episode \"{episode_dir}\"")
    print(f"  4. python scripts/render.py --episode \"{episode_dir}\" --quality draft")
    return 0


if __name__ == "__main__":
    sys.exit(main())
