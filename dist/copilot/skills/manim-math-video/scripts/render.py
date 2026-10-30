#!/usr/bin/env python3
"""Render a scaffolded episode, copy deliverables, and run QA."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from _common import (
    QUALITY_PRESETS,
    atomic_write_json,
    episode_id,
    find_manim_executable,
    latex_available,
    load_json,
    now_iso,
    output_basename,
    render_dimensions,
    resolve_episode,
    validate_brief,
    validate_manifest,
    validate_storyboard,
)


def _manim_command(version: tuple[int, ...]) -> list[str]:
    manim = find_manim_executable()
    if not manim:
        raise FileNotFoundError(
            "Manim CLI not found. Activate the project venv, add its Scripts "
            "directory to PATH, or set MANIM_BIN to the manim executable."
        )
    if version >= (0, 22, 0):
        return [manim, "render"]
    return [manim]


def _manim_version() -> tuple[int, ...]:
    manim = find_manim_executable()
    if not manim:
        raise FileNotFoundError("Manim CLI not found (PATH, local venv, or MANIM_BIN).")
    completed = subprocess.run(
        [manim, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (completed.stdout or "") + (completed.stderr or "")
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


def _find_output(episode_dir: Path, slug: str, suffix: str) -> Path | None:
    candidates = [
        path
        for path in (episode_dir / "media").rglob(f"{slug}{suffix}")
        if "partial_movie_files" not in path.parts
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: path.stat().st_mtime)


def _display(command: list[str]) -> str:
    try:
        return shlex.join(command)
    except Exception:
        return " ".join(command)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True, help="Episode directory")
    parser.add_argument("--quality", choices=sorted(QUALITY_PRESETS), help="Quality override")
    parser.add_argument("--scene", default="Episode", help="Manim scene class name")
    parser.add_argument("--skip-tts", action="store_true", help="Use the existing voice manifest")
    parser.add_argument("--force-tts", action="store_true", help="Regenerate all narration")
    parser.add_argument("--no-cache", action="store_true", help="Pass --disable_caching to Manim")
    parser.add_argument("--no-qa", action="store_true", help="Skip video inspection")
    parser.add_argument("--strict-qa", action="store_true", help="Treat QA warnings as failures")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without rendering")
    args = parser.parse_args(argv)

    episode_dir = resolve_episode(args.episode)
    brief = load_json(episode_dir / "brief.json")
    storyboard = load_json(episode_dir / "storyboard.json")
    theme_path = episode_dir / "theme.json"
    if not theme_path.exists():
        print(f"Missing theme.json in {episode_dir}", file=sys.stderr)
        return 2

    brief_errors, brief_warnings = validate_brief(brief)
    story_errors, story_warnings = validate_storyboard(
        storyboard, brief, episode_dir=episode_dir
    )
    errors = brief_errors + story_errors
    warnings = brief_warnings + story_warnings
    has_equations = any(beat.get("kind") == "equation" for beat in storyboard.get("beats", []))
    if has_equations and not latex_available() and not brief.get("output", {}).get("latex_fallback", False):
        errors.append(
            "This storyboard has equation beats but LaTeX is not on PATH. "
            "Install LaTeX or set output.latex_fallback=true for a draft only."
        )
    for message in warnings:
        print(f"  ! {message}")
    if errors:
        print("\nCannot render; fix these first:", file=sys.stderr)
        for message in errors:
            print(f"  ✗ {message}", file=sys.stderr)
        return 2

    quality = args.quality or str(brief.get("output", {}).get("quality", "standard"))
    if quality not in QUALITY_PRESETS:
        print(f"Unknown quality {quality!r}.", file=sys.stderr)
        return 2
    preset = dict(QUALITY_PRESETS[quality])
    aspect_ratio = str(brief.get("episode", {}).get("aspect_ratio", "16:9"))
    render_width, render_height = render_dimensions(quality, aspect_ratio)
    preset["width"] = render_width
    preset["height"] = render_height
    preset["aspect_ratio"] = aspect_ratio
    if args.quality and args.quality != brief.get("output", {}).get("quality"):
        print(
            f"  ! Quality override {quality!r} differs from the brief "
            f"({brief.get('output', {}).get('quality')!r}). Do not treat this as the final cut.",
            file=sys.stderr,
        )

    try:
        version = _manim_version()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    base_command = _manim_command(version)

    manifest_path = episode_dir / "voice" / "manifest.json"
    if not args.skip_tts:
        tts_command = [sys.executable, str(Path(__file__).with_name("tts.py")), "--episode", str(episode_dir)]
        if args.force_tts:
            tts_command.append("--force")
        print(f"TTS: {_display(tts_command)}")
        if not args.dry_run:
            completed = subprocess.run(tts_command, cwd=episode_dir, check=False)
            if completed.returncode != 0:
                print("TTS failed; render aborted.", file=sys.stderr)
                return completed.returncode
    if not manifest_path.exists():
        print(
            f"No voice manifest at {manifest_path}. Run scripts/tts.py first or omit --skip-tts.",
            file=sys.stderr,
        )
        return 2
    manifest = load_json(manifest_path)
    manifest_errors, manifest_warnings = validate_manifest(manifest, storyboard)
    for message in manifest_warnings:
        print(f"  ! {message}")
    if manifest_errors:
        print("Voice manifest is invalid:", file=sys.stderr)
        for message in manifest_errors:
            print(f"  ✗ {message}", file=sys.stderr)
        return 2

    slug_base = f"{episode_id(brief['series']['season'], brief['series']['episode_number'])}-{brief['episode']['slug']}"
    command = list(base_command) + [
        "--resolution",
        f"{preset['width']},{preset['height']}",
        "--fps",
        str(preset["fps"]),
        "--format",
        "mp4",
        "--media_dir",
        "media",
        "--output_file",
        slug_base,
        "--progress_bar",
        "display",
        "episode.py",
        args.scene,
    ]
    if args.no_cache:
        command.append("--disable_caching")

    env = dict(os.environ)
    env["PYTHONPATH"] = str(episode_dir) + os.pathsep + env.get("PYTHONPATH", "")
    env.setdefault("PYTHONIOENCODING", "utf-8")

    start_time = time.time()
    output_dir = episode_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    final_video = output_dir / f"{output_basename(brief, quality, aspect_ratio)}.mp4"
    final_srt = output_dir / f"{episode_id(brief['series']['season'], brief['series']['episode_number'])}-{brief['episode']['slug']}.srt"
    if final_video.exists():
        final_video.unlink()
    if final_srt.exists():
        final_srt.unlink()

    print(f"\nRender: {_display(command)}")
    print(f"Working directory: {episode_dir}")
    if args.dry_run:
        print("\nDry run: no render executed.")
        return 0

    completed = subprocess.run(command, cwd=episode_dir, env=env, check=False)
    elapsed = time.time() - start_time
    if completed.returncode != 0:
        print(f"Manim failed with exit code {completed.returncode}.", file=sys.stderr)
        return completed.returncode

    rendered = _find_output(episode_dir, slug_base, ".mp4")
    if rendered is None:
        print("Manim reported success but no MP4 was found.", file=sys.stderr)
        return 1
    shutil.copyfile(rendered, final_video)
    rendered_srt = _find_output(episode_dir, slug_base, ".srt")
    if rendered_srt is not None:
        shutil.copyfile(rendered_srt, final_srt)
    print(f"\nVideo: {final_video}")
    if final_srt.exists():
        print(f"Subtitles: {final_srt}")

    qa_status = 0
    if not args.no_qa:
        qa_command = [
            sys.executable,
            str(Path(__file__).with_name("qa.py")),
            "--video",
            str(final_video),
            "--out-dir",
            str(episode_dir / "qa"),
            "--target-duration",
            str(storyboard.get("target_duration_seconds") or brief["episode"].get("target_duration_seconds", 0)),
            "--width",
            str(preset["width"]),
            "--height",
            str(preset["height"]),
            "--fps",
            str(preset["fps"]),
        ]
        if final_srt.exists():
            qa_command.extend(["--srt", str(final_srt)])
        if args.strict_qa:
            qa_command.append("--strict")
        print(f"\nQA: {_display(qa_command)}")
        qa_status = subprocess.run(qa_command, cwd=episode_dir, check=False).returncode

    report = {
        "schema_version": 1,
        "created_at": now_iso(),
        "episode": str(episode_dir),
        "quality": quality,
        "preset": preset,
        "manim_version": ".".join(str(part) for part in version),
        "command": command,
        "tts_manifest": str(manifest_path),
        "video": str(final_video),
        "subtitles": str(final_srt) if final_srt.exists() else None,
        "render_seconds": round(elapsed, 2),
        "qa_exit_code": qa_status,
        "warnings": warnings,
    }
    atomic_write_json(episode_dir / "qa" / "render_report.json", report)
    print(f"\nRender report: {episode_dir / 'qa' / 'render_report.json'}")
    print(f"Render time: {elapsed:.1f}s")
    if qa_status != 0:
        print("QA reported issues; inspect qa/report.md.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
