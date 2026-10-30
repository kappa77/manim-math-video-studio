#!/usr/bin/env python3
"""Self-test the skill assets and, optionally, a full smoke render."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from _common import (
    ASSETS,
    PROJECT_DIR,
    load_json,
    validate_brief,
    validate_storyboard,
    validate_template,
)


def _check_assets() -> int:
    failures = 0
    for path in sorted((ASSETS / "templates").glob("*.json")):
        errors, warnings = validate_template(load_json(path))
        if errors:
            failures += 1
            print(f"FAIL template {path.name}")
            for error in errors:
                print(f"  ✗ {error}")
        else:
            print(f"ok   template {path.name}")
        for warning in warnings:
            print(f"  ! {warning}")

    brief = load_json(ASSETS / "brief.example.json")
    errors, warnings = validate_brief(brief)
    if errors:
        failures += 1
        print("FAIL brief.example.json")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("ok   brief.example.json")
    for warning in warnings:
        print(f"  ! {warning}")

    storyboard = load_json(ASSETS / "storyboard.example.json")
    errors, warnings = validate_storyboard(storyboard, brief)
    if errors:
        failures += 1
        print("FAIL storyboard.example.json")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("ok   storyboard.example.json")
    for warning in warnings:
        print(f"  ! {warning}")

    sys.path.insert(0, str(PROJECT_DIR))
    try:
        from manim_lib.expr import compile_expr

        for expression in ("x**2", "sin(x)/x", "exp(-x**2)", "2(x+1)"):
            compile_expr(expression)
        print("ok   expression evaluator")
    except Exception as exc:  # noqa: BLE001
        failures += 1
        print(f"FAIL expression evaluator: {exc}")
    return failures


def _smoke_render() -> int:
    with tempfile.TemporaryDirectory(prefix="manim-math-video-selftest-") as temporary:
        root = Path(temporary)
        brief = load_json(ASSETS / "brief.example.json")
        brief["series"]["episode_number"] = 1
        brief["series"]["title"] = "Smoke Test"
        brief["series"]["slug"] = "smoke-test"
        brief["episode"]["title"] = "Smoke test"
        brief["episode"]["slug"] = "smoke-test"
        brief["episode"]["target_duration_seconds"] = 30
        brief["output"]["quality"] = "draft"
        brief["output"]["voice"]["provider"] = "none"
        brief_path = root / "brief.json"
        brief_path.write_text(json.dumps(brief, indent=2), encoding="utf-8")
        series_dir = root / "series"

        commands = [
            [
                sys.executable,
                str(Path(__file__).with_name("new_episode.py")),
                "--brief",
                str(brief_path),
                "--series-dir",
                str(series_dir),
            ],
        ]
        for command in commands:
            completed = subprocess.run(command, check=False)
            if completed.returncode != 0:
                print(f"FAIL: {' '.join(command)}")
                return 1

        episode_dir = series_dir / "episodes" / "001-smoke-test"
        storyboard = {
            "schema_version": 1,
            "episode_id": "s01e001",
            "episode_slug": "smoke-test",
            "title": "Smoke test",
            "language": "en-US",
            "template": "clean-light",
            "target_duration_seconds": 30,
            "beats": [
                {
                    "id": "title",
                    "kind": "title",
                    "silent": True,
                    "duration_hint": 1.0,
                    "narration": "",
                    "title": "Smoke test",
                },
                {
                    "id": "graph",
                    "kind": "graph",
                    "silent": True,
                    "duration_hint": 2.0,
                    "narration": "",
                    "heading": "A parabola",
                    "graph": {
                        "type": "cartesian",
                        "expr": "x**2",
                        "x_range": [-3, 3, 1],
                        "y_range": [-1, 9, 1],
                        "animation": "draw",
                    },
                },
            ],
        }
        (episode_dir / "storyboard.json").write_text(json.dumps(storyboard, indent=2), encoding="utf-8")

        commands = [
            [sys.executable, str(Path(__file__).with_name("tts.py")), "--episode", str(episode_dir), "--provider", "none"],
            [
                sys.executable,
                str(Path(__file__).with_name("render.py")),
                "--episode",
                str(episode_dir),
                "--quality",
                "draft",
                "--skip-tts",
                "--no-qa",
            ],
        ]
        for command in commands:
            completed = subprocess.run(command, check=False)
            if completed.returncode != 0:
                print(f"FAIL: {' '.join(command)}")
                return 1

        outputs = list((episode_dir / "output").glob("*.mp4"))
        if not outputs:
            print("FAIL: smoke render produced no MP4")
            return 1
        print(f"ok   smoke render: {outputs[0].name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true", help="Run a silent smoke render (requires Manim)")
    args = parser.parse_args(argv)
    failures = _check_assets()
    if failures:
        print(f"\n{failures} asset check(s) failed.")
        return 1
    print("\nAsset checks passed.")
    if args.full:
        print("Running full smoke render...")
        if _smoke_render() != 0:
            return 1
    print("\nSelf-test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
