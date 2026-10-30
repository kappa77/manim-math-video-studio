#!/usr/bin/env python3
"""Create the project virtual environment and install the skill dependencies."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS = ROOT / "requirements.txt"
CHECK = ROOT / "manim-math-video" / "scripts" / "check_env.py"


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def run(command: list[str]) -> int:
    print(f"\n$ {' '.join(command)}", flush=True)
    return subprocess.run(command, check=False).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        default=str(ROOT / ".venv"),
        help="Virtual environment directory (default: <repo>/.venv)",
    )
    parser.add_argument("--no-check", action="store_true", help="Skip check_env.py")
    args = parser.parse_args(argv)

    venv = Path(args.venv).expanduser().resolve()
    python = venv_python(venv)
    if not REQUIREMENTS.exists():
        print(f"Missing requirements file: {REQUIREMENTS}", file=sys.stderr)
        return 2

    if not python.exists():
        print(f"Creating virtual environment: {venv}")
        code = run([sys.executable, "-m", "venv", str(venv)])
        if code != 0:
            return code
    else:
        print(f"Using existing virtual environment: {venv}")

    if not python.exists():
        print(f"Virtual environment Python not found: {python}", file=sys.stderr)
        return 2

    code = run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
    if code != 0:
        return code
    code = run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)])
    if code != 0:
        return code

    print("\nVirtual environment ready.")
    print(f"  {venv}")
    if os.name == "nt":
        print("\nActivate it in a new terminal:")
        print(f"  PowerShell: {venv}\\Scripts\\Activate.ps1")
        print(f"  cmd:        {venv}\\Scripts\\activate.bat")
        print(f"  bash:       source {venv.as_posix()}/Scripts/activate")
        print("\nOr call the venv Python directly:")
        print(f"  {python} {CHECK}")
    else:
        print("\nActivate it in a new terminal:")
        print(f"  source {venv}/bin/activate")
        print("\nOr call the venv Python directly:")
        print(f"  {python} {CHECK}")

    if args.no_check:
        return 0
    if not CHECK.exists():
        print(f"Missing check script: {CHECK}", file=sys.stderr)
        return 2
    return run([str(python), str(CHECK)])


if __name__ == "__main__":
    sys.exit(main())
