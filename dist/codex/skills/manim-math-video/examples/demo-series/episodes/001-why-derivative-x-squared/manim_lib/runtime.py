"""Storyboard-driven Manim scene runtime.

The generated ``episode.py`` subclasses :class:`StoryboardScene` and points it at
the episode's ``storyboard.json``, ``brief.json``, ``theme.json``, and
``voice/manifest.json``.
"""

from __future__ import annotations

import json
import logging
import math
import re
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from manim import *  # noqa: F403 - Manim public API is the scene vocabulary
from manim import logger


from .graphs import GraphBuilder, GraphBundle, GraphSpecError
from .narration import VoiceManifest, VoiceoverTracker, caption_timings
from .theme import Theme

LOGGER = logging.getLogger(__name__)


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def latex_available() -> bool:
    return bool(shutil.which("latex") or shutil.which("xelatex"))


_SUPERSCRIPT = str.maketrans("0123456789+-=()nxi", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿˣⁱ")
_SUBSCRIPT = str.maketrans("0123456789+-=()", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")
_GREEK = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "theta": "θ",
    "lambda": "λ",
    "mu": "μ",
    "pi": "π",
    "rho": "ρ",
    "sigma": "σ",
    "tau": "τ",
    "phi": "φ",
    "omega": "ω",
    "Delta": "Δ",
    "Sigma": "Σ",
    "Omega": "Ω",
}


def _take_group(text: str, open_index: int) -> tuple[str, int]:
    """Return the braced group starting at ``open_index`` and the next index."""
    if open_index >= len(text) or text[open_index] != "{":
        return "", open_index
    depth = 0
    chars: list[str] = []
    for index in range(open_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
            if depth == 1:
                continue
        elif char == "}":
            depth -= 1
            if depth == 0:
                return "".join(chars), index + 1
        chars.append(char)
    return "".join(chars), len(text)


def _latex_fallback(latex: str) -> str:
    """A deliberately small LaTeX-to-Unicode approximation for silent drafts."""
    text = str(latex)
    # \frac{a}{b} -> (a)/(b)
    while "\\frac" in text:
        start = text.index("\\frac")
        numerator, after_num = _take_group(text, start + 5)
        denominator, after_den = _take_group(text, after_num)
        if not numerator and not denominator:
            break
        text = text[:start] + f"({numerator})/({denominator})" + text[after_den:]
    text = re.sub(r"\frac(\d)(\d)", lambda m: f"{m.group(1)}/{m.group(2)}", text)
    # \sqrt{a} -> √(a)
    while "\\sqrt" in text:
        start = text.index("\\sqrt")
        radicand, after = _take_group(text, start + 5)
        text = text[:start] + f"√({radicand})" + text[after:]
    replacements = {
        "\\lim": "lim",
        "\\to": "→",
        "\\rightarrow": "→",
        "\\infty": "∞",
        "\\cdot": "·",
        "\\times": "×",
        "\\div": "÷",
        "\\pm": "±",
        "\\leq": "≤",
        "\\le": "≤",
        "\\geq": "≥",
        "\\ge": "≥",
        "\\neq": "≠",
        "\\approx": "≈",
        "\\sum": "Σ",
        "\\int": "∫",
        "\\partial": "∂",
        "\\left": "",
        "\\right": "",
        "\\,": " ",
        "\\!": "",
        "\\;": " ",
        "\\ ": " ",
        "\\quad": "  ",
        "\\qquad": "    ",
    }
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    for name, symbol in _GREEK.items():
        text = re.sub(rf"\\{name}\b", symbol, text)
    # Simple superscripts/subscripts.
    text = re.sub(r"\^\{([0-9+\-=()nxi]+)\}", lambda m: m.group(1).translate(_SUPERSCRIPT), text)
    text = re.sub(r"_\{([0-9+\-=()]+)\}", lambda m: m.group(1).translate(_SUBSCRIPT), text)
    text = re.sub(r"\^([0-9+\-=()nxi])", lambda m: m.group(1).translate(_SUPERSCRIPT), text)
    text = re.sub(r"_([0-9+\-=()])", lambda m: m.group(1).translate(_SUBSCRIPT), text)
    text = text.replace("{", "").replace("}", "").strip()
    return text


class StoryboardScene(Scene):
    """Render every standard beat in a storyboard with synchronized narration."""

    storyboard_file = "storyboard.json"
    brief_file = "brief.json"
    theme_file = "theme.json"
    voice_file = "voice/manifest.json"
    root_dir: Path | str | None = None

    def setup(self) -> None:
        super().setup()
        self.root = Path(self.root_dir or Path.cwd()).resolve()
        self.storyboard = _read_json(self.root / self.storyboard_file)
        self.brief = _read_json(self.root / self.brief_file)
        self.theme = Theme.load(self.root / self.theme_file)
        self.voice = VoiceManifest.load(self.root / self.voice_file)
        self.aspect_ratio = str(
            self.brief.get("episode", {}).get("aspect_ratio")
            or self.theme.aspect_ratio
            or "16:9"
        )
        frames = {
            "16:9": (14.222, 8.0),
            "9:16": (8.0, 14.222),
            "1:1": (8.0, 8.0),
            "4:3": (10.6667, 8.0),
        }
        frame_width, frame_height = frames.get(self.aspect_ratio, frames["16:9"])
        config.frame_width = frame_width
        config.frame_height = frame_height
        self.camera.frame_width = frame_width
        self.camera.frame_height = frame_height
        self.camera.max_allowable_norm = frame_width
        try:
            self.camera.resize_frame_shape()
            config.frame_width = self.camera.frame_width
            config.frame_height = self.camera.frame_height
        except Exception:
            pass
        self.camera.background_color = self.theme.color("background")
        self.latex_available = latex_available()
        self.latex_fallback = bool(
            self.brief.get("output", {}).get("latex_fallback", False)
        )
        if not self.latex_available and not self.latex_fallback:
            has_equations = any(
                beat.get("kind") == "equation"
                for beat in self.storyboard.get("beats", [])
            )
            if has_equations:
                raise RuntimeError(
                    "This storyboard contains equation beats, but LaTeX is not on PATH. "
                    "Install a LaTeX distribution (see references/troubleshooting.md) or set "
                    "output.latex_fallback=true for a draft-only Unicode approximation."
                )
        self.graph_builder = GraphBuilder(self.theme, self.latex_available)
        self._music_started = False
        self._warned_aspect = False

    # ------------------------------------------------------------------ entry
    def construct(self) -> None:
        self._start_music()
        beats = self.storyboard.get("beats", [])
        if not beats:
            raise ValueError("storyboard.json has no beats.")
        seen: set[str] = set()
        for beat in beats:
            beat_id = str(beat.get("id", ""))
            if not beat_id:
                raise ValueError("Every beat needs an id.")
            if beat_id in seen:
                raise ValueError(f"Duplicate beat id {beat_id!r}.")
            seen.add(beat_id)
            kind = str(beat.get("kind", ""))
            handler = getattr(self, f"render_{kind}", None)
            if handler is None:
                raise ValueError(
                    f"Unsupported beat kind {kind!r} for {beat_id!r}. "
                    "Use a documented kind or a custom beat."
                )
            with self.voiceover(beat_id) as vo:
                handler(beat, vo)
            if bool(beat.get("clear", True)):
                self._transition_out()

    def _start_music(self) -> None:
        music = self.brief.get("output", {}).get("music")
        if not music:
            return
        path = Path(str(music))
        if not path.is_absolute():
            path = self.root / path
        if not path.exists():
            logger.warning("Music file not found, skipping: %s", path)
            return
        gain = float(self.brief.get("output", {}).get("music_gain_db", -24))
        self.add_sound(str(path), gain=gain)
        self._music_started = True
        logger.info("Added background music %s at %.1f dB", path, gain)

    def _transition_out(self) -> None:
        visuals = [
            mob
            for mob in self.mobjects
            if isinstance(mob, Mobject) and not isinstance(mob, ValueTracker)
        ]
        if not visuals:
            return
        transition = str(self.theme.motion("transition", "fade"))
        duration = float(self.theme.motion("transition_time", 0.28))
        if transition == "none" or duration <= 0:
            self.clear()
        else:
            self.play(FadeOut(Group(*visuals)), run_time=duration)
        self.remove(*[mob for mob in self.mobjects if isinstance(mob, ValueTracker)])

    # ------------------------------------------------------------------ voice
    @contextmanager
    def voiceover(self, segment_id: str, pad: float | None = None):
        segment = self.voice.get(segment_id)
        tail = float(self.theme.captions("tail_pad", 0.15) if pad is None else pad)
        if segment.audio is not None and segment.audio.exists():
            self.add_sound(str(segment.audio))
        elif segment.audio is not None:
            logger.warning("Narration audio missing for %s: %s", segment_id, segment.audio)
        if bool(self.brief.get("output", {}).get("captions", True)) and self.theme.captions(
            "enabled", True
        ):
            max_chars = int(self.theme.captions("max_chars", 84))
            for cue, offset, duration in caption_timings(
                segment.caption, segment.duration, max_chars=max_chars
            ):
                self.add_subcaption(cue, duration=duration, offset=offset)
        tracker = VoiceoverTracker(self, segment, pad=tail)
        try:
            yield tracker
        except Exception:
            raise
        else:
            remaining = tracker.duration + tracker.pad - tracker.elapsed
            if remaining > 0:
                self.wait(remaining)

    # ------------------------------------------------------------------ width
    def _content_width(self) -> float:
        margin = float(self.theme.layout("margin", 0.7))
        return max(
            1.0,
            min(
                float(self.theme.layout("text_max_width", 11.5)),
                float(config.frame_width) - 2 * margin,
            ),
        )

    # ------------------------------------------------------------------ text
    def _text(
        self,
        text: str,
        size_kind: str = "body",
        color: str = "ink",
        font_kind: str = "body",
        *,
        default_size: float = 30,
        slant: str = "NORMAL",
    ) -> Text:
        mob = Text(
            str(text),
            font=self.theme.font(font_kind),
            font_size=self.theme.size(size_kind, default_size),
            color=self.theme.color(color),
            slant=slant,
        )
        return self._fit_width(mob, self._content_width())

    def _fit_width(self, mob: Mobject, max_width: float) -> Mobject:
        if mob.width > max_width > 0:
            mob.scale_to_fit_width(max_width)
        return mob

    def _max_chars(self, font_size: float, max_width: float | None = None) -> int:
        width = float(max_width if max_width is not None else self._content_width())
        return max(18, int(width / max(0.0085 * font_size, 0.12)))

    def _wrapped_text(
        self,
        text: str,
        size_kind: str = "body",
        color: str = "ink",
        font_kind: str = "body",
        *,
        default_size: float = 30,
        max_width: float | None = None,
        font_size_override: float | None = None,
    ) -> Mobject:
        width = float(max_width if max_width is not None else self._content_width())
        font_size = float(
            font_size_override
            if font_size_override is not None
            else self.theme.size(size_kind, default_size)
        )
        max_chars = self._max_chars(font_size, width)
        raw_lines: list[str] = []
        for paragraph in str(text).split("\n"):
            words = paragraph.split()
            current = ""
            for word in words:
                if not current:
                    current = word
                elif len(current) + 1 + len(word) <= max_chars:
                    current = f"{current} {word}"
                else:
                    raw_lines.append(current)
                    current = word
            if current:
                raw_lines.append(current)
        if not raw_lines:
            raw_lines = [""]
        if len(raw_lines) == 1:
            mob = Text(
                raw_lines[0],
                font=self.theme.font(font_kind),
                font_size=font_size,
                color=self.theme.color(color),
            )
            return self._fit_width(mob, width)
        mob = Paragraph(
            *raw_lines,
            font=self.theme.font(font_kind),
            font_size=font_size,
            color=self.theme.color(color),
            alignment="left",
            line_spacing=0.45,
        )
        return self._fit_width(mob, width)

    def _heading(
        self,
        heading: str | None,
        subheading: str | None = None,
        *,
        number: str | None = None,
    ) -> VGroup:
        group = VGroup()
        if not heading and not subheading and not number:
            return group
        max_width = self._content_width()
        if number:
            number_mob = Text(
                str(number),
                font=self.theme.font("body"),
                font_size=self.theme.size("body", 30) * 0.62,
                color=self.theme.color("primary"),
            )
            group.add(number_mob)
        if heading:
            heading_mob = Text(
                str(heading),
                font=self.theme.font("heading"),
                font_size=self.theme.size("heading", 44),
                color=self.theme.color("ink"),
            )
            self._fit_width(heading_mob, max_width)
            group.add(heading_mob)
        rule = Line(
            np.array([0.0, 0.0, 0.0]),
            np.array([1.15, 0.0, 0.0]),
            color=self.theme.color("primary"),
            stroke_width=3.0,
        )
        group.add(rule)
        if subheading:
            sub_mob = self._wrapped_text(
                str(subheading),
                size_kind="body",
                color="muted",
                default_size=30,
                max_width=max_width,
            )
            sub_mob.scale(0.82)
            group.add(sub_mob)
        group.arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        group.to_edge(UP, buff=float(self.theme.layout("heading_top_buff", 0.45)))
        group.to_edge(LEFT, buff=float(self.theme.layout("margin", 0.7)))
        return group

    def _add_heading(
        self,
        heading: str | None,
        subheading: str | None = None,
        *,
        number: str | None = None,
        animate: bool = True,
        run_time: float = 0.8,
    ) -> VGroup:
        group = self._heading(heading, subheading, number=number)
        if len(group) == 0:
            return group
        if animate:
            self.play(FadeIn(group, shift=DOWN * 0.15), run_time=run_time)
        else:
            self.add(group)
        return group

    def _place_below(self, content: Mobject, heading: VGroup | None, buff: float = 0.5) -> Mobject:
        margin = float(self.theme.layout("margin", 0.7))
        has_heading = heading is not None and len(heading) > 0
        if has_heading:
            content.next_to(heading, DOWN, buff=buff)
        else:
            content.move_to(ORIGIN)
        available = content.get_top()[1] - (-float(config.frame_height) / 2 + margin)
        if content.height > available > 0:
            content.scale_to_fit_height(available)
            if has_heading:
                content.next_to(heading, DOWN, buff=buff)
            else:
                content.move_to(ORIGIN)
        if content.get_bottom()[1] < -float(config.frame_height) / 2 + margin:
            content.shift(UP * (-float(config.frame_height) / 2 + margin - content.get_bottom()[1]))
        content.set_x(0)
        return content

    def _bullet_list(
        self,
        items: Iterable[Any],
        *,
        role: str = "primary",
        size: float | None = None,
        max_width: float | None = None,
    ) -> VGroup:
        rows = VGroup()
        color = self.theme.role(role, "primary")
        width = float(max_width if max_width is not None else self._content_width())
        font_size = float(size if size is not None else self.theme.size("bullet", 30))
        for item in items:
            if isinstance(item, dict):
                text = str(item.get("text", ""))
                item_role = str(item.get("role", role))
                emphasis = bool(item.get("emphasis", False))
            else:
                text = str(item)
                item_role = role
                emphasis = False
            marker = Dot(radius=0.045, color=self.theme.role(item_role, "primary"))
            text_mob = self._wrapped_text(
                text,
                size_kind="bullet",
                color="ink",
                default_size=font_size,
                max_width=width - 0.45,
                font_size_override=font_size,
            )
            if emphasis:
                text_mob.set_color(self.theme.role(item_role, "primary"))
            row = VGroup(marker, text_mob).arrange(RIGHT, aligned_edge=UP, buff=0.2)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=float(self.theme.layout("bullet_spacing", 0.35)))
        self._fit_width(rows, width)
        return rows

    def _animate_reveal(self, mob: Mobject, vo: VoiceoverTracker, *, lag: float = 0.18) -> None:
        run_time = max(0.7, min(3.0, vo.duration * 0.5))
        if isinstance(mob, VGroup) and len(mob) > 1:
            self.play(
                LaggedStart(*[FadeIn(part, shift=RIGHT * 0.15) for part in mob], lag_ratio=lag),
                run_time=run_time,
            )
        else:
            self.play(FadeIn(mob, shift=DOWN * 0.1), run_time=run_time)

    # ------------------------------------------------------------------ beats
    def render_title(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        series = self.brief.get("series", {})
        episode = self.brief.get("episode", {})
        kicker = beat.get("kicker")
        if not kicker:
            kicker = f"{series.get('title', '')} · S{int(series.get('season', 1)):02d}E{int(series.get('episode_number', 1)):03d}"
        title_text = str(beat.get("title", episode.get("title", "")))
        subtitle = beat.get("subtitle")
        max_width = self._content_width()
        kicker_mob = Text(
            str(kicker),
            font=self.theme.font("body"),
            font_size=self.theme.size("body", 30) * 0.66,
            color=self.theme.color("muted"),
        )
        self._fit_width(kicker_mob, max_width)
        title_mob = Text(
            title_text,
            font=self.theme.font("heading"),
            font_size=self.theme.size("title", 58),
            color=self.theme.color("ink"),
        )
        self._fit_width(title_mob, max_width)
        rule = Line(ORIGIN, RIGHT * 1.8, color=self.theme.color("primary"), stroke_width=3.5)
        group = VGroup(kicker_mob, title_mob, rule)
        if subtitle:
            subtitle_mob = self._wrapped_text(
                str(subtitle),
                size_kind="heading",
                color="muted",
                default_size=44,
                max_width=max_width,
            )
            subtitle_mob.scale(0.55)
            group.add(subtitle_mob)
        group.arrange(DOWN, buff=0.24, aligned_edge=LEFT)
        group.move_to(np.array([0.0, 0.0, 0.0]))
        run_time = max(0.9, min(3.2, vo.duration * 0.58))
        self.play(FadeIn(kicker_mob, shift=UP * 0.2), run_time=run_time * 0.35)
        self.play(Write(title_mob), run_time=run_time * 0.55)
        self.play(Create(rule), run_time=run_time * 0.3)
        if subtitle:
            self.play(FadeIn(group[-1], shift=UP * 0.1), run_time=run_time * 0.3)

    def render_section(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = self._add_heading(
            beat.get("heading", ""),
            beat.get("subheading"),
            number=beat.get("number"),
            run_time=max(0.6, min(1.4, vo.duration * 0.3)),
        )
        # A section card is mostly typography: hold the heading and let narration carry it.
        if heading.height > 0:
            self.wait(max(0.0, min(0.6, vo.remaining * 0.2)))

    def render_bullets(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = self._add_heading(
            beat.get("heading"),
            beat.get("subheading"),
            run_time=max(0.5, min(1.0, vo.duration * 0.18)),
        )
        items = beat.get("items", [])
        rows = self._bullet_list(items)
        self._place_below(rows, heading, buff=0.55)
        reveal = str(beat.get("reveal", "one_by_one"))
        if reveal == "all":
            self.play(FadeIn(rows, shift=DOWN * 0.15), run_time=max(0.7, min(2.2, vo.duration * 0.4)))
        else:
            self._animate_reveal(rows, vo, lag=float(self.theme.motion("reveal_lag", 0.18)))

    def _math_mobject(
        self,
        latex: str,
        *,
        size: float | None = None,
        highlights: Iterable[str] | None = None,
    ) -> Mobject:
        size = float(size if size is not None else self.theme.size("equation", 46))
        if self.latex_available:
            highlights = [str(term) for term in (highlights or []) if str(term)]
            kwargs: dict[str, Any] = {
                "font_size": size,
                "color": self.theme.color("ink"),
            }
            if highlights:
                kwargs["substrings_to_isolate"] = highlights
                kwargs["tex_to_color_map"] = {
                    term: self.theme.color("primary") for term in highlights
                }
            return MathTex(str(latex), **kwargs)
        if not self.latex_fallback:
            raise RuntimeError(
                "LaTeX is required for equation beats. Install LaTeX or set "
                "output.latex_fallback=true for a draft."
            )
        logger.warning("LaTeX unavailable; using a Unicode approximation for an equation.")
        return Text(
            _latex_fallback(str(latex)),
            font=self.theme.font("mono"),
            font_size=size * 0.8,
            color=self.theme.color("ink"),
        )

    def _highlight_math(self, mob: Mobject, highlights: Iterable[str]) -> None:
        if not self.latex_available or not isinstance(mob, MathTex):
            return
        color = self.theme.color("primary")
        for term in highlights:
            try:
                mob.set_color_by_tex(str(term), color)
            except Exception:
                LOGGER.debug("Could not color equation term %s", term)

    def render_equation(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = self._add_heading(
            beat.get("heading"),
            run_time=max(0.5, min(1.0, vo.duration * 0.16)),
        )
        highlights = list(beat.get("highlight") or [])
        equation = self._math_mobject(str(beat.get("latex", "")), highlights=highlights)
        self._fit_width(equation, self._content_width())
        self._place_below(equation, heading, buff=0.8)
        intro_time = max(0.6, min(2.0, vo.duration * 0.25))
        self.play(Write(equation), run_time=intro_time)

        steps = beat.get("steps") or []
        if steps:
            per_step = max(0.55, min(1.7, (vo.duration * 0.6) / max(1, len(steps))))
            current = equation
            for step_latex in steps:
                next_mob = self._math_mobject(str(step_latex), highlights=highlights)
                self._fit_width(next_mob, self._content_width())
                self._place_below(next_mob, heading, buff=0.8)
                try:
                    self.play(TransformMatchingTex(current, next_mob), run_time=per_step)
                except Exception:
                    self.play(ReplacementTransform(current, next_mob), run_time=per_step)
                current = next_mob
            equation = current

        note = beat.get("note")
        if note:
            note_mob = self._wrapped_text(
                str(note),
                size_kind="body",
                color="muted",
                default_size=30,
                max_width=self._content_width(),
            )
            note_mob.scale(0.72)
            note_mob.next_to(equation, DOWN, buff=0.4)
            if note_mob.get_bottom()[1] < -float(config.frame_height) / 2 + 0.4:
                note_mob.shift(UP * (-float(config.frame_height) / 2 + 0.4 - note_mob.get_bottom()[1]))
            self.play(FadeIn(note_mob), run_time=0.5)

    def _path_from_plot(self, plot: Mobject) -> Mobject | None:
        if isinstance(plot, VGroup):
            for submob in plot.submobjects:
                if isinstance(submob, VGroup):
                    path = self._path_from_plot(submob)
                    if path is not None:
                        return path
                elif len(submob.points) > 1:
                    return submob
            return None
        if len(plot.points) > 1:
            return plot
        return None

    def _graph_intro(self, bundle: GraphBundle, vo: VoiceoverTracker) -> None:
        intro = max(0.5, min(1.2, vo.duration * 0.16))
        self.play(
            Create(bundle.axes),
            FadeIn(bundle.ticks),
            FadeIn(bundle.axis_labels),
            run_time=intro,
        )
        if bundle.plots:
            plot_time = max(0.8, min(2.6, vo.duration * 0.3))
            plot_animations = []
            for plot in bundle.plots:
                if isinstance(plot, VGroup):
                    plot_animations.append(FadeIn(plot))
                else:
                    plot_animations.append(Create(plot))
            self.play(LaggedStart(*plot_animations, lag_ratio=0.15), run_time=plot_time)
        if len(bundle.annotations) > 0:
            self.play(FadeIn(bundle.annotations), run_time=max(0.4, min(1.2, vo.duration * 0.16)))
        if bundle.legend is not None:
            self.play(FadeIn(bundle.legend), run_time=0.4)

    def render_graph(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        spec = beat.get("graph") or {}
        bundle = self.graph_builder.build(spec)
        heading = None
        if beat.get("heading"):
            heading = self._add_heading(
                beat.get("heading"),
                run_time=max(0.5, min(1.0, vo.duration * 0.15)),
            )
        if heading is not None:
            self._place_below(bundle.group, heading, buff=0.35)
        else:
            bundle.group.move_to(np.array([0.0, float(self.theme.layout("graph_center_y", -0.75)), 0.0]))
        animation = spec.get("animation", "draw")
        if isinstance(animation, str):
            animation = {"type": animation}
        animation_type = str(animation.get("type", "draw")).lower()

        if animation_type == "none":
            self.add(bundle.group)
            return

        if bundle.grid is not None:
            self.add(bundle.grid)

        if animation_type == "secant_to_tangent":
            self._graph_intro(bundle, vo)
            moving_group, tracker, final_tangent = self.graph_builder.make_secant_to_tangent(
                bundle,
                x0=float(animation.get("x", 1.0)),
                h_start=float(animation.get("h_start", 1.5)),
                h_end=float(animation.get("h_end", 0.02)),
                show_triangle=bool(animation.get("show_triangle", True)),
            )
            self.add(moving_group, tracker)
            run_time = max(1.0, min(5.0, vo.remaining * 0.82))
            self.play(tracker.animate.set_value(float(animation.get("h_end", 0.02))), run_time=run_time)
            self.play(final_tangent.animate.set_opacity(1.0), run_time=0.5)
            return

        if animation_type == "riemann":
            self._graph_intro(bundle, vo)
            groups = self.graph_builder.make_riemann_groups(
                bundle,
                x1=float(animation.get("x1", 0.0)),
                x2=float(animation.get("x2", 1.0)),
                steps=[int(step) for step in animation.get("steps", [4, 8, 16, 32])],
                expr=animation.get("expr"),
            )
            if not groups:
                return
            current = groups[0]
            self.add(current)
            run_time = max(0.8, min(1.5, vo.remaining * 0.7 / max(1, len(groups) - 1)))
            for next_group in groups[1:]:
                self.play(Transform(current, next_group), run_time=run_time)
            return

        self._graph_intro(bundle, vo)

        if animation_type == "sweep" and bundle.plots:
            path = self._path_from_plot(bundle.plots[int(animation.get("plot", 0))])
            if path is not None:
                dot = Dot(
                    path.points[0],
                    color=self.theme.color("secondary"),
                    radius=float(self.theme.graph_style("dot_radius", 0.07)) * 1.2,
                )
                self.add(dot)
                sweep_time = animation.get("run_time")
                if sweep_time is None:
                    sweep_time = max(0.8, min(5.0, vo.remaining * 0.8))
                self.play(MoveAlongPath(dot, path), run_time=float(sweep_time))

    def render_compare(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = self._add_heading(
            beat.get("heading"),
            run_time=max(0.5, min(1.0, vo.duration * 0.16)),
        )
        gap = float(self.theme.layout("column_gap", 0.9))
        margin = float(self.theme.layout("margin", 0.7))
        vertical = float(config.frame_height) > float(config.frame_width)
        column_width = (
            float(config.frame_width) - 2 * margin
            if vertical
            else (float(config.frame_width) - 2 * margin - gap) / 2
        )
        columns = []
        for key in ("left", "right"):
            data = beat.get(key, {})
            role = str(data.get("role", "primary"))
            heading_mob = Text(
                str(data.get("heading", "")),
                font=self.theme.font("heading"),
                font_size=self.theme.size("heading", 44) * 0.62,
                color=self.theme.role(role, "primary"),
            )
            self._fit_width(heading_mob, column_width)
            items = self._bullet_list(
                data.get("items", []),
                role=role,
                size=self.theme.size("bullet", 30) * 0.85,
                max_width=column_width,
            )
            column = VGroup(heading_mob, items).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
            self._fit_width(column, column_width)
            columns.append(column)
        if vertical:
            divider = Line(
                LEFT * 2.0,
                RIGHT * 2.0,
                color=self.theme.color("grid"),
                stroke_width=1.5,
            )
            content = VGroup(columns[0], divider, columns[1]).arrange(
                DOWN, buff=gap * 0.6, aligned_edge=LEFT
            )
        else:
            divider = Line(
                DOWN * 2.0,
                UP * 2.0,
                color=self.theme.color("grid"),
                stroke_width=1.5,
            )
            content = VGroup(columns[0], divider, columns[1]).arrange(
                RIGHT, buff=gap, aligned_edge=UP
            )
        self._place_below(content, heading, buff=0.5)
        run_time = max(0.8, min(2.6, vo.duration * 0.45))
        self.play(
            LaggedStart(
                FadeIn(columns[0], shift=RIGHT * 0.2),
                FadeIn(columns[1], shift=LEFT * 0.2),
                lag_ratio=0.25,
            ),
            run_time=run_time,
        )

    def render_recap(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = self._add_heading(
            beat.get("heading"),
            run_time=max(0.5, min(1.0, vo.duration * 0.16)),
        )
        rows = VGroup()
        max_width = self._content_width()
        for index, item in enumerate(beat.get("items", []), start=1):
            badge = Circle(
                radius=0.21,
                color=self.theme.color("primary"),
                stroke_width=2.0,
                fill_color=self.theme.color("primary"),
                fill_opacity=0.12,
            )
            number = Text(
                str(index),
                font=self.theme.font("body"),
                font_size=self.theme.size("body", 30) * 0.62,
                color=self.theme.color("primary"),
            ).move_to(badge.get_center())
            text_mob = self._wrapped_text(
                str(item),
                size_kind="bullet",
                color="ink",
                default_size=30,
                max_width=max_width - 0.75,
            )
            row = VGroup(VGroup(badge, number), text_mob).arrange(RIGHT, aligned_edge=UP, buff=0.24)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        self._fit_width(rows, max_width)
        self._place_below(rows, heading, buff=0.55)
        self._animate_reveal(rows, vo, lag=0.22)

    def render_outro(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = self._add_heading(
            beat.get("heading", "Next question"),
            run_time=max(0.5, min(1.0, vo.duration * 0.16)),
        )
        next_text = beat.get("next")
        cta = beat.get("cta")
        group = VGroup()
        if next_text:
            next_mob = Text(
                str(next_text),
                font=self.theme.font("heading"),
                font_size=self.theme.size("title", 58) * 0.58,
                color=self.theme.color("ink"),
            )
            self._fit_width(next_mob, self._content_width())
            group.add(next_mob)
        if cta:
            cta_mob = Text(
                str(cta),
                font=self.theme.font("body"),
                font_size=self.theme.size("body", 30) * 0.78,
                color=self.theme.color("muted"),
            )
            self._fit_width(cta_mob, self._content_width())
            group.add(cta_mob)
        if len(group) == 0:
            return
        group.arrange(DOWN, buff=0.35)
        self._place_below(group, heading, buff=0.8)
        self.play(
            LaggedStart(*[FadeIn(part, shift=UP * 0.15) for part in group], lag_ratio=0.2),
            run_time=max(0.8, min(2.4, vo.duration * 0.4)),
        )

    def render_quote(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = None
        if beat.get("heading"):
            heading = self._add_heading(
                beat.get("heading"),
                run_time=max(0.5, min(1.0, vo.duration * 0.15)),
            )
        quote = Text(
            f"“{beat.get('quote', '')}”",
            font=self.theme.font("heading"),
            font_size=self.theme.size("heading", 44) * 0.9,
            color=self.theme.color("ink"),
            slant="ITALIC",
        )
        self._fit_width(quote, self._content_width())
        group = VGroup(quote)
        attribution = beat.get("attribution")
        if attribution:
            attr = Text(
                f"— {attribution}",
                font=self.theme.font("body"),
                font_size=self.theme.size("body", 30) * 0.7,
                color=self.theme.color("muted"),
            )
            group.add(attr)
        group.arrange(DOWN, aligned_edge=RIGHT, buff=0.3)
        self._place_below(group, heading, buff=0.8)
        self.play(FadeIn(quote, shift=UP * 0.1), run_time=max(0.8, min(2.0, vo.duration * 0.3)))
        if attribution:
            self.play(FadeIn(group[-1]), run_time=0.4)

    def render_image(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        heading = self._add_heading(
            beat.get("heading"),
            run_time=max(0.4, min(0.8, vo.duration * 0.12)),
        )
        path = Path(str(beat.get("path", "")))
        if not path.is_absolute():
            path = self.root / path
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        image = ImageMobject(str(path))
        width = float(beat.get("width", 5.5))
        image.scale_to_fit_width(width)
        group = VGroup(image)
        label = beat.get("label")
        if label:
            label_mob = Text(
                str(label),
                font=self.theme.font("body"),
                font_size=self.theme.size("body", 30) * 0.7,
                color=self.theme.color("muted"),
            )
            self._fit_width(label_mob, self._content_width())
            group.add(label_mob)
        group.arrange(DOWN, buff=0.22)
        self._fit_width(group, self._content_width())
        self._place_below(group, heading, buff=0.45)
        self.play(FadeIn(group, shift=UP * 0.1), run_time=max(0.8, min(2.0, vo.duration * 0.3)))

    def render_custom(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        self.custom_beat(beat, vo)

    def custom_beat(self, beat: dict[str, Any], vo: VoiceoverTracker) -> None:
        raise NotImplementedError(
            f"Beat {beat.get('id')!r} is kind='custom'. Override custom_beat() in episode.py "
            "and use the supplied vo timing object."
        )
