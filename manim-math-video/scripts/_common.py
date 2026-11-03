"""Shared helpers for the manim-math-video scripts."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
TEMPLATES_DIR = ASSETS / "templates"
PROJECT_DIR = ASSETS / "project"
VOICES_PATH = ASSETS / "voices.json"
TTS_CONFIG_PATH = Path.home() / ".manim-math-video" / "tts.json"

MANIM_NAMES = ("manim.exe", "manim.cmd", "manim") if os.name == "nt" else ("manim",)


MANAGED_VENV = Path.home() / ".manim-math-video" / "venv"
#: Modules that must exist for the scripts to run; used by ensure_runtime().
RUNTIME_MODULES = ("numpy", "manim", "av", "PIL")


def _marker_venv_root() -> Path | None:
    """Environment recorded by install.py beside the skill files."""
    try:
        text = (SKILL_ROOT / ".venv-path").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return Path(text).expanduser() if text else None


def _shared_venv_roots() -> list[Path]:
    """Environments created by install.py, honoured before PATH."""
    roots: list[Path] = []
    override = os.environ.get("MANIM_STUDIO_VENV", "").strip()
    if override:
        roots.append(Path(override).expanduser())
    marker = _marker_venv_root()
    if marker is not None:
        roots.append(marker)
    roots.append(MANAGED_VENV)
    return roots


def managed_venv_python() -> Path | None:
    """Return the interpreter of the shared environment installed by install.py."""
    binary = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    for root in _shared_venv_roots():
        candidate = root / binary
        if candidate.is_file():
            return candidate
    return None


def ensure_runtime() -> None:
    """Re-exec this script with the shared environment when dependencies are missing.

    The skill is installed by ``install.py``, which prepares one environment at
    ``~/.manim-math-video/venv``. Agents often call ``python scripts/render.py``
    with whatever interpreter is on PATH, which would miss Manim and PyAV. Rather
    than failing, switch to the prepared interpreter once. Set
    ``MANIM_STUDIO_NO_REEXEC=1`` to disable.
    """
    if os.environ.get("MANIM_STUDIO_NO_REEXEC") or os.environ.get("MANIM_STUDIO_REEXEC"):
        return
    try:
        if all(importlib.util.find_spec(name) is not None for name in RUNTIME_MODULES):
            return
    except (ImportError, ValueError):
        pass
    python = managed_venv_python()
    if python is None:
        return
    try:
        # Do not use resolve(): in a venv, bin/python is usually a symlink to
        # the base interpreter, so resolving both paths would make the guard
        # think the current interpreter is already the managed one and skip
        # the re-exec on Linux and macOS.
        if os.path.normcase(os.path.abspath(str(python))) == os.path.normcase(
            os.path.abspath(sys.executable)
        ):
            return
    except OSError:
        pass
    os.environ["MANIM_STUDIO_REEXEC"] = "1"
    print(f"[manim-math-video] using the managed environment: {python}", file=sys.stderr, flush=True)
    try:
        os.execv(str(python), [str(python), *sys.argv])
    except OSError:
        pass


def _venv_script_directories() -> list[Path]:
    binary_dir = "Scripts" if os.name == "nt" else "bin"
    roots: list[Path] = []
    for base in (Path.cwd(), *Path.cwd().parents):
        roots.extend((base / ".venv", base / "venv"))
    roots.extend((SKILL_ROOT.parent / ".venv", SKILL_ROOT / ".venv", *_shared_venv_roots()))
    return [root / binary_dir for root in roots]


def find_manim_executable() -> str | None:
    """Find the Manim CLI in MANIM_BIN, the active venv, a local venv, or PATH."""
    override = os.environ.get("MANIM_BIN", "").strip()
    if override:
        candidate = Path(override).expanduser()
        if candidate.is_file():
            return str(candidate)
        resolved = shutil.which(override)
        if resolved:
            return resolved

    directories = [Path(sys.executable).parent, *_venv_script_directories()]
    seen: set[Path] = set()
    for directory in directories:
        if directory in seen:
            continue
        seen.add(directory)
        for name in MANIM_NAMES:
            candidate = directory / name
            if candidate.is_file():
                return str(candidate)
    return shutil.which("manim")
QUALITY_PRESETS: dict[str, dict[str, Any]] = {
    "draft": {
        "width": 854,
        "height": 480,
        "fps": 15,
        "suffix": "480p15",
        "label": "Draft 480p15",
    },
    "standard": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "suffix": "1080p30",
        "label": "Standard 1080p30",
    },
    "high": {
        "width": 1920,
        "height": 1080,
        "fps": 60,
        "suffix": "1080p60",
        "label": "High 1080p60",
    },
    "4k": {
        "width": 3840,
        "height": 2160,
        "fps": 60,
        "suffix": "2160p60",
        "label": "4K 2160p60",
    },
}
KINDS = {
    "title",
    "section",
    "bullets",
    "equation",
    "graph",
    "compare",
    "recap",
    "outro",
    "quote",
    "image",
    "custom",
}
GRAPH_TYPES = {"cartesian", "parametric", "data", "bars", "vector_field"}
ANNOTATION_TYPES = {
    "point",
    "dot",
    "text",
    "vertical_line",
    "vline",
    "horizontal_line",
    "hline",
    "tangent",
    "secant",
    "area",
    "integral",
    "riemann",
    "brace",
    "arrow",
    "slope_triangle",
    "derivative",
}
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
EPISODE_ID_RE = re.compile(r"^s\d{2}e\d{3}$")
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


# --------------------------------------------------------------------------- io
def load_json(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def atomic_write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    temporary.replace(path)


def write_text(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_text(text: str, length: int = 10) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def slugify(value: str) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "episode"


def episode_id(season: int, number: int) -> str:
    return f"s{int(season):02d}e{int(number):03d}"


def episode_dir_name(brief: dict[str, Any]) -> str:
    series = brief.get("series", {})
    episode = brief.get("episode", {})
    return f"{int(series.get('episode_number', 1)):03d}-{episode.get('slug') or slugify(episode.get('title', 'episode'))}"


def render_dimensions(quality: str, aspect_ratio: str = "16:9") -> tuple[int, int]:
    preset = QUALITY_PRESETS[quality]
    width, height = int(preset["width"]), int(preset["height"])
    if aspect_ratio == "9:16":
        return height, width
    if aspect_ratio == "1:1":
        return height, height
    if aspect_ratio == "4:3":
        return round(height * 4 / 3), height
    return width, height


def quality_suffix(quality: str, aspect_ratio: str = "16:9") -> str:
    width, height = render_dimensions(quality, aspect_ratio)
    if aspect_ratio == "16:9":
        return str(QUALITY_PRESETS[quality]["suffix"])
    return f"{width}x{height}"


def output_basename(
    brief: dict[str, Any],
    quality: str,
    aspect_ratio: str | None = None,
) -> str:
    series = brief.get("series", {})
    episode = brief.get("episode", {})
    eid = episode_id(series.get("season", 1), series.get("episode_number", 1))
    ratio = aspect_ratio or str(episode.get("aspect_ratio", "16:9"))
    return f"{eid}-{episode.get('slug') or slugify(episode.get('title', 'episode'))}-{quality_suffix(quality, ratio)}"


def resolve_episode(path: str | Path) -> Path:
    path = Path(path).resolve()
    if path.is_file() and path.name == "brief.json":
        path = path.parent
    if not path.exists():
        raise FileNotFoundError(f"Episode path not found: {path}")
    if not (path / "brief.json").exists():
        raise FileNotFoundError(f"No brief.json in {path}")
    return path


def find_series_root(episode_dir: str | Path) -> Path | None:
    episode_dir = Path(episode_dir).resolve()
    if episode_dir.parent.name == "episodes":
        return episode_dir.parent.parent
    return None


def latex_available() -> bool:
    return bool(shutil.which("latex") or shutil.which("xelatex"))


# --------------------------------------------------------------------------- voices
def load_voices() -> dict[str, Any]:
    return load_json(VOICES_PATH)


def normalize_language(value: str, voices: dict[str, Any] | None = None) -> str:
    voices = voices or load_voices()
    raw = str(value or "").strip()
    if not raw:
        return str(voices.get("default_language", "en-US"))
    languages: dict[str, Any] = voices.get("languages", {})
    if raw in languages:
        return raw
    needle = raw.casefold().replace("_", "-")
    for locale, info in languages.items():
        aliases = [locale.casefold(), str(info.get("label", "")).casefold()]
        aliases.extend(str(alias).casefold() for alias in info.get("aliases", []))
        if needle in aliases:
            return locale
    for locale in languages:
        if locale.casefold().split("-")[0] == needle.split("-")[0]:
            return locale
    return raw


def language_info(locale: str, voices: dict[str, Any] | None = None) -> dict[str, Any]:
    voices = voices or load_voices()
    return voices.get("languages", {}).get(locale, {})


def voice_entries(locale: str, voices: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return list(language_info(locale, voices).get("voices", []))


def load_tts_config() -> dict[str, Any]:
    """Read the provider preference written by the installer, if present."""
    try:
        data = load_json(TTS_CONFIG_PATH)
    except Exception:  # noqa: BLE001 - a missing or broken config is not fatal
        return {}
    return data if isinstance(data, dict) else {}


def provider_info(provider: str, voices: dict[str, Any] | None = None) -> dict[str, Any]:
    voices = voices or load_voices()
    return dict(voices.get("providers", {}).get(provider, {}))


def default_voice_for(
    provider: str,
    locale: str,
    voices: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> str:
    """Pick the configured/default voice, falling back to the edge catalog."""
    voices = voices or load_voices()
    if provider in {"cartesia", "elevenlabs"}:
        config = config if config is not None else load_tts_config()
        stored = config.get("providers", {})
        stored = stored.get(provider, {}) if isinstance(stored, dict) else {}
        return str(
            (stored.get("voice_id") if isinstance(stored, dict) else None)
            or provider_info(provider, voices).get("default_voice")
            or ""
        )
    return default_voice(locale, voices)


def default_voice(locale: str, voices: dict[str, Any] | None = None) -> str:
    voices = voices or load_voices()
    info = language_info(locale, voices)
    if info.get("default_voice"):
        return str(info["default_voice"])
    entries = voice_entries(locale, voices)
    if entries:
        return str(entries[0]["id"])
    fallback = voices.get("languages", {}).get(voices.get("default_language", "en-US"), {})
    return str(fallback.get("default_voice", "en-US-AvaMultilingualNeural"))


def style_defaults(style: str, voices: dict[str, Any] | None = None) -> dict[str, str]:
    voices = voices or load_voices()
    styles = voices.get("styles", {})
    data = styles.get(style) or styles.get("warm-teacher") or {}
    return {
        "rate": str(data.get("rate", "+0%")),
        "pitch": str(data.get("pitch", "+0Hz")),
        "volume": "+0%",
    }


def resolve_output(brief: dict[str, Any]) -> dict[str, Any]:
    voices = load_voices()
    output = dict(brief.get("output", {}))
    locale = normalize_language(str(output.get("language", "")), voices)
    output["language"] = locale
    voice = dict(output.get("voice", {}))
    config = load_tts_config()
    provider = str(voice.get("provider") or config.get("provider") or "edge")
    if provider == "auto":
        provider = str(config.get("provider") or "edge")
    style = str(voice.get("style") or "warm-teacher")
    defaults = style_defaults(style, voices)
    for key in ("rate", "pitch", "volume"):
        voice.setdefault(key, defaults[key])
    voice["provider"] = provider
    if not voice.get("id"):
        voice["id"] = default_voice_for(provider, locale, voices, config)
    if provider in {"cartesia", "elevenlabs"} and not voice.get("model_id"):
        stored = config.get("providers", {})
        stored = stored.get(provider, {}) if isinstance(stored, dict) else {}
        voice["model_id"] = stored.get("model_id") or provider_info(provider, voices).get(
            "default_model"
        )
    voice.setdefault("style", style)
    output["voice"] = voice
    output.setdefault("quality", "standard")
    output.setdefault("captions", True)
    output.setdefault("latex_fallback", False)
    output.setdefault("subtitle_language", locale.split("-")[0])
    return output


# --------------------------------------------------------------------------- templates
def template_path(template_id: str) -> Path:
    return TEMPLATES_DIR / f"{template_id}.json"


def load_template(template_id: str) -> dict[str, Any]:
    path = template_path(template_id)
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in TEMPLATES_DIR.glob("*.json")))
        raise FileNotFoundError(f"Template {template_id!r} not found. Available: {available}")
    return load_json(path)


def validate_template(template: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for key in ("schema_version", "id", "name", "version", "background", "ink", "roles", "fonts", "sizes", "layout", "graph", "motion", "captions", "story"):
        if key not in template:
            errors.append(f"Template is missing required key {key!r}.")
    if template.get("schema_version") != 1:
        errors.append("Template schema_version must be 1.")
    template_id = str(template.get("id", ""))
    if not ID_RE.match(template_id):
        errors.append(f"Template id {template_id!r} is not lowercase-hyphenated.")
    for key in ("background", "surface", "ink", "muted"):
        value = template.get(key)
        if value is not None and not HEX_RE.match(str(value)):
            errors.append(f"Template color {key!r} must be a #RRGGBB value.")
    for role, value in template.get("roles", {}).items():
        if not HEX_RE.match(str(value)):
            errors.append(f"Template role {role!r} must be a #RRGGBB value.")
    for font_kind, candidates in template.get("fonts", {}).items():
        if not isinstance(candidates, list) or not candidates:
            errors.append(f"Template font {font_kind!r} must be a non-empty list.")
    for key in ("heading", "body", "title", "bullet", "equation"):
        if key not in template.get("sizes", {}):
            warnings.append(f"Template sizes is missing {key!r}.")
    if template.get("aspect_ratio", "16:9") != "16:9":
        warnings.append("Non-16:9 templates use the runtime's automatic frame sizing; review a draft for layout.")
    return errors, warnings


# --------------------------------------------------------------------------- brief
def validate_brief(brief: dict[str, Any], *, check_template: bool = True) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if brief.get("schema_version") != 1:
        errors.append("brief.schema_version must be 1.")
    for section in ("series", "episode", "output", "accuracy"):
        if not isinstance(brief.get(section), dict):
            errors.append(f"brief is missing the {section!r} section.")

    series = brief.get("series", {})
    episode = brief.get("episode", {})
    output = brief.get("output", {})
    accuracy = brief.get("accuracy", {})

    for key in ("title", "slug", "season", "episode_number", "template", "premise", "audience"):
        if not series.get(key):
            errors.append(f"series.{key} is required.")
    if series.get("slug") and not SLUG_RE.match(str(series["slug"])):
        errors.append("series.slug must be lowercase, hyphenated.")
    if series.get("template") and not ID_RE.match(str(series["template"])):
        errors.append("series.template must be a lowercase-hyphenated template id.")
    elif series.get("template") and check_template:
        try:
            template = load_template(str(series["template"]))
            template_errors, template_warnings = validate_template(template)
            errors.extend(template_errors)
            warnings.extend(template_warnings)
        except FileNotFoundError as exc:
            errors.append(str(exc))

    for key in ("title", "slug", "thesis", "audience", "prerequisites", "goals", "rigor", "tone", "target_duration_seconds", "platform", "aspect_ratio", "key_points", "misconceptions", "visuals"):
        empty_list_allowed = key in {"prerequisites", "misconceptions"}
        if key not in episode or episode.get(key) in (None, "") or (episode.get(key) == [] and not empty_list_allowed):
            errors.append(f"episode.{key} is required.")
    if episode.get("slug") and not SLUG_RE.match(str(episode["slug"])):
        errors.append("episode.slug must be lowercase, hyphenated.")
    if episode.get("rigor") not in {"explanation", "narrative", "procedure", "analysis", "intuition", "sketch", "proof", "derivation"}:
        errors.append("episode.rigor must be one of explanation, narrative, procedure, analysis, intuition, sketch, proof, derivation.")
    if episode.get("aspect_ratio") not in {"16:9", "9:16", "1:1", "4:3"}:
        errors.append("episode.aspect_ratio must be 16:9, 9:16, 1:1, or 4:3.")
    duration = episode.get("target_duration_seconds")
    if not isinstance(duration, (int, float)) or duration < 30:
        errors.append("episode.target_duration_seconds must be at least 30.")
    elif duration < 90:
        warnings.append("Target duration under 90 seconds is very tight for an argument-driven episode.")
    elif duration > 1800:
        warnings.append("Target duration over 30 minutes; consider splitting into episodes.")

    quality = str(output.get("quality", "standard"))
    if quality not in QUALITY_PRESETS:
        errors.append(f"output.quality must be one of {sorted(QUALITY_PRESETS)}.")
    if not output.get("language"):
        errors.append("output.language is required.")
    else:
        resolved = normalize_language(str(output["language"]))
        if language_info(resolved) == {}:
            warnings.append(
                f"Language {output['language']!r} is not in the curated catalog; "
                "voice compatibility cannot be checked."
            )
    if not output.get("subtitle_language"):
        warnings.append("output.subtitle_language is missing; defaulting to the narration language.")
    voice = output.get("voice", {})
    provider = str(voice.get("provider", "edge"))
    if provider not in {"edge", "piper", "cartesia", "elevenlabs", "custom", "none"}:
        errors.append(
            "output.voice.provider must be edge, piper, cartesia, elevenlabs, custom, or none."
        )
    if provider in {"edge", "piper", "cartesia", "elevenlabs", "custom"} and not voice.get("id"):
        errors.append("output.voice.id is required.")
    if provider in {"cartesia", "elevenlabs"} and voice.get("id") and any(
        character.isspace() for character in str(voice["id"])
    ):
        errors.append(
            "output.voice.id must be the provider voice id, not a display name."
        )
    if provider == "piper" and not voice.get("piper_model"):
        errors.append("output.voice.piper_model is required when provider is piper.")
    if provider == "custom" and not voice.get("command"):
        errors.append("output.voice.command is required when provider is custom.")
    if provider in {"cartesia", "elevenlabs"}:
        info = provider_info(provider)
        env_name = str(info.get("api_key_env") or "")
        if env_name and not os.environ.get(env_name):
            warnings.append(
                f"{info.get('label', provider)} is selected but {env_name} is not set; "
                "narration will fail until the key is available."
            )
    locale = normalize_language(str(output.get("language", "")))
    info = language_info(locale)
    voice_id = str(voice.get("id", ""))
    if provider == "edge" and voice_id and info:
        allowed = {entry["id"] for entry in voice_entries(locale)}
        if allowed and voice_id not in allowed:
            if voice_id.split("-")[0] != locale.split("-")[0]:
                warnings.append(
                    f"Voice {voice_id!r} does not match narration locale {locale!r}; "
                    "the delivery may sound wrong or switch language."
                )
            else:
                warnings.append(
                    f"Voice {voice_id!r} is not in the curated list for {locale}; "
                    "it will be used if edge-tts recognizes it."
                )
    selection = output.get("voice_selection") or {}
    if provider != "none" and str(selection.get("status", "")).lower() != "confirmed":
        warnings.append(
            "output.voice_selection is not confirmed; obtain an explicit voice choice "
            "or confirmed series-voice reuse before generating narration."
        )
    if not output.get("captions", True):
        warnings.append("Captions are disabled; this reduces accessibility and searchability.")
    if output.get("latex_fallback"):
        warnings.append("latex_fallback is enabled; do not ship this as final mathematics.")
    if episode.get("aspect_ratio", "16:9") != "16:9":
        warnings.append("Non-16:9 layout uses automatic frame sizing; review a draft for overflow and caption fit.")

    for key in ("notation", "pronunciations", "sources", "claims_to_verify"):
        if key not in accuracy:
            warnings.append(f"accuracy.{key} is missing.")
    claims = accuracy.get("claims_to_verify") or []
    if claims:
        warnings.append(f"{len(claims)} claim(s) still need verification before publishing.")
    return errors, warnings


# --------------------------------------------------------------------------- storyboard
def _import_expr_module():
    path = PROJECT_DIR / "manim_lib" / "expr.py"
    spec = importlib.util.spec_from_file_location("manim_math_video_expr", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load expression module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def estimate_duration(storyboard: dict[str, Any], wpm: float = 145.0, tail_pad: float = 0.15) -> float:
    total = 0.0
    for beat in storyboard.get("beats", []):
        if beat.get("silent"):
            total += float(beat.get("duration_hint", 2.0))
            continue
        text = str(beat.get("speech") or beat.get("narration") or "")
        words = len(re.findall(r"\S+", text))
        total += max(1.0, words / max(1.0, wpm) * 60.0) + tail_pad
    return total


def validate_storyboard(
    storyboard: dict[str, Any],
    brief: dict[str, Any] | None = None,
    *,
    episode_dir: Path | None = None,
    check_expressions: bool = True,
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if storyboard.get("schema_version") != 1:
        errors.append("storyboard.schema_version must be 1.")
    if not EPISODE_ID_RE.match(str(storyboard.get("episode_id", ""))):
        errors.append("storyboard.episode_id must look like s01e001.")
    for key in ("title", "language", "template"):
        if not storyboard.get(key):
            errors.append(f"storyboard.{key} is required.")
    beats = storyboard.get("beats")
    if not isinstance(beats, list) or not beats:
        errors.append("storyboard.beats must be a non-empty list.")
        return errors, warnings

    try:
        expr_module = _import_expr_module() if check_expressions else None
    except Exception as exc:  # pragma: no cover - defensive
        expr_module = None
        warnings.append(f"Could not load the expression validator: {exc}")

    seen: set[str] = set()
    has_equation = False
    for index, beat in enumerate(beats, start=1):
        label = f"beat {index} ({beat.get('id', '?')})"
        beat_id = str(beat.get("id", ""))
        if not beat_id:
            errors.append(f"{label}: id is required.")
        elif not ID_RE.match(beat_id):
            errors.append(f"{label}: id must be lowercase, start with a letter/number, use - or _.")
        elif beat_id in seen:
            errors.append(f"{label}: duplicate id {beat_id!r}.")
        seen.add(beat_id)
        kind = str(beat.get("kind", ""))
        if kind not in KINDS:
            errors.append(f"{label}: unknown kind {kind!r}.")
            continue
        narration = str(beat.get("narration", "")).strip()
        if not narration and not beat.get("silent"):
            errors.append(f"{label}: narration is empty (set silent=true with duration_hint for a silent visual).")
        if beat.get("silent") and not beat.get("duration_hint"):
            errors.append(f"{label}: silent beats need duration_hint.")
        if "TODO" in json.dumps(beat, ensure_ascii=False):
            errors.append(f"{label}: contains a TODO placeholder.")
        if kind == "equation":
            has_equation = True
            if not beat.get("latex"):
                errors.append(f"{label}: equation beat needs latex.")
            if beat.get("steps") and len(beat["steps"]) > 6:
                warnings.append(f"{label}: {len(beat['steps'])} equation steps in one narration beat; split it.")
        elif kind == "graph":
            graph = beat.get("graph")
            if not isinstance(graph, dict):
                errors.append(f"{label}: graph beat needs a graph object.")
            else:
                graph_type = str(graph.get("type", ""))
                if graph_type not in GRAPH_TYPES:
                    errors.append(f"{label}: graph.type must be one of {sorted(GRAPH_TYPES)}.")
                if graph_type == "cartesian" and not (graph.get("plots") or graph.get("expr")):
                    errors.append(f"{label}: cartesian graph needs plots[] or expr.")
                if graph_type == "parametric" and not (graph.get("x_expr") and graph.get("y_expr")):
                    errors.append(f"{label}: parametric graph needs x_expr and y_expr.")
                if graph_type == "data" and not (graph.get("points") or graph.get("x_values")):
                    errors.append(f"{label}: data graph needs points[] or x_values/y_values.")
                if graph_type == "bars" and not (graph.get("categories") and graph.get("values")):
                    errors.append(f"{label}: bars graph needs categories[] and values[].")
                if graph_type == "vector_field" and not (graph.get("x_expr") and graph.get("y_expr")):
                    errors.append(f"{label}: vector_field needs x_expr and y_expr.")
                expressions: list[str] = []
                if graph.get("expr"):
                    expressions.append(str(graph["expr"]))
                for plot in graph.get("plots", []) or []:
                    if isinstance(plot, dict) and plot.get("expr"):
                        expressions.append(str(plot["expr"]))
                required_annotation_fields = {
                    "point": ("x", "y"),
                    "dot": ("x", "y"),
                    "text": ("x", "y", "text"),
                    "vertical_line": ("x",),
                    "vline": ("x",),
                    "horizontal_line": ("y",),
                    "hline": ("y",),
                    "tangent": ("x",),
                    "secant": ("x1", "x2"),
                    "area": ("x1", "x2"),
                    "integral": ("x1", "x2"),
                    "riemann": ("x1", "x2"),
                    "brace": ("x1", "x2"),
                    "arrow": ("from", "to"),
                    "slope_triangle": ("x1", "x2"),
                }
                for annotation in graph.get("annotations", []) or []:
                    if not isinstance(annotation, dict):
                        errors.append(f"{label}: each annotation must be an object.")
                        continue
                    annotation_type = str(annotation.get("type", "")).lower()
                    if annotation_type not in ANNOTATION_TYPES:
                        errors.append(f"{label}: unknown annotation type {annotation_type!r}.")
                    for field_name in required_annotation_fields.get(annotation_type, ()):
                        if field_name not in annotation or annotation.get(field_name) in (None, ""):
                            errors.append(
                                f"{label}: {annotation_type} annotation needs {field_name!r}."
                            )
                    if annotation.get("expr"):
                        expressions.append(str(annotation["expr"]))
                if expr_module is not None:
                    for expr in expressions:
                        try:
                            expr_module.compile_expr(expr)
                        except Exception as exc:
                            errors.append(f"{label}: bad expression {expr!r}: {exc}")
                animation = graph.get("animation")
                animation_type = animation if isinstance(animation, str) else (
                    animation.get("type") if isinstance(animation, dict) else "draw"
                )
                if animation_type not in {"draw", "sweep", "secant_to_tangent", "riemann", "area", "none"}:
                    errors.append(f"{label}: unknown graph animation {animation_type!r}.")
                if animation_type == "secant_to_tangent" and graph_type != "cartesian":
                    errors.append(f"{label}: secant_to_tangent needs a cartesian graph.")
        elif kind == "bullets":
            if not beat.get("heading") or not beat.get("items"):
                errors.append(f"{label}: bullets needs heading and items.")
            if len(beat.get("items", [])) > 6:
                warnings.append(f"{label}: more than 6 bullets; consider splitting the beat.")
        elif kind == "section":
            if not beat.get("heading"):
                errors.append(f"{label}: section needs heading.")
        elif kind == "compare":
            for side in ("left", "right"):
                if not isinstance(beat.get(side), dict) or not beat[side].get("items"):
                    errors.append(f"{label}: compare needs {side}.items.")
        elif kind == "recap":
            if not beat.get("heading") or not beat.get("items"):
                errors.append(f"{label}: recap needs heading and items.")
        elif kind == "image":
            if not beat.get("path"):
                errors.append(f"{label}: image needs path.")
            elif episode_dir is not None:
                image_path = Path(str(beat["path"]))
                if not image_path.is_absolute():
                    image_path = episode_dir / image_path
                if not image_path.exists():
                    warnings.append(f"{label}: image not found yet: {image_path}")
        elif kind == "custom":
            if not beat.get("notes"):
                warnings.append(f"{label}: custom beat has no notes for the override.")

    if has_equation and not latex_available():
        warnings.append(
            "Storyboard has equation beats but LaTeX is not on PATH; rendering will fail "
            "unless output.latex_fallback is true."
        )
    target = int(storyboard.get("target_duration_seconds") or (brief or {}).get("episode", {}).get("target_duration_seconds", 0) or 0)
    if target:
        estimate = estimate_duration(storyboard)
        drift = (estimate - target) / max(1, target)
        if abs(drift) > 0.25:
            warnings.append(
                f"Estimated duration {estimate:.0f}s is {drift:+.0%} versus target {target}s; "
                "cut or expand the script before recording."
            )
    if brief:
        expected_id = episode_id(brief.get("series", {}).get("season", 1), brief.get("series", {}).get("episode_number", 1))
        if storyboard.get("episode_id") != expected_id:
            errors.append(
                f"storyboard.episode_id is {storyboard.get('episode_id')!r}, expected {expected_id!r}."
            )
        if storyboard.get("language") and storyboard.get("language") != brief.get("output", {}).get("language"):
            warnings.append(
                f"Storyboard language {storyboard.get('language')!r} differs from brief output.language "
                f"{brief.get('output', {}).get('language')!r}."
            )
        if storyboard.get("template") and storyboard.get("template") != brief.get("series", {}).get("template"):
            errors.append("Storyboard template differs from the series template.")
    return errors, warnings


# --------------------------------------------------------------------------- tts manifest
def validate_manifest(manifest: dict[str, Any], storyboard: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    segments = manifest.get("segments")
    if not isinstance(segments, list) or not segments:
        errors.append("Voice manifest has no segments.")
        return errors, warnings
    by_id = {str(segment.get("id")): segment for segment in segments}
    for beat in storyboard.get("beats", []):
        beat_id = str(beat.get("id"))
        if beat_id not in by_id:
            errors.append(f"Voice manifest is missing narration for beat {beat_id!r}.")
            continue
        duration = float(by_id[beat_id].get("duration", 0.0))
        if duration <= 0:
            errors.append(f"Voice manifest duration is zero for beat {beat_id!r}.")
        audio = by_id[beat_id].get("audio")
        if audio and not (Path(audio).is_absolute()):
            # Relative to the episode directory, but we do not know it here.
            pass
    total = float(manifest.get("total_duration", 0.0))
    if total <= 0:
        errors.append("Voice manifest total_duration must be positive.")
    return errors, warnings

# Switch to the shared environment prepared by install.py when this interpreter
# lacks the runtime dependencies, so `python scripts/render.py` just works.
ensure_runtime()
