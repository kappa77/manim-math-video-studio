#!/usr/bin/env python3
"""Run the skill environment check from the repository root."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "manim-math-video" / "scripts" / "check_env.py"


def main() -> int:
    if not TARGET.exists():
        print(f"Skill script not found: {TARGET}", file=sys.stderr)
        return 2
    return subprocess.call([sys.executable, str(TARGET), *sys.argv[1:]])


if __name__ == "__main__":
    sys.exit(main())
