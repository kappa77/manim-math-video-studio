#!/usr/bin/env python3
"""Generate short, comparable voice samples for the voice-selection gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _common import (
    atomic_write_json,
    default_voice,
    load_voices,
    normalize_language,
    now_iso,
    sha256_text,
    slugify,
    style_defaults,
    voice_entries,
)
from tts import _custom_generate, _edge_generate_with_retry, _piper_generate


DEFAULT_TEXT = (
    "In this episode we follow one idea from its first question to the moment "
    "everything clicks, and see why it still matters today."
)


def choose_entries(
    entries: list[dict[str, Any]],
    recommended: str,
    requested: str | None,
    count: int,
) -> list[dict[str, Any]]:
    if requested:
        wanted = [part.strip() for part in requested.split(",") if part.strip()]
        by_key: dict[str, dict[str, Any]] = {}
        for entry in entries:
            by_key[str(entry.get("id", "")).casefold()] = entry
            by_key[str(entry.get("label", "")).casefold()] = entry
        chosen: list[dict[str, Any]] = []
        for value in wanted:
            entry = by_key.get(value.casefold())
            if entry is None:
                raise SystemExit(
                    f"Unknown voice {value!r}. Use --list or an id from assets/voices.json."
                )
            if entry not in chosen:
                chosen.append(entry)
        return chosen[:count]

    ordered: list[dict[str, Any]] = []
    for entry in entries:
        if str(entry.get("id", "")) == recommended:
            ordered.append(entry)
            break
    if not ordered and entries:
        ordered.append(entries[0])

    # Prefer a different gender for the second sample, then fill with the rest.
    last_gender = str(ordered[0].get("gender", "")) if ordered else ""
    for entry in entries:
        if len(ordered) >= count:
            break
        if entry in ordered:
            continue
        if str(entry.get("gender", "")) != last_gender:
            ordered.append(entry)
            last_gender = str(entry.get("gender", ""))
    for entry in entries:
        if len(ordered) >= count:
            break
        if entry not in ordered:
            ordered.append(entry)
    return ordered[:count]


def media_duration(path: Path) -> float | None:
    try:
        import av

        with av.open(str(path)) as container:
            if container.duration:
                return round(float(container.duration) / 1_000_000.0, 2)
    except Exception:  # noqa: BLE001 - duration is optional metadata
        return None
    return None


def unique_stem(index: int, entry: dict[str, Any], used: set[str]) -> str:
    label = slugify(entry.get("label") or entry.get("id") or "voice")
    stem = f"{index:02d}-{label}"
    if stem in used:
        stem = f"{stem}-{slugify(entry.get('id', index))}"
    used.add(stem)
    return stem


def synthesize(
    entry: dict[str, Any],
    out_base: Path,
    *,
    provider: str,
    text: str,
    language: str,
    rate: str,
    pitch: str,
    volume: str,
    piper_model: str | None,
    custom_command: list[str] | None,
    custom_suffix: str,
) -> Path:
    voice_id = str(entry.get("id", ""))
    if provider == "edge":
        out_path = out_base.with_suffix(".mp3")
        _edge_generate_with_retry(
            text,
            voice_id,
            rate,
            pitch,
            volume,
            out_path,
        )
        return out_path
    if provider == "piper":
        if not piper_model:
            raise SystemExit("--provider piper requires --piper-model.")
        out_path = out_base.with_suffix(".wav")
        _piper_generate(text, piper_model, out_path)
        return out_path
    if provider == "custom":
        if not custom_command:
            raise SystemExit("--provider custom requires --command-json.")
        out_path = out_base.with_suffix(custom_suffix)
        _custom_generate(
            text,
            custom_command,
            out_path,
            voice=voice_id,
            language=language,
            rate=rate,
            pitch=pitch,
            volume=volume,
        )
        return out_path
    raise SystemExit(f"Unsupported provider for samples: {provider}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", required=True, help="Narration locale, e.g. it-IT")
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Same 18-25 word sentence for every sample (localize it for the locale)",
    )
    parser.add_argument("--style", default="warm-teacher", help="Delivery style preset")
    parser.add_argument("--rate", help="Rate override, e.g. -3%%")
    parser.add_argument("--pitch", help="Pitch override, e.g. +0Hz")
    parser.add_argument("--volume", default="+0%", help="Volume override, e.g. +0%%")
    parser.add_argument(
        "--voices",
        help="Comma-separated voice ids or labels; default: pick three from the catalog",
    )
    parser.add_argument("--count", type=int, default=3, help="Number of samples (default: 3)")
    parser.add_argument(
        "--out-dir",
        default="voice-samples",
        help="Output directory in the user workspace (default: voice-samples)",
    )
    parser.add_argument("--provider", choices=["edge", "piper", "custom"], default="edge")
    parser.add_argument("--piper-model", help="Path to a Piper .onnx model")
    parser.add_argument(
        "--command-json",
        help="JSON array custom TTS command with {text_file}, {out_file}, {voice}, ...",
    )
    parser.add_argument(
        "--custom-suffix",
        default=".wav",
        help="Output suffix for a custom provider (default: .wav)",
    )
    parser.add_argument("--list", action="store_true", help="List candidate voices and exit")
    parser.add_argument("--force", action="store_true", help="Regenerate existing samples")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan only")
    args = parser.parse_args(argv)

    voices = load_voices()
    language = normalize_language(args.language, voices)
    entries = voice_entries(language, voices)
    recommended = default_voice(language, voices)
    if not entries:
        print(
            f"No curated voices for {language!r}. Any valid edge-tts voice id can be "
            "passed with --voices.",
            file=sys.stderr,
        )
    if args.list:
        for entry in entries:
            marker = " (recommended)" if entry.get("id") == recommended else ""
            print(
                f"{entry.get('id', ''):44} {entry.get('label', ''):10} "
                f"{entry.get('gender', ''):7} {entry.get('style', '')}{marker}"
            )
        return 0

    chosen = choose_entries(entries, recommended, args.voices, max(1, args.count))
    if not chosen:
        raise SystemExit("No voices selected. Use --voices with at least one voice id.")
    presets = style_defaults(args.style, voices)
    rate = args.rate or presets["rate"]
    pitch = args.pitch or presets["pitch"]
    custom_command = None
    if args.command_json:
        try:
            custom_command = json.loads(args.command_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"--command-json is not valid JSON: {exc}") from exc
        if not isinstance(custom_command, list) or not all(
            isinstance(part, str) for part in custom_command
        ):
            raise SystemExit("--command-json must be a JSON array of strings.")
    if args.language.casefold().split("-")[0] != "en" and args.text == DEFAULT_TEXT:
        print(
            "  ! --text was not supplied; the default sample sentence is English. "
            "Pass a localized 18-25 word sentence for a fair comparison."
        )

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "samples.json"
    signature = sha256_text(
        json.dumps(
            {
                "text": args.text,
                "language": language,
                "style": args.style,
                "rate": rate,
                "pitch": pitch,
                "volume": args.volume,
                "provider": args.provider,
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        16,
    )
    previous: dict[str, dict[str, Any]] = {}
    if manifest_path.exists() and not args.force:
        try:
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - rebuild a broken manifest
            old = {}
        if old.get("signature") == signature:
            previous = {
                str(item.get("voice_id")): item
                for item in old.get("samples", [])
                if item and item.get("voice_id")
            }

    used: set[str] = set()
    samples: list[dict[str, Any]] = []
    for index, entry in enumerate(chosen, start=1):
        stem = unique_stem(index, entry, used)
        out_base = out_dir / stem
        voice_id = str(entry.get("id", ""))
        print(
            f"{index}. {entry.get('label', '')} — {voice_id}"
            + (" (recommended)" if voice_id == recommended else "")
        )
        if args.dry_run:
            print(f"   would write {out_base} with suffix for {args.provider}")
            continue

        before = previous.get(voice_id)
        if before:
            old_name = str(before.get("filename") or Path(str(before.get("path", ""))).name)
            old_path = out_dir / old_name
            if old_path.exists():
                duration = media_duration(old_path)
                samples.append(
                    {
                        "index": index,
                        "voice_id": voice_id,
                        "label": entry.get("label", ""),
                        "gender": entry.get("gender", ""),
                        "recommended": voice_id == recommended,
                        "path": str(old_path),
                        "filename": old_path.name,
                        "duration_seconds": duration,
                    }
                )
                suffix = f" ({duration:.1f}s)" if duration else ""
                print(f"   reusing {old_path}{suffix}")
                continue

        out_path = synthesize(
            entry,
            out_base,
            provider=args.provider,
            text=args.text,
            language=language,
            rate=rate,
            pitch=pitch,
            volume=args.volume,
            piper_model=args.piper_model,
            custom_command=custom_command,
            custom_suffix=args.custom_suffix,
        )
        duration = media_duration(out_path)
        samples.append(
            {
                "index": index,
                "voice_id": voice_id,
                "label": entry.get("label", ""),
                "gender": entry.get("gender", ""),
                "recommended": voice_id == recommended,
                "path": str(out_path),
                "filename": out_path.name,
                "duration_seconds": duration,
            }
        )
        suffix = f" ({duration:.1f}s)" if duration else ""
        print(f"   {out_path}{suffix}")

    if args.dry_run:
        return 0

    manifest = {
        "schema_version": 1,
        "signature": signature,
        "generated_at": now_iso(),
        "language": language,
        "text": args.text,
        "style": args.style,
        "rate": rate,
        "pitch": pitch,
        "volume": args.volume,
        "provider": args.provider,
        "recommended_voice": recommended,
        "samples": samples,
    }
    atomic_write_json(manifest_path, manifest)
    print(f"\nWrote {manifest_path}")
    print(
        "Ask the user to choose a number or exact voice id, then record the choice "
        "in brief.json output.voice_selection."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
