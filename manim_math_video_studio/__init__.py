"""Installer entry point for the manim-math-video Agent Skill."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from install import main

try:
    __version__ = version("manim-math-video-studio")
except PackageNotFoundError:  # running from a checkout
    __version__ = "development"

__all__ = ["main", "__version__"]
