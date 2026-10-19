#!/usr/bin/env python3
"""Generate narration audio and a timing manifest from a storyboard."""

from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any

from _common import (
    atomic_write_json,
    default_voice,
    load_json,
    load_template,
    load_voices,
    normalize_language,
    now_iso,
    resolve_episode,
    sha256_text,
    style_defaults,
    write_text,
)


# --------------------------------------------------------------------------- text
def apply_lexicon(text: str, lexicon: dict[str, str]) -> str:
    if not lexicon:
        return text
    result = str(text)
    for source in sorted(lexicon, key=len, reverse=True):
        replacement = str(lexicon[source])
        pattern = re.compile(rf"(?<!\w){re.escape(source)}(?!\w)", flags=re.IGNORECASE)
        result = pattern.sub(lambda _match, value=replacement: value, result)
    return result


def spoken_text_for(beat: dict[str, Any]) -> str:
    return str(beat.get("speech") or beat.get("narration") or "").strip()


def caption_text_for(beat: dict[str, Any]) -> str:
    return str(beat.get("caption") or beat.get("narration") or "").strip()


def estimate_seconds(text: str, wpm: float) -> float:
    words = len(re.findall(r"\S+", text))
    return max(1.0, words / max(1.0, wpm) * 60.0)


# --------------------------------------------------------------------------- audio
def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        rate = handle.getframerate()
    return frames / float(rate) if rate else 0.0


def ensure_wav(source: Path, target: Path) -> Path:
    source = Path(source)
    target = Path(target)
    if source.suffix.lower() == ".wav":
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
        return target
    try:
        import av

        with av.open(str(source)) as input_container:
            stream = input_container.streams.audio[0]
            output_container = av.open(str(target), mode="w", format="wav")
            try:
                output_stream = output_container.add_stream(
                    "pcm_s16le",
                    rate=stream.rate,
                    layout=stream.layout.name,
                )
                for frame in input_container.decode(stream):
                    frame.pts = None
                    for packet in output_stream.encode(frame):
                        output_container.mux(packet)
                for packet in output_stream.encode(None):
                    output_container.mux(packet)
            finally:
                output_container.close()
        return target
    except Exception as av_error:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg:
            subprocess.run(
                [ffmpeg, "-y", "-i", str(source), str(target)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return target
        raise RuntimeError(
            f"Could not convert {source} to WAV. Install PyAV (`pip install av`) or ffmpeg. "
            f"PyAV error: {av_error}"
        ) from av_error


def _seconds_from_edge_ticks(value: Any) -> float:
    number = float(value or 0.0)
    # edge-tts reports 100-nanosecond ticks.
    if abs(number) > 1000:
        return number / 10_000_000.0
    return number


async def _edge_generate(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
    out_mp3: Path,
    *,
    proxy: str | None = None,
) -> list[dict[str, Any]]:
    import edge_tts

    signature = inspect.signature(edge_tts.Communicate)
    kwargs: dict[str, Any] = {
        "rate": rate,
        "pitch": pitch,
        "volume": volume,
    }
    if "boundary" in signature.parameters:
        kwargs["boundary"] = "WordBoundary"
    if proxy and "proxy" in signature.parameters:
        kwargs["proxy"] = proxy
    communicate = edge_tts.Communicate(text, voice, **kwargs)
    words: list[dict[str, Any]] = []
    temporary = out_mp3.with_suffix(out_mp3.suffix + ".part")
    try:
        with temporary.open("wb") as handle:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    handle.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = _seconds_from_edge_ticks(chunk.get("offset"))
                    duration = _seconds_from_edge_ticks(chunk.get("duration"))
                    words.append(
                        {
                            "text": str(chunk.get("text", "")),
                            "start": round(start, 4),
                            "end": round(start + duration, 4),
                        }
                    )
        temporary.replace(out_mp3)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return words


def _edge_generate_with_retry(
    text: str,
    voice: str,
    rate: str,
    pitch: str,
    volume: str,
    out_mp3: Path,
    *,
    proxy: str | None = None,
    attempts: int = 3,
) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return asyncio.run(
                _edge_generate(
                    text,
                    voice,
                    rate,
                    pitch,
                    volume,
                    out_mp3,
                    proxy=proxy,
                )
            )
        except Exception as exc:  # noqa: BLE001 - retry network and service errors
            last_error = exc
            if attempt < attempts:
                delay = 2 ** (attempt - 1)
                print(f"    edge-tts attempt {attempt} failed ({exc}); retrying in {delay}s...")
                time.sleep(delay)
    raise RuntimeError(f"edge-tts failed after {attempts} attempts: {last_error}") from last_error


def _piper_generate(text: str, model: str, out_wav: Path, executable: str = "piper") -> None:
    binary = shutil.which(executable)
    if not binary:
        raise RuntimeError(
            "Piper executable not found on PATH. Install piper and pass --piper-model."
        )
    subprocess.run(
        [binary, "--model", model, "--output_file", str(out_wav)],
        input=text.encode("utf-8"),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _custom_generate(
    text: str,
    command: list[str],
    out_path: Path,
    *,
    voice: str,
    language: str,
    rate: str,
    pitch: str,
    volume: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="manim-tts-") as temporary:
        text_file = Path(temporary) / "text.txt"
        text_file.write_text(text, encoding="utf-8")
        replacements = {
            "{text_file}": str(text_file),
            "{out_file}": str(out_path),
            "{voice}": voice,
            "{language}": language,
            "{rate}": rate,
            "{pitch}": pitch,
            "{volume}": volume,
        }
        rendered: list[str] = []
        for part in command:
            for placeholder, value in replacements.items():
                part = part.replace(placeholder, value)
            rendered.append(part)
        subprocess.run(rendered, check=True)


def _list_edge_voices(language: str | None) -> int:
    voices = load_voices()
    try:
        import edge_tts

        live = asyncio.run(edge_tts.list_voices())
        rows = []
        for voice in live:
            locale = str(voice.get("Locale", ""))
            if language and not locale.casefold().startswith(language.casefold()):
                continue
            rows.append(
                (
                    str(voice.get("ShortName", "")),
                    locale,
                    str(voice.get("Gender", "")),
                    str(voice.get("FriendlyName", "")),
                )
            )
        print(f"{'Voice':40} {'Locale':10} {'Gender':8} Friendly name")
        for short_name, locale, gender, friendly in sorted(rows):
            print(f"{short_name:40} {locale:10} {gender:8} {friendly}")
        return 0
    except Exception as exc:  # noqa: BLE001 - offline fallback
        print(f"edge-tts voice listing unavailable ({exc}); showing the curated catalog.\n")
    if language:
        normalized = normalize_language(language, voices)
        locales = [normalized] if normalized in voices.get("languages", {}) else [
            locale for locale in sorted(voices.get("languages", {}))
            if locale.casefold().startswith(language.casefold())
        ]
    else:
        locales = sorted(voices.get("languages", {}))
    for locale in locales:
        info = voices.get("languages", {}).get(locale)
        if not info:
            continue
        print(f"\n{locale} — {info.get('label', '')}")
        for voice in info.get("voices", []):
            print(f"  {voice['id']:42} {voice.get('gender', ''):7} {voice.get('style', '')}")
    return 0


def _list_styles() -> int:
    voices = load_voices()
    print(f"{'Style':26} {'Rate':8} {'Pitch':8} Description")
    for name, info in voices.get("styles", {}).items():
        print(f"{name:26} {info.get('rate', ''):8} {info.get('pitch', ''):8} {info.get('description', '')}")
    return 0


def _split_caption(text: str, max_chars: int) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    chunks: list[str] = []
    current = ""
    for word in words:
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= max_chars:
            current = f"{current} {word}"
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def _write_preview_srt(segments: list[dict[str, Any]], path: Path, max_chars: int, tail_pad: float) -> None:
    cues: list[tuple[float, float, str]] = []
    cursor = 0.0
    for segment in segments:
        caption = str(segment.get("caption", "")).strip()
        duration = float(segment.get("duration", 0.0))
        if caption:
            chunks = _split_caption(caption, max_chars)
            weights = [max(1, len(chunk)) for chunk in chunks]
            total = sum(weights) or 1
            offset = cursor
            for chunk, weight in zip(chunks, weights):
                chunk_duration = duration * weight / total
                cues.append((offset, offset + chunk_duration, chunk))
                offset += chunk_duration
        cursor += duration + tail_pad

    def timestamp(seconds: float) -> str:
        milliseconds = int(round(seconds * 1000))
        hours, remainder = divmod(milliseconds, 3_600_000)
        minutes, remainder = divmod(remainder, 60_000)
        secs, millis = divmod(remainder, 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    lines: list[str] = []
    for index, (start, end, text) in enumerate(cues, start=1):
        lines.extend([str(index), f"{timestamp(start)} --> {timestamp(end)}", text, ""])
    write_text(path, "\n".join(lines))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", help="Episode directory")
    parser.add_argument("--provider", choices=["edge", "piper", "custom", "none"], help="TTS provider override")
    parser.add_argument("--voice", help="Voice id override")
    parser.add_argument("--language", help="Narration locale override")
    parser.add_argument("--style", help="Delivery style override")
    parser.add_argument("--rate", help="Rate override, e.g. -3%%")
    parser.add_argument("--pitch", help="Pitch override, e.g. +0Hz")
    parser.add_argument("--volume", help="Volume override, e.g. +0%%")
    parser.add_argument("--proxy", help="Proxy URL for edge-tts")
    parser.add_argument("--piper-model", help="Path to a Piper .onnx model")
    parser.add_argument("--force", action="store_true", help="Regenerate all segments")
    parser.add_argument("--only", action="append", default=[], help="Regenerate only this beat id (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without synthesizing")
    parser.add_argument("--check", action="store_true", help="Validate the storyboard and voice selection only")
    parser.add_argument("--list-voices", action="store_true", help="List edge-tts voices")
    parser.add_argument("--list-styles", action="store_true", help="List delivery styles")
    parser.add_argument("--wpm", type=float, default=145.0, help="Words per minute for silent/estimated durations")
    args = parser.parse_args(argv)

    if args.list_styles:
        return _list_styles()
    if args.list_voices:
        return _list_edge_voices(args.language)
    if not args.episode:
        parser.error("--episode is required unless --list-voices/--list-styles is used.")

    episode_dir = resolve_episode(args.episode)
    brief = load_json(episode_dir / "brief.json")
    storyboard = load_json(episode_dir / "storyboard.json")
    theme_path = episode_dir / "theme.json"
    theme = load_json(theme_path) if theme_path.exists() else {}
    voice_cfg = dict(brief.get("output", {}).get("voice", {}))
    output_cfg = brief.get("output", {})

    language = normalize_language(args.language or output_cfg.get("language", ""))
    provider = args.provider or voice_cfg.get("provider") or "edge"
    style = args.style or voice_cfg.get("style") or "warm-teacher"
    presets = style_defaults(style)
    if args.style and not args.rate:
        rate = presets["rate"]
    else:
        rate = args.rate or voice_cfg.get("rate") or presets["rate"]
    if args.style and not args.pitch:
        pitch = presets["pitch"]
    else:
        pitch = args.pitch or voice_cfg.get("pitch") or presets["pitch"]
    volume = args.volume or voice_cfg.get("volume") or "+0%"
    voice_id = args.voice or voice_cfg.get("id") or default_voice(language)
    if provider == "none":
        voice_id = voice_id or "silent"
    lexicon = dict(brief.get("accuracy", {}).get("pronunciations", {}) or {})
    wpm = float(args.wpm or theme.get("story", {}).get("words_per_minute", 145))
    tail_pad = float(theme.get("captions", {}).get("tail_pad", 0.15))
    max_chars = int(theme.get("captions", {}).get("max_chars", 84))

    beats = [beat for beat in storyboard.get("beats", []) if str(beat.get("id", "")).strip()]
    beat_ids = {str(beat["id"]) for beat in beats}
    for only in args.only:
        if only not in beat_ids:
            print(f"ERROR: --only beat {only!r} is not in the storyboard.", file=sys.stderr)
            return 2

    # Validate provider prerequisites.
    if provider == "edge":
        try:
            import edge_tts  # noqa: F401
        except ImportError:
            print(
                "edge-tts is not installed. Install it with:\n  python -m pip install edge-tts\n"
                "or use --provider piper/custom/none.",
                file=sys.stderr,
            )
            return 2
    if provider == "piper":
        model = args.piper_model or voice_cfg.get("piper_model")
        if not model:
            print("--provider piper requires --piper-model (or output.voice.piper_model).", file=sys.stderr)
            return 2
        voice_cfg["piper_model"] = model
    if provider == "custom":
        command = voice_cfg.get("command")
        if not isinstance(command, (list, tuple)) or not command:
            print(
                "--provider custom requires output.voice.command to be a non-empty array in brief.json.",
                file=sys.stderr,
            )
            return 2
    if provider == "edge":
        voices = load_voices()
        info = voices.get("languages", {}).get(language, {})
        allowed = {voice["id"] for voice in info.get("voices", [])}
        if allowed and voice_id not in allowed:
            print(
                f"  ! Voice {voice_id!r} is not in the curated {language} list; "
                "edge-tts will be asked directly."
            )

    if args.check:
        print(f"Episode: {episode_dir}")
        print(f"Provider: {provider} | voice: {voice_id} | language: {language}")
        print(f"Style: {style} | rate: {rate} | pitch: {pitch} | volume: {volume}")
        print(f"Beats: {len(beats)} | lexicon entries: {len(lexicon)}")
        print("Voice selection looks valid.")
        return 0

    old_manifest: dict[str, Any] = {}
    manifest_path = episode_dir / "voice" / "manifest.json"
    if manifest_path.exists() and not args.force:
        try:
            old_manifest = load_json(manifest_path)
        except Exception:
            old_manifest = {}
    old_segments = {str(segment.get("id")): segment for segment in old_manifest.get("segments", [])}

    voice_dir = episode_dir / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    segments: list[dict[str, Any]] = []
    total = 0.0

    for index, beat in enumerate(beats, start=1):
        beat_id = str(beat["id"])
        spoken = apply_lexicon(spoken_text_for(beat), lexicon)
        caption = caption_text_for(beat)
        silent = bool(beat.get("silent")) or not spoken
        hash_input = json.dumps(
            {
                "provider": provider,
                "voice": voice_id,
                "language": language,
                "rate": rate,
                "pitch": pitch,
                "volume": volume,
                "text": spoken,
                "lexicon": lexicon,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        audio_hash = sha256_text(hash_input, 12)
        base = f"{beat_id}-{audio_hash}" if spoken else f"{beat_id}-silent"
        mp3_path = voice_dir / f"{base}.mp3"
        wav_path = voice_dir / f"{base}.wav"
        relative_wav = wav_path.relative_to(episode_dir).as_posix()

        reuse = False
        if not args.force and (not args.only or beat_id not in args.only):
            old = old_segments.get(beat_id)
            if old and old.get("audio_hash") == audio_hash and old.get("duration"):
                old_audio = old.get("audio")
                old_path = episode_dir / str(old_audio) if old_audio else None
                if old_path and old_path.exists():
                    reuse = True
                    duration = float(old["duration"])
                    words = old.get("words", [])
                    audio_value = str(old_audio)
                elif provider == "none":
                    reuse = True
                    duration = float(old["duration"])
                    words = []
                    audio_value = None
        if not reuse:
            words: list[dict[str, Any]] = []
            audio_value: str | None = None
            if silent or provider == "none":
                duration = float(beat.get("duration_hint") or estimate_seconds(spoken, wpm))
            else:
                if args.dry_run:
                    duration = float(beat.get("duration_hint") or estimate_seconds(spoken, wpm))
                    print(f"[dry-run] {beat_id}: would synthesize {duration:.1f}s of {language} with {voice_id}")
                else:
                    print(f"[{index}/{len(beats)}] {beat_id}: synthesizing...")
                    if provider == "edge":
                        words = _edge_generate_with_retry(
                            spoken,
                            voice_id,
                            rate,
                            pitch,
                            volume,
                            mp3_path,
                            proxy=args.proxy,
                        )
                        ensure_wav(mp3_path, wav_path)
                    elif provider == "piper":
                        _piper_generate(spoken, str(voice_cfg.get("piper_model")), wav_path)
                        words = []
                    elif provider == "custom":
                        raw_out = voice_dir / f"{base}.out"
                        _custom_generate(
                            spoken,
                            list(voice_cfg.get("command", [])),
                            raw_out,
                            voice=voice_id,
                            language=language,
                            rate=rate,
                            pitch=pitch,
                            volume=volume,
                        )
                        if raw_out.suffix.lower() == ".wav":
                            raw_out.replace(wav_path)
                        else:
                            ensure_wav(raw_out, wav_path)
                            raw_out.unlink(missing_ok=True)
                        words = []
                    else:
                        raise ValueError(f"Unsupported provider {provider!r}")
                    duration = wav_duration(wav_path)
                    audio_value = relative_wav
                    print(f"    {duration:.2f}s -> {relative_wav}")
            if silent or provider == "none":
                duration = float(beat.get("duration_hint") or estimate_seconds(spoken, wpm))
                audio_value = None
            if not spoken:
                caption = ""
        total += duration
        segments.append(
            {
                "id": beat_id,
                "text": spoken,
                "caption": caption,
                "duration": round(duration, 4),
                "audio": audio_value,
                "audio_hash": audio_hash,
                "words": words,
            }
        )

    manifest = {
        "schema_version": 1,
        "created_at": now_iso(),
        "episode_id": storyboard.get("episode_id"),
        "provider": provider,
        "language": language,
        "voice": voice_id,
        "style": style,
        "rate": rate,
        "pitch": pitch,
        "volume": volume,
        "lexicon": lexicon,
        "segments": segments,
        "total_duration": round(total, 4),
    }

    if args.dry_run:
        print(f"\nDry run: {len(segments)} segments, estimated total {total:.1f}s")
        return 0

    atomic_write_json(manifest_path, manifest)
    _write_preview_srt(segments, voice_dir / "captions.srt", max_chars=max_chars, tail_pad=tail_pad)
    narration_lines = [f"{segment['id']}\t{segment['duration']:.2f}s\t{segment['text']}" for segment in segments]
    write_text(voice_dir / "narration.txt", "\n".join(narration_lines) + "\n")

    target = float(
        storyboard.get("target_duration_seconds")
        or brief.get("episode", {}).get("target_duration_seconds")
        or 0
    )
    print(f"\nWrote {manifest_path}")
    print(f"Total narration: {total:.1f}s across {len(segments)} segments")
    if target:
        drift = (total - target) / max(1.0, target)
        print(f"Target: {target:.0f}s ({drift:+.0%})")
        if abs(drift) > 0.2:
            print("  ! Duration is more than 20% away from the target; revise the script.", file=sys.stderr)
    print(f"Voice: {voice_id} | {language} | {provider} | {style}")
    print(f"Preview captions: {voice_dir / 'captions.srt'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
