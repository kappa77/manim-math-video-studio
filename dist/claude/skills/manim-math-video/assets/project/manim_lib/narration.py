"""Voice manifest loading and narration timing helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class WordTiming:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class VoiceSegment:
    id: str
    text: str
    caption: str
    duration: float
    audio: Path | None
    words: tuple[WordTiming, ...] = ()
    audio_hash: str | None = None


class VoiceManifest:
    def __init__(self, data: dict[str, Any], path: Path):
        self.data = data
        self.path = path
        self.root = path.parent.parent if path.parent.name == "voice" else path.parent
        self.segments: dict[str, VoiceSegment] = {}
        for raw in data.get("segments", []):
            segment_id = str(raw["id"])
            audio_path: Path | None = None
            if raw.get("audio"):
                candidate = Path(str(raw["audio"]))
                if not candidate.is_absolute():
                    candidate = (self.root / candidate).resolve()
                    if not candidate.exists():
                        candidate = (path.parent / raw["audio"]).resolve()
                audio_path = candidate
            words = tuple(
                WordTiming(
                    text=str(word.get("text", "")),
                    start=float(word.get("start", 0.0)),
                    end=float(word.get("end", 0.0)),
                )
                for word in raw.get("words", [])
            )
            self.segments[segment_id] = VoiceSegment(
                id=segment_id,
                text=str(raw.get("text", "")),
                caption=str(raw.get("caption", raw.get("text", ""))),
                duration=float(raw.get("duration", 0.0)),
                audio=audio_path,
                words=words,
                audio_hash=raw.get("audio_hash"),
            )

    @classmethod
    def load(cls, path: str | Path) -> "VoiceManifest":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(
                f"Voice manifest not found: {path}. Run scripts/tts.py for this episode first."
            )
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not data.get("segments"):
            raise ValueError(f"Voice manifest {path} has no segments.")
        return cls(data=data, path=path)

    def get(self, segment_id: str) -> VoiceSegment:
        try:
            return self.segments[segment_id]
        except KeyError as exc:
            available = ", ".join(sorted(self.segments))
            raise KeyError(
                f"No narration segment with id {segment_id!r}. Available: {available}. "
                "The storyboard and the voice manifest are out of sync; rerun tts.py."
            ) from exc

    @property
    def total_duration(self) -> float:
        return float(self.data.get("total_duration", 0.0)) or sum(
            segment.duration for segment in self.segments.values()
        )

    @property
    def language(self) -> str:
        return str(self.data.get("language", ""))

    @property
    def voice(self) -> str:
        return str(self.data.get("voice", ""))


class VoiceoverTracker:
    """Timing view passed to a beat while its narration is playing."""

    def __init__(self, scene: Any, segment: VoiceSegment, pad: float = 0.15):
        self.scene = scene
        self.segment = segment
        self.pad = max(0.0, float(pad))
        self.start_time = float(scene.renderer.time)
        self._fallback_elapsed = 0.0

    @property
    def duration(self) -> float:
        return self.segment.duration

    @property
    def elapsed(self) -> float:
        try:
            return max(0.0, float(self.scene.renderer.time) - self.start_time)
        except Exception:
            return self._fallback_elapsed

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self.elapsed)

    @property
    def budget(self) -> float:
        """Remaining narration time plus the configured tail pad."""
        return max(0.0, self.duration + self.pad - self.elapsed)

    @property
    def progress(self) -> float:
        if self.duration <= 0:
            return 1.0
        return min(1.0, max(0.0, self.elapsed / self.duration))


def split_caption(text: str, max_chars: int = 84) -> list[str]:
    """Split a caption into readable cues without cutting words."""
    text = re.sub(r"\s+", " ", str(text)).strip()
    if not text:
        return []
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]

    sentences = re.split(r"(?<=[.!?])\s+", text)
    cues: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) <= max_chars:
            if not current:
                current = sentence
            elif len(current) + 1 + len(sentence) <= max_chars:
                current = f"{current} {sentence}"
            else:
                cues.append(current)
                current = sentence
            continue

        words = sentence.split()
        for word in words:
            if not current:
                current = word
            elif len(current) + 1 + len(word) <= max_chars:
                current = f"{current} {word}"
            else:
                cues.append(current)
                current = word
        if current:
            cues.append(current)
            current = ""
    if current:
        cues.append(current)
    return cues


def caption_timings(
    caption: str,
    duration: float,
    max_chars: int = 84,
) -> list[tuple[str, float, float]]:
    """Return ``(text, offset, duration)`` cues proportional to text length."""
    cues = split_caption(caption, max_chars=max_chars)
    if not cues or duration <= 0:
        return []
    weights = [max(1, len(cue)) for cue in cues]
    total_weight = sum(weights)
    result: list[tuple[str, float, float]] = []
    offset = 0.0
    for cue, weight in zip(cues, weights):
        cue_duration = duration * weight / total_weight
        result.append((cue, offset, cue_duration))
        offset += cue_duration
    # Correct rounding drift on the last cue.
    if result:
        text, last_offset, _ = result[-1]
        result[-1] = (text, last_offset, max(0.05, duration - last_offset))
    return result


def iter_segments(manifest: VoiceManifest) -> Iterable[VoiceSegment]:
    return manifest.segments.values()
