#!/usr/bin/env python3
"""Check the Python, Manim, LaTeX, TTS, and media dependencies."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from _common import SKILL_ROOT, find_manim_executable

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_DIM = "\033[2m"
STATUS_COLORS = {
    "ok": "\033[32m",
    "warn": "\033[33m",
    "optional": "\033[36m",
    "fail": "\033[31m",
}


def _enable_windows_ansi() -> None:
    """Enable virtual-terminal sequences on Windows consoles."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


def _color_enabled(stream, mode: str) -> bool:
    if mode == "never":
        return False
    if mode == "always":
        return True
    if os.environ.get("NO_COLOR") is not None:
        return False
    return bool(getattr(stream, "isatty", lambda: False)())


def _paint(text: str, code: str, enabled: bool) -> str:
    return f"{code}{text}{ANSI_RESET}" if enabled and code else text


def _version_of(module_name: str) -> str | None:
    try:
        module = importlib.import_module(module_name)
        return getattr(module, "__version__", None) or "installed"
    except Exception:
        return None


def _tool_version(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        return ((completed.stdout or "") + (completed.stderr or "")).strip().splitlines()[0]
    except Exception:
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON")
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Color the table (default: auto; respects NO_COLOR)",
    )
    parser.add_argument("--no-color", action="store_true", help="Same as --color never")
    args = parser.parse_args(argv)
    if args.no_color:
        args.color = "never"
    if args.color != "never":
        _enable_windows_ansi()
    color = _color_enabled(sys.stdout, args.color)

    checks: list[dict[str, str]] = []

    def add(name: str, status: str, detail: str, recommendation: str = "") -> None:
        checks.append(
            {
                "component": name,
                "status": status,
                "detail": detail,
                "recommendation": recommendation,
            }
        )

    python_ok = sys.version_info >= (3, 10)
    python_detail = f"{platform.python_version()} ({sys.executable})"
    if sys.prefix != sys.base_prefix:
        python_detail += " [venv]"
    add(
        "Python",
        "ok" if python_ok else "fail",
        python_detail,
        "Install Python 3.10 or newer." if not python_ok else "",
    )

    manim_version = _version_of("manim")
    add(
        "Manim",
        "ok" if manim_version else "fail",
        manim_version or "not importable",
        "Install Manim Community: python -m pip install manim" if not manim_version else "",
    )
    manim_exe = find_manim_executable()
    add(
        "manim executable",
        "ok" if manim_exe else "fail",
        manim_exe or "not found in PATH, the active venv, a local .venv, or MANIM_BIN",
        "Activate the project venv (or add its Scripts directory to PATH). "
        "You can also set MANIM_BIN to the full manim executable path."
        if not manim_exe
        else "",
    )

    latex = shutil.which("latex")
    dvisvgm = shutil.which("dvisvgm")
    add(
        "LaTeX",
        "ok" if latex else "warn",
        latex or "not on PATH",
        "Required for equation beats. Install TeX Live/MiKTeX/TinyTeX." if not latex else "",
    )
    add(
        "dvisvgm",
        "ok" if dvisvgm else "warn",
        dvisvgm or "not on PATH",
        "Usually installed with TeX; Manim needs it for MathTex." if not dvisvgm else "",
    )

    edge_tts = _version_of("edge_tts")
    add(
        "edge-tts",
        "ok" if edge_tts else "warn",
        edge_tts or "not installed",
        "Default TTS provider. Install: python -m pip install edge-tts" if not edge_tts else "",
    )
    piper = shutil.which("piper")
    add(
        "Piper",
        "ok" if piper else "optional",
        piper or "not installed (optional offline TTS)",
        "Install Piper and a voice model for offline narration." if not piper else "",
    )

    av_version = _version_of("av")
    add(
        "PyAV",
        "ok" if av_version else "warn",
        av_version or "not installed",
        "Needed for MP3 -> WAV conversion and QA. Install: python -m pip install av" if not av_version else "",
    )
    ffmpeg = shutil.which("ffmpeg")
    add(
        "ffmpeg",
        "ok" if ffmpeg else "optional",
        ffmpeg or "not on PATH (PyAV can cover most operations)",
        "Optional. Install ffmpeg for post-production, subtitle burn-in, and audio normalization." if not ffmpeg else "",
    )

    numpy_version = _version_of("numpy")
    add(
        "NumPy",
        "ok" if numpy_version else "fail",
        numpy_version or "not installed",
        "Install: python -m pip install numpy" if not numpy_version else "",
    )
    pil_version = _version_of("PIL")
    add(
        "Pillow",
        "ok" if pil_version else "warn",
        pil_version or "not installed",
        "Needed for QA contact sheets. Install: python -m pip install pillow" if not pil_version else "",
    )

    try:
        import manimpango

        fonts = manimpango.list_fonts()
        lowered = {font.casefold() for font in fonts}
        preferred = ["Inter", "Segoe UI", "DejaVu Sans", "Georgia", "Consolas"]
        found = [font for font in preferred if font.casefold() in lowered]
        add(
            "Fonts",
            "ok" if found else "warn",
            f"{len(fonts)} fonts; preferred found: {', '.join(found) if found else 'none'}",
            "Install Inter or use the template fallbacks (Segoe UI / DejaVu Sans)."
            if not found
            else "",
        )
    except Exception as exc:
        add("Fonts", "warn", f"Could not list fonts: {exc}", "Check ManimPango installation.")

    assets = [
        SKILL_ROOT / "assets" / "templates" / "clean-light.json",
        SKILL_ROOT / "assets" / "templates" / "dark-board.json",
        SKILL_ROOT / "assets" / "templates" / "paper-editorial.json",
        SKILL_ROOT / "assets" / "voices.json",
        SKILL_ROOT / "assets" / "project" / "manim_lib" / "runtime.py",
    ]
    missing = [str(path.relative_to(SKILL_ROOT)) for path in assets if not path.exists()]
    add(
        "Skill assets",
        "ok" if not missing else "fail",
        "complete" if not missing else f"missing: {', '.join(missing)}",
        "Reinstall/copy the complete skill directory." if missing else "",
    )

    if args.json:
        print(json.dumps({"ok": not any(item["status"] == "fail" for item in checks), "checks": checks}, indent=2))
    else:
        title = f"manim-math-video environment — {platform.system()} {platform.release()}"
        print(_paint(title, ANSI_BOLD, color))
        print(f"Skill root: {_paint(str(SKILL_ROOT), ANSI_DIM, color)}\n")
        header = f"{'Component':22} {'Status':9} Detail"
        print(_paint(header, ANSI_BOLD, color))
        print(_paint("-" * 100, ANSI_DIM, color))
        for item in checks:
            status_color = STATUS_COLORS.get(item["status"], "")
            status = _paint(f"{item['status']:9}", status_color, color)
            print(f"{item['component']:22} {status} {item['detail']}")
            if item["recommendation"]:
                arrow = _paint("->", ANSI_DIM, color)
                print(f"{'':32} {arrow} {item['recommendation']}")

        legend = ", ".join(
            f"{_paint(label, STATUS_COLORS[label], color)} = {description}"
            for label, description in (
                ("ok", "ready"),
                ("warn", "needed for some workflows"),
                ("optional", "nice to have"),
                ("fail", "blocking"),
            )
        )
        print(f"\nLegend: {legend}")

        failures = [item for item in checks if item["status"] == "fail"]
        warnings = [item for item in checks if item["status"] == "warn"]
        if failures:
            names = ", ".join(item["component"] for item in failures)
            print(
                f"\n{_paint('Blocking issues:', STATUS_COLORS['fail'], color)}"
                f" {len(failures)} ({names})"
            )
        else:
            print(f"\n{_paint('Environment ready.', STATUS_COLORS['ok'], color)}")
        if warnings:
            print(
                f"{_paint('Warnings:', STATUS_COLORS['warn'], color)}"
                f" {len(warnings)} (review the rows above)"
            )

    return 1 if any(item["status"] == "fail" for item in checks) else 0


if __name__ == "__main__":
    sys.exit(main())
