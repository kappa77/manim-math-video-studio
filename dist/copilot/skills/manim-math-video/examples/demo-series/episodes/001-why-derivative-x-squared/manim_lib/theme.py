"""Theme loading and font/color resolution for a generated episode."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import manimpango

    _AVAILABLE_FONTS = {name.casefold(): name for name in manimpango.list_fonts()}
except Exception:  # pragma: no cover - Manim always ships manimpango
    _AVAILABLE_FONTS = {}


def _resolve_font(candidates: list[str], fallback: str) -> str:
    for candidate in candidates:
        if not candidate:
            continue
        exact = _AVAILABLE_FONTS.get(candidate.casefold())
        if exact:
            return exact
        needle = candidate.casefold()
        for key, original in _AVAILABLE_FONTS.items():
            if needle in key:
                return original
    for generic in (fallback, "DejaVu Sans", "Segoe UI", "Arial", "sans-serif"):
        exact = _AVAILABLE_FONTS.get(generic.casefold())
        if exact:
            return exact
    return fallback


@dataclass(frozen=True)
class Theme:
    data: dict[str, Any]
    path: Path

    @classmethod
    def load(cls, path: str | Path) -> "Theme":
        path = Path(path)
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if "id" not in data:
            raise ValueError(f"Theme {path} has no id.")
        return cls(data=data, path=path)

    @property
    def id(self) -> str:
        return str(self.data["id"])

    @property
    def name(self) -> str:
        return str(self.data.get("name", self.id))

    @property
    def aspect_ratio(self) -> str:
        return str(self.data.get("aspect_ratio", "16:9"))

    def color(self, role: str, default: str | None = None) -> str:
        if role.startswith("#"):
            return role
        if role in self.data.get("roles", {}):
            return str(self.data["roles"][role])
        if role in self.data:
            return str(self.data[role])
        if default is not None:
            return default
        raise KeyError(f"Unknown color role {role!r} in theme {self.id}.")

    def font(self, kind: str = "body") -> str:
        fonts = self.data.get("fonts", {})
        candidates = fonts.get(kind) or fonts.get("body") or []
        fallback = {
            "heading": "DejaVu Sans",
            "body": "DejaVu Sans",
            "mono": "DejaVu Sans Mono",
        }.get(kind, "DejaVu Sans")
        return _resolve_font(list(candidates), fallback)

    def size(self, kind: str, default: float) -> float:
        return float(self.data.get("sizes", {}).get(kind, default))

    def layout(self, key: str, default: Any = None) -> Any:
        return self.data.get("layout", {}).get(key, default)

    def graph_style(self, key: str, default: Any = None) -> Any:
        return self.data.get("graph", {}).get(key, default)

    def motion(self, key: str, default: Any = None) -> Any:
        return self.data.get("motion", {}).get(key, default)

    def captions(self, key: str, default: Any = None) -> Any:
        return self.data.get("captions", {}).get(key, default)

    def story(self, key: str, default: Any = None) -> Any:
        return self.data.get("story", {}).get(key, default)

    def role(self, name: str | None, default: str = "primary") -> str:
        if not name:
            return self.color(default)
        try:
            return self.color(name)
        except KeyError:
            return self.color(default)
