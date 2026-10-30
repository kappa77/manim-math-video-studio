#!/usr/bin/env python3
"""Render a storyboard as a readable script with duration estimates."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

from _common import estimate_duration, load_json, resolve_episode, write_text


def _visual_summary(beat: dict[str, Any]) -> list[str]:
    kind = str(beat.get("kind", ""))
    lines: list[str] = []
    if kind == "title":
        if beat.get("subtitle"):
            lines.append(f"Subtitle: {beat['subtitle']}")
        if beat.get("kicker"):
            lines.append(f"Kicker: {beat['kicker']}")
    elif kind == "section":
        if beat.get("subheading"):
            lines.append(f"Subheading: {beat['subheading']}")
    elif kind == "bullets":
        for item in beat.get("items", []):
            text = item.get("text") if isinstance(item, dict) else item
            lines.append(f"- {text}")
    elif kind == "equation":
        lines.append(f"LaTeX: `{beat.get('latex', '')}`")
        for step in beat.get("steps", []) or []:
            lines.append(f"  -> `{step}`")
        if beat.get("note"):
            lines.append(f"Note: {beat['note']}")
    elif kind == "graph":
        graph = beat.get("graph", {})
        lines.append(
            f"Graph: {graph.get('type', 'cartesian')} | animation: {graph.get('animation', 'draw')}"
        )
        for plot in graph.get("plots", []) or []:
            if isinstance(plot, dict):
                lines.append(f"  plot: y = {plot.get('expr')}")
        if graph.get("expr") and not graph.get("plots"):
            lines.append(f"  plot: y = {graph['expr']}")
        for annotation in graph.get("annotations", []) or []:
            lines.append(f"  annotation: {annotation.get('type')} {annotation.get('label', '')}".rstrip())
    elif kind == "compare":
        for side in ("left", "right"):
            data = beat.get(side, {})
            lines.append(f"{side.title()}: {data.get('heading', '')}")
            for item in data.get("items", []):
                lines.append(f"  - {item}")
    elif kind == "recap":
        for item in beat.get("items", []):
            lines.append(f"- {item}")
    elif kind == "outro":
        if beat.get("next"):
            lines.append(f"Next: {beat['next']}")
        if beat.get("cta"):
            lines.append(f"CTA: {beat['cta']}")
    elif kind == "quote":
        lines.append(f"Quote: {beat.get('quote', '')}")
        if beat.get("attribution"):
            lines.append(f"Attribution: {beat['attribution']}")
    elif kind == "image":
        lines.append(f"Image: {beat.get('path', '')}")
        if beat.get("label"):
            lines.append(f"Label: {beat['label']}")
    elif kind == "custom":
        lines.append("Custom visual: override custom_beat() in episode.py")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True, help="Episode directory")
    parser.add_argument("--stdout", action="store_true", help="Print instead of writing script.md")
    args = parser.parse_args(argv)

    episode_dir = resolve_episode(args.episode)
    brief = load_json(episode_dir / "brief.json")
    storyboard = load_json(episode_dir / "storyboard.json")
    theme_path = episode_dir / "theme.json"
    theme = load_json(theme_path) if theme_path.exists() else {}
    manifest_path = episode_dir / "voice" / "manifest.json"
    manifest = load_json(manifest_path) if manifest_path.exists() else None
    durations = {
        str(segment.get("id")): float(segment.get("duration", 0.0))
        for segment in (manifest or {}).get("segments", [])
    }

    series = brief.get("series", {})
    episode = brief.get("episode", {})
    wpm = float(theme.get("story", {}).get("words_per_minute", 145))
    estimated = estimate_duration(storyboard, wpm=wpm)
    total_words = 0
    for beat in storyboard.get("beats", []):
        text = str(beat.get("speech") or beat.get("narration") or "")
        total_words += len(re.findall(r"\S+", text))

    lines: list[str] = []
    lines.append(f"# {storyboard.get('title', episode.get('title', 'Episode'))}")
    lines.append("")
    lines.append(f"**Series:** {series.get('title', '')} · {storyboard.get('episode_id', '')}")
    lines.append(f"**Template:** {series.get('template', '')} | **Quality:** {brief.get('output', {}).get('quality', '')}")
    lines.append(f"**Language:** {brief.get('output', {}).get('language', '')} | **Voice:** {brief.get('output', {}).get('voice', {}).get('id', '')}")
    lines.append(f"**Target:** {episode.get('target_duration_seconds', '')} s | **Estimate:** {estimated:.0f} s | **Words:** {total_words}")
    lines.append(f"**Thesis:** {episode.get('thesis', '')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for index, beat in enumerate(storyboard.get("beats", []), start=1):
        beat_id = str(beat.get("id", ""))
        kind = str(beat.get("kind", ""))
        actual = durations.get(beat_id)
        duration_text = f"{actual:.1f}s" if actual is not None else "not recorded"
        lines.append(f"## {index:02d}. {beat_id} — {kind} ({duration_text})")
        lines.append("")
        narration = str(beat.get("narration", "")).strip()
        if narration:
            lines.append(f"**Narration:** {narration}")
        else:
            lines.append("**Narration:** _(silent)_")
        speech = str(beat.get("speech", "")).strip()
        if speech and speech != narration:
            lines.append("")
            lines.append(f"**Spoken form:** {speech}")
        caption = str(beat.get("caption", "")).strip()
        if caption and caption != narration:
            lines.append("")
            lines.append(f"**Caption:** {caption}")
        visual = _visual_summary(beat)
        if visual:
            lines.append("")
            lines.append("**Visual:**")
            lines.extend(f"- {line}" if not line.startswith(("-", "  ")) else line for line in visual)
        if beat.get("notes"):
            lines.append("")
            lines.append(f"**Notes:** {beat['notes']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Accuracy checklist")
    lines.append("")
    lines.append("- [ ] Every formula re-derived.")
    lines.append("- [ ] Domains and edge cases checked.")
    lines.append("- [ ] Notation consistent with the series.")
    lines.append("- [ ] Sources real and cited.")
    lines.append("- [ ] Pronunciations checked in the voice manifest.")
    lines.append("")

    text = "\n".join(lines)
    if args.stdout:
        print(text)
    else:
        write_text(episode_dir / "script.md", text)
        print(f"Wrote {episode_dir / 'script.md'}")
        print(f"Estimated duration: {estimated:.0f}s (target {episode.get('target_duration_seconds', '?')}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
