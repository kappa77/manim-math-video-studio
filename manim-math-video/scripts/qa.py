#!/usr/bin/env python3
"""Inspect a rendered video: streams, audio, subtitles, contact sheet, report."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

from _common import atomic_write_json, now_iso, write_text


def _db(value: float) -> float:
    if value <= 0:
        return -120.0
    return 20.0 * math.log10(value)


def _as_float_audio(array: np.ndarray) -> np.ndarray:
    array = np.asarray(array)
    if array.dtype.kind in "iu":
        info = np.iinfo(array.dtype)
        return array.astype(np.float32) / float(max(abs(info.min), info.max))
    return array.astype(np.float32)


def inspect_media(path: Path) -> dict[str, Any]:
    import av

    result: dict[str, Any] = {
        "path": str(path),
        "duration": 0.0,
        "video": None,
        "audio": None,
        "audio_stats": None,
    }
    with av.open(str(path)) as container:
        if container.duration:
            result["duration"] = round(float(container.duration) / av.time_base, 3)
        video_stream = next((stream for stream in container.streams if stream.type == "video"), None)
        audio_stream = next((stream for stream in container.streams if stream.type == "audio"), None)
        if video_stream is not None:
            rate = video_stream.average_rate or video_stream.guessed_rate
            result["video"] = {
                "codec": video_stream.codec_context.name,
                "width": int(video_stream.codec_context.width),
                "height": int(video_stream.codec_context.height),
                "fps": round(float(rate), 3) if rate else None,
                "frames": int(video_stream.frames or 0),
            }
        if audio_stream is not None:
            result["audio"] = {
                "codec": audio_stream.codec_context.name,
                "sample_rate": int(audio_stream.codec_context.sample_rate or 0),
                "channels": int(audio_stream.codec_context.channels or 0),
            }
            peak = 0.0
            sum_squares = 0.0
            sample_count = 0
            for frame in container.decode(audio_stream):
                array = _as_float_audio(frame.to_ndarray())
                peak = max(peak, float(np.max(np.abs(array))) if array.size else 0.0)
                sum_squares += float(np.sum(array.astype(np.float64) ** 2))
                sample_count += int(array.size)
            rms = math.sqrt(sum_squares / sample_count) if sample_count else 0.0
            result["audio_stats"] = {
                "peak_db": round(_db(peak), 2),
                "rms_db": round(_db(rms), 2),
                "samples": sample_count,
            }
    return result


def _srt_seconds(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, milliseconds = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000.0


def inspect_srt(path: Path, video_duration: float) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})"
    )
    cues = []
    for match in pattern.finditer(text):
        start = _srt_seconds(match.group(1))
        end = _srt_seconds(match.group(2))
        cues.append((start, end))
    total = sum(max(0.0, end - start) for start, end in cues)
    coverage = total / video_duration if video_duration > 0 else 0.0
    return {
        "path": str(path),
        "cues": len(cues),
        "first_start": round(cues[0][0], 2) if cues else None,
        "last_end": round(cues[-1][1], 2) if cues else None,
        "coverage": round(coverage, 3),
    }


def extract_frames(path: Path, times: list[float]) -> list[Any]:
    import av
    from PIL import Image

    frames: list[tuple[float, Image.Image]] = []
    with av.open(str(path)) as container:
        stream = next((s for s in container.streams if s.type == "video"), None)
        if stream is None:
            return frames
        for target in times:
            try:
                # When a stream is passed, PyAV interprets the offset in that
                # stream's time base, not in AV_TIME_BASE.
                container.seek(
                    max(0, int(target / float(stream.time_base))),
                    stream=stream,
                    backward=True,
                )
            except Exception:
                container.seek(0)
            chosen = None
            for frame in container.decode(stream):
                frame_time = (
                    float(frame.pts * stream.time_base)
                    if frame.pts is not None
                    else 0.0
                )
                if frame_time + 1e-6 >= target:
                    chosen = frame
                    break
            if chosen is None:
                continue
            image = chosen.to_image().convert("RGB")
            frames.append((target, image))
    return frames


def make_contact_sheet(frames: list[tuple[float, Any]], out_path: Path, columns: int = 5) -> None:
    from PIL import Image, ImageDraw, ImageFont

    if not frames:
        return
    width = 480
    thumbs = []
    for target, image in frames:
        ratio = width / image.width
        thumb = image.resize((width, int(image.height * ratio)), Image.LANCZOS)
        canvas = Image.new("RGB", (width, thumb.height + 28), (18, 18, 20))
        canvas.paste(thumb, (0, 28))
        draw = ImageDraw.Draw(canvas)
        draw.text((10, 7), f"{target:0.1f}s", fill=(235, 235, 235), font=ImageFont.load_default())
        thumbs.append(canvas)
    columns = max(1, min(columns, len(thumbs)))
    rows = math.ceil(len(thumbs) / columns)
    cell_width = max(thumb.width for thumb in thumbs)
    cell_height = max(thumb.height for thumb in thumbs)
    sheet = Image.new("RGB", (cell_width * columns, cell_height * rows), (12, 12, 14))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((index % columns) * cell_width, (index // columns) * cell_height))
    sheet.save(out_path, quality=92)


def brightness_report(frames: list[tuple[float, Any]]) -> dict[str, Any]:
    values = []
    for target, image in frames:
        array = np.asarray(image.convert("L"), dtype=np.float32)
        values.append((target, float(array.mean())))
    return {"frames": [{"time": time, "mean_luma": round(value, 2)} for time, value in values]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--video", required=True, help="Rendered MP4/WebM file")
    parser.add_argument("--srt", help="Subtitle file")
    parser.add_argument("--out-dir", help="QA output directory (default: <video parent>/qa)")
    parser.add_argument("--target-duration", type=float, help="Expected duration in seconds")
    parser.add_argument("--width", type=int, help="Expected width")
    parser.add_argument("--height", type=int, help="Expected height")
    parser.add_argument("--fps", type=float, help="Expected frame rate")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args(argv)

    video = Path(args.video).resolve()
    if not video.exists():
        print(f"Video not found: {video}", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir).resolve() if args.out_dir else video.parent / "qa"
    out_dir.mkdir(parents=True, exist_ok=True)

    warnings: list[str] = []
    failures: list[str] = []

    try:
        media = inspect_media(video)
    except ImportError:
        print("PyAV is required for QA. Install it with: python -m pip install av", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Could not inspect {video}: {exc}", file=sys.stderr)
        return 2

    duration = float(media["duration"])
    if duration <= 0:
        failures.append("Video duration is zero or unknown.")
    if media.get("video") is None:
        failures.append("No video stream found.")
    else:
        video_info = media["video"]
        if args.width and video_info["width"] != args.width:
            failures.append(f"Width {video_info['width']} != expected {args.width}.")
        if args.height and video_info["height"] != args.height:
            failures.append(f"Height {video_info['height']} != expected {args.height}.")
        if args.fps and video_info.get("fps") and abs(video_info["fps"] - args.fps) > 0.5:
            warnings.append(f"FPS {video_info['fps']} != expected {args.fps}.")
    if media.get("audio") is None:
        failures.append("No audio stream found. Narration will not play.")
    else:
        stats = media.get("audio_stats") or {}
        peak = float(stats.get("peak_db", -120))
        rms = float(stats.get("rms_db", -120))
        if peak <= -60:
            failures.append("Audio is effectively silent (peak <= -60 dB).")
        elif peak < -30:
            warnings.append(f"Audio peak is low ({peak:.1f} dB).")
        if peak > -0.1:
            warnings.append("Audio may be clipping (peak > -0.1 dB).")
        if rms < -45:
            warnings.append(f"Audio RMS is low ({rms:.1f} dB).")
    if args.target_duration and duration > 0:
        drift = (duration - args.target_duration) / max(1.0, args.target_duration)
        if abs(drift) > 0.25:
            warnings.append(
                f"Video duration {duration:.1f}s is {drift:+.0%} versus target {args.target_duration:.1f}s."
            )

    srt_info = None
    if args.srt:
        srt_path = Path(args.srt).resolve()
        if not srt_path.exists():
            warnings.append(f"Subtitle file not found: {srt_path}")
        else:
            srt_info = inspect_srt(srt_path, duration)
            if srt_info["cues"] == 0:
                warnings.append("Subtitle file has no cues.")
            elif srt_info["coverage"] < 0.6:
                warnings.append(
                    f"Subtitles cover only {srt_info['coverage']:.0%} of the video; check the narration/captions."
                )
    else:
        warnings.append("No subtitle file was provided for QA.")

    frames: list[tuple[float, Any]] = []
    brightness = {"frames": []}
    contact_sheet = None
    try:
        if duration > 1:
            times = [duration * fraction for fraction in (0.05, 0.25, 0.5, 0.75, 0.95)]
            frames = extract_frames(video, times)
            contact_sheet = out_dir / "contact_sheet.jpg"
            make_contact_sheet(frames, contact_sheet)
            brightness = brightness_report(frames)
            for item in brightness["frames"]:
                if item["mean_luma"] < 8:
                    warnings.append(f"Frame at {item['time']:.1f}s is nearly black.")
                elif item["mean_luma"] > 247:
                    warnings.append(f"Frame at {item['time']:.1f}s is nearly white.")
    except ImportError:
        warnings.append("Pillow is not installed; contact sheet skipped.")
    except Exception as exc:  # noqa: BLE001 - QA should still produce a report
        warnings.append(f"Contact sheet extraction failed: {exc}")

    report = {
        "schema_version": 1,
        "created_at": now_iso(),
        "video": media,
        "subtitles": srt_info,
        "brightness": brightness,
        "contact_sheet": str(contact_sheet) if contact_sheet else None,
        "expected": {
            "width": args.width,
            "height": args.height,
            "fps": args.fps,
            "target_duration": args.target_duration,
        },
        "failures": failures,
        "warnings": warnings,
        "ok": not failures,
    }
    atomic_write_json(out_dir / "report.json", report)

    lines = [
        f"# QA report — {video.name}",
        "",
        f"- Created: {report['created_at']}",
        f"- Duration: {duration:.2f}s",
        f"- Resolution: {(media.get('video') or {}).get('width')}x{(media.get('video') or {}).get('height')}",
        f"- FPS: {(media.get('video') or {}).get('fps')}",
        f"- Audio: {(media.get('audio') or {}).get('codec')} {(media.get('audio') or {}).get('sample_rate')} Hz",
        f"- Audio peak / RMS: {(media.get('audio_stats') or {}).get('peak_db')} dB / {(media.get('audio_stats') or {}).get('rms_db')} dB",
        f"- Subtitles: {srt_info['cues'] if srt_info else 'not checked'} cues"
        + (f", {srt_info['coverage']:.0%} coverage" if srt_info else ""),
        f"- Contact sheet: {contact_sheet if contact_sheet else 'not generated'}",
        "",
        "## Failures",
        "",
    ]
    lines.extend([f"- {item}" for item in failures] or ["- None."])
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in warnings] or ["- None."])
    lines.extend(["", "## Brightness", ""])
    for item in brightness["frames"]:
        lines.append(f"- {item['time']:.1f}s: mean luma {item['mean_luma']:.1f}")
    write_text(out_dir / "report.md", "\n".join(lines) + "\n")

    print(f"Wrote {out_dir / 'report.json'}")
    print(f"Wrote {out_dir / 'report.md'}")
    if contact_sheet:
        print(f"Wrote {contact_sheet}")
    if failures:
        print("\nFAILURES:")
        for item in failures:
            print(f"  ✗ {item}")
    if warnings:
        print("\nWARNINGS:")
        for item in warnings:
            print(f"  ! {item}")
    if failures or (args.strict and warnings):
        return 1
    print("\nQA passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
