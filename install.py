#!/usr/bin/env python3
"""One-command installer for the manim-math-video agent skill.

Installs the skill tree for the agents found on this machine and prepares one
shared Python environment at ~/.manim-math-video/venv. Standard library only:
this file must run before any dependency exists.

Typical use (see install.sh / install.ps1 for the piped one-liners):

    python install.py                      # auto-detect agents, install deps
    python install.py --platform claude    # one agent only
    python install.py --with-latex         # also install a LaTeX engine
    python install.py --uninstall          # remove skill trees and the venv
"""

from __future__ import annotations

import argparse
import json
import os
import platform as platform_module
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ARCHIVE_URL = os.environ.get("MMS_ARCHIVE_URL", "").strip()  # optional mirror or file:// URL
REPO = os.environ.get("MMS_REPO", "kappa77/manim-math-video-studio")
DEFAULT_REF = os.environ.get("MMS_REF", "main")
SKILL_NAME = "manim-math-video"
PLATFORMS = ("claude", "codex", "copilot", "pi")
MIN_PYTHON = (3, 10)
STATE_DIR = Path.home() / ".manim-math-video"
DEFAULT_VENV = STATE_DIR / "venv"
STATE_FILE = STATE_DIR / "install.json"

INVOKE = {
    "claude": "/manim-math-video",
    "codex": "$manim-math-video",
    "copilot": "/manim-math-video",
    "pi": "/skill:manim-math-video",
}
CLI = {"claude": "claude", "codex": "codex", "copilot": "copilot", "pi": "pi"}

IS_WINDOWS = os.name == "nt"
ECHO = True  # set by --quiet, controls command echoing
VERBOSE = False  # set by --verbose, controls pip output


# --------------------------------------------------------------------------- #
# output helpers
# --------------------------------------------------------------------------- #


def say(message: str = "") -> None:
    print(message, flush=True)


def step(message: str) -> None:
    say(f"\n==> {message}")


def note(message: str) -> None:
    say(f"    {message}")


def warn(message: str) -> None:
    say(f"    ! {message}")


def die(message: str, code: int = 1):
    print(f"\nERROR: {message}", file=sys.stderr, flush=True)
    raise SystemExit(code)


# --------------------------------------------------------------------------- #
# source tree: local checkout or download
# --------------------------------------------------------------------------- #


def looks_like_source(root: Path) -> bool:
    return (root / "platforms" / "manifest.json").is_file() and (root / "dist").is_dir()


def download_source(ref: str, destination: Path) -> Path:
    """Download the repository archive for `ref` and return the extracted root."""
    if ARCHIVE_URL:
        url = ARCHIVE_URL
        say(f"    fetching {url}")
    else:
        kind = "tags" if ref.startswith("v") else "heads"
        url = f"https://codeload.github.com/{REPO}/tar.gz/refs/{kind}/{ref}"
        say(f"    fetching {REPO}@{ref}")
    archive = destination / "repo.archive"
    try:
        with urllib.request.urlopen(url, timeout=120) as response, archive.open("wb") as handle:
            shutil.copyfileobj(response, handle)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user as a hint
        die(
            f"could not download {url}: {exc}\n"
            "       Check your network, or clone the repository and run install.py from it."
        )

    extract = destination / "src"
    extract.mkdir()
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(extract)
        else:
            with tarfile.open(archive) as bundle:
                try:
                    bundle.extractall(extract, filter="data")
                except TypeError:  # Python < 3.12 has no filter argument
                    bundle.extractall(extract)
    except Exception as exc:  # noqa: BLE001
        die(f"could not unpack the archive: {exc}")

    entries = [path for path in extract.iterdir() if path.is_dir()]
    if len(entries) != 1:
        die("unexpected archive layout; please report this issue")
    return entries[0]


def resolve_source(explicit: str | None, ref: str = DEFAULT_REF) -> tuple[Path, "tempfile.TemporaryDirectory | None"]:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if not looks_like_source(root):
            die(f"--source {root} is not a checkout of this repository")
        return root, None

    # When exec'd from a URL (`python -c "...exec(urlopen(...))"`) there is no
    # __file__, so fall through to the download path.
    here = Path(globals()["__file__"]).resolve().parent if "__file__" in globals() else None
    if here is not None and looks_like_source(here):
        return here, None

    holder = tempfile.TemporaryDirectory(prefix="mms-install-")
    return download_source(ref, Path(holder.name)), holder


# --------------------------------------------------------------------------- #
# platform detection
# --------------------------------------------------------------------------- #


def load_manifest(root: Path) -> dict:
    try:
        return json.loads((root / "platforms" / "manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        die(f"could not read platforms/manifest.json: {exc}")


def signals_for(platform: str) -> list[Path | None]:
    home = Path.home()
    found: list[Path | None] = [Path(p) if (p := shutil.which(CLI[platform])) else None]
    if platform == "claude":
        found.append(home / ".claude")
    elif platform == "codex":
        found.extend((home / ".codex", home / ".agents"))
    elif platform == "copilot":
        found.append(home / ".copilot")
    elif platform == "pi":
        found.append(home / ".pi")
    return [item for item in found if item is not None]


def detect_platforms() -> list[str]:
    detected = [name for name in PLATFORMS if any(item.exists() for item in signals_for(name))]
    return detected


def resolve_platforms(spec: str | None) -> list[str]:
    if not spec or spec == "auto":
        detected = detect_platforms()
        if detected:
            return detected
        warn("no agent installation detected; defaulting to Claude Code")
        note("use --platform codex,copilot,pi or --platform all to choose")
        return ["claude"]
    if spec == "all":
        return list(PLATFORMS)
    requested = [item.strip().lower() for item in spec.split(",") if item.strip()]
    unknown = [item for item in requested if item not in PLATFORMS]
    if unknown:
        die(f"unknown platform(s): {', '.join(unknown)}; choose from {', '.join(PLATFORMS)}")
    return requested


def target_dir(platform: str, manifest: dict, root_override: str | None) -> Path:
    config = manifest["platforms"][platform]
    if root_override:
        return Path(root_override).expanduser().resolve() / SKILL_NAME
    if platform == "codex" and not (Path.home() / ".codex").exists() and (Path.home() / ".agents").exists():
        return (Path.home() / ".agents" / "skills" / SKILL_NAME).resolve()
    return Path(config["install_root"]).expanduser().resolve() / SKILL_NAME


# --------------------------------------------------------------------------- #
# python / environment
# --------------------------------------------------------------------------- #


def version_of(command: list[str]) -> tuple[int, int] | None:
    try:
        result = subprocess.run(
            [*command, "-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return None
    text = (result.stdout or "").strip()
    if result.returncode != 0 or "." not in text:
        return None
    major, _, minor = text.partition(".")
    return int(major), int(minor)


def find_interpreter() -> list[str]:
    if tuple(sys.version_info[:2]) >= MIN_PYTHON:
        return [sys.executable]
    candidates: list[list[str]] = []
    if IS_WINDOWS:
        candidates.extend([["py", f"-{major}.{minor}"] for major in (3,) for minor in (13, 12, 11, 10)])
    candidates.extend([[f"python3.{minor}"] for minor in (13, 12, 11, 10)] + [["python3"], ["python"]])
    for candidate in candidates:
        if not shutil.which(candidate[0]):
            continue
        found = version_of(candidate)
        if found and found >= MIN_PYTHON:
            return candidate
    available = "%d.%d" % sys.version_info[:2]
    die(
        f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required, found {available}.\n"
        "       Install a newer Python (https://www.python.org/downloads/) and rerun."
    )


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def run(command: list[str], *, echo: bool | None = None, capture: bool = False) -> int:
    """Run a command; `capture` hides its output unless it fails."""
    if (ECHO if echo is None else echo) and not (ECHO and not VERBOSE and capture):
        note("$ " + " ".join(str(part) for part in command))
    if capture and not VERBOSE:
        result = subprocess.run(
            command, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        if result.returncode != 0 and result.stdout:
            tail = result.stdout.strip().splitlines()[-25:]
            for line in tail:
                say(f"    | {line}")
        return result.returncode
    return subprocess.run(command, check=False).returncode


def create_venv(venv: Path, use_uv: bool) -> None:
    if venv_python(venv).is_file():
        note(f"reusing environment: {venv}")
        return
    venv.parent.mkdir(parents=True, exist_ok=True)
    interpreter = find_interpreter()
    if use_uv and shutil.which("uv"):
        note("using uv for a faster install")
        uv_python = " ".join(interpreter) if len(interpreter) == 1 else None
        if uv_python:
            code = run(["uv", "venv", "--python", uv_python, str(venv)])
            if code == 0 and venv_python(venv).is_file():
                return
        warn("uv could not create the environment; falling back to venv")
        shutil.rmtree(venv, ignore_errors=True)
    code = run([*interpreter, "-m", "venv", str(venv)])
    if code != 0 or not venv_python(venv).is_file():
        die("could not create the Python environment")


def install_dependencies(venv: Path, requirements: Path, use_uv: bool) -> None:
    python = str(venv_python(venv))
    flags = ["-q"] if not VERBOSE else []
    if use_uv and shutil.which("uv"):
        code = run(["uv", "pip", "install", *flags, "--python", python, "-r", str(requirements)], capture=True)
        if code == 0:
            return
        warn("uv install failed; falling back to pip")
    run([python, "-m", "pip", "install", "-q", "--upgrade", "--disable-pip-version-check", "--no-input", "pip"], capture=True)
    code = run(
        [
            python,
            "-m",
            "pip",
            "install",
            *flags,
            "--disable-pip-version-check",
            "--no-input",
            "-r",
            str(requirements),
        ],
        capture=True,
    )
    if code != 0:
        die("dependency installation failed; rerun with --verbose to see the full output")


# --------------------------------------------------------------------------- #
# latex (optional)
# --------------------------------------------------------------------------- #


def latex_ready() -> bool:
    return bool(shutil.which("latex")) and bool(shutil.which("dvisvgm"))


LATEX_HINTS = {
    "nt": [
        "winget install --id MiKTeX.MiKTeX -e --accept-package-agreements --accept-source-agreements",
    ],
    "darwin": [
        "brew install --cask basictex",
        "sudo tlmgr install dvisvgm standalone amsmath amsfonts",
    ],
    "linux": [
        "sudo apt install texlive texlive-latex-extra dvisvgm   # Debian / Ubuntu",
        "sudo dnf install texlive-scheme-medium dvisvgm         # Fedora",
    ],
}


def install_latex(enable: bool, dry_run: bool) -> None:
    if latex_ready():
        note("LaTeX + dvisvgm already available (equation beats enabled)")
        return
    key = "nt" if IS_WINDOWS else platform_module.system().lower()
    hints = LATEX_HINTS.get(key, LATEX_HINTS["linux"])
    if not enable:
        note("LaTeX not installed: equation beats are unavailable, everything else works")
        note("enable later with: python install.py --with-latex")
        return
    step("Installing LaTeX (dvisvgm + basic packages)")
    if dry_run:
        note("would run: " + "; ".join(hints))
        return
    if IS_WINDOWS and shutil.which("winget"):
        code = run(hints[0].split())
        if code != 0:
            warn("winget could not install MiKTeX; install it manually:")
            for hint in hints:
                note(hint)
        else:
            note("MiKTeX installed; set 'Always install missing packages on the fly' in MiKTeX Console")
        return
    if platform_module.system().lower() == "darwin" and shutil.which("brew"):
        run(hints[0].split())
        run(hints[1].split())
        return
    warn("automatic LaTeX install is not supported here; run:")
    for hint in hints:
        note(hint)


# --------------------------------------------------------------------------- #
# install / uninstall
# --------------------------------------------------------------------------- #


def copy_skill(source: Path, target: Path) -> None:
    preserve = target / ".venv"
    if target.exists():
        if preserve.exists():
            stash = target.parent / f".{SKILL_NAME}-venv-stash"
            shutil.rmtree(stash, ignore_errors=True)
            preserve.rename(stash)
        else:
            stash = None
        shutil.rmtree(target, ignore_errors=True)
        if stash is not None:
            shutil.copytree(source, target)
            stash.rename(target / ".venv")
        else:
            shutil.copytree(source, target)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)


def read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def write_state(platforms: dict[str, str], venv: Path, version: str) -> None:
    previous = read_state()
    merged = dict(previous.get("platforms", {}))
    merged.update(platforms)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": version,
        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "venv": str(venv),
        "platforms": merged,
    }
    STATE_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_version(root: Path) -> str:
    try:
        return (root / "VERSION").read_text(encoding="utf-8").strip() or "0.0.0"
    except Exception:  # noqa: BLE001
        return "0.0.0"


def verify(skill_dir: Path, venv: Path) -> int:
    python = venv_python(venv)
    check = skill_dir / "scripts" / "check_env.py"
    if not python.is_file() or not check.is_file():
        return 0
    step("Verifying the environment")
    environment = dict(os.environ, PYTHONWARNINGS="ignore::SyntaxWarning")
    result = subprocess.run([str(python), str(check)], check=False, env=environment)
    return result.returncode


def uninstall(dry_run: bool) -> int:
    state = read_state()
    targets = dict(state.get("platforms", {}))
    if not targets:
        manifest = load_manifest(resolve_source(None)[0])
        for name in PLATFORMS:
            targets[name] = str(target_dir(name, manifest, None))
    venv = Path(state.get("venv", DEFAULT_VENV)).expanduser()
    step("Removing installed skills" + (" (dry run)" if dry_run else ""))
    for name, path in targets.items():
        directory = Path(path)
        if not directory.exists():
            continue
        if directory.name != SKILL_NAME:
            warn(f"skipping {directory} (unexpected name; remove it manually)")
            continue
        note(f"{name}: {directory}")
        if not dry_run:
            shutil.rmtree(directory, ignore_errors=True)
    if venv.exists():
        # Normalize symlinked HOME paths (macOS /var -> /private/var, Windows
        # short paths) before deciding whether this installer owns the venv.
        try:
            managed_venv = venv.resolve()
            default_venv = DEFAULT_VENV.expanduser().resolve()
            state_root = STATE_DIR.expanduser().resolve()
        except OSError:
            managed_venv, default_venv, state_root = venv, DEFAULT_VENV.expanduser(), STATE_DIR.expanduser()
        managed = managed_venv == default_venv or state_root in managed_venv.parents
        if not managed:
            warn(f"leaving {venv} in place (not created by this installer)")
        else:
            note(f"environment: {venv}")
            if not dry_run:
                shutil.rmtree(managed_venv, ignore_errors=True)
    if not dry_run:
        STATE_FILE.unlink(missing_ok=True)
    say("\nDone." if not dry_run else "\nDry run: nothing was removed.")
    return 0


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #


def build_plan(root: Path, manifest: dict, platforms: list[str], root_override: str | None) -> dict[str, Path]:
    plan: dict[str, Path] = {}
    for name in platforms:
        plan[name] = target_dir(name, manifest, root_override)
    return plan


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    # Flags are awkward to append to the universal `python -c` one-liner, so
    # accept them from the environment too.
    extra = os.environ.get("MMS_ARGS", "").strip()
    if extra:
        arguments = [*shlex.split(extra), *arguments]

    parser = argparse.ArgumentParser(
        prog="install.py",
        description="Install the manim-math-video skill for your agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python install.py                      auto-detect agents, install everything\n"
            "  python install.py --platform codex     one agent only\n"
            "  python install.py --with-latex         also install a LaTeX engine\n"
            "  python install.py --uninstall          remove skills and environment\n"
        ),
    )
    parser.add_argument("--platform", "--platforms", dest="platform", default="auto",
                        help=f"auto (default), all, or a comma list of {', '.join(PLATFORMS)}")
    parser.add_argument("--root", help="install into this directory instead of the personal root")
    parser.add_argument("--venv", default=str(DEFAULT_VENV), help=f"environment directory (default: {DEFAULT_VENV})")
    parser.add_argument("--source", help="path to this repository (default: auto-detect or download)")
    parser.add_argument(
        "--ref",
        default=DEFAULT_REF,
        help=f"git ref to download when not installed from a checkout (default: {DEFAULT_REF})",
    )
    parser.add_argument("--with-latex", action="store_true", help="install a LaTeX engine for equation beats")
    parser.add_argument("--no-deps", action="store_true", help="skip Python dependencies")
    parser.add_argument("--no-uv", action="store_true", help="do not use uv even when it is installed")
    parser.add_argument("--dry-run", action="store_true", help="show the plan without changing anything")
    parser.add_argument("--uninstall", action="store_true", help="remove the installed skills and environment")
    parser.add_argument("--quiet", action="store_true", help="hide subprocess commands")
    parser.add_argument("--verbose", action="store_true", help="show full pip output")
    args = parser.parse_args(arguments)

    global ECHO, VERBOSE
    ECHO = not args.quiet
    VERBOSE = args.verbose


    if args.uninstall:
        return uninstall(args.dry_run)

    root, holder = resolve_source(args.source, args.ref or DEFAULT_REF)
    try:
        manifest = load_manifest(root)
        platforms = resolve_platforms(args.platform)
        if args.root and len(platforms) != 1:
            die("--root installs a single platform; combine it with --platform")
        plan = build_plan(root, manifest, platforms, args.root)
        venv = Path(args.venv).expanduser().resolve()
        version = read_version(root)

        say("manim-math-video installer")
        say(f"  version   {version}")
        say(f"  python    {sys.version.split()[0]} ({sys.executable})")
        say(f"  env       {venv}")
        for name, path in plan.items():
            say(f"  {name:<9} {path}")

        missing = [name for name in plan if not (root / "dist" / name / "skills" / SKILL_NAME).is_dir()]
        if missing:
            die(f"missing prebuilt trees for: {', '.join(missing)}; run: python platforms/build.py")

        if args.dry_run:
            say("\nDry run: nothing was changed.")
            return 0

        step("Installing the skill")
        for name, path in plan.items():
            copy_skill(root / "dist" / name / "skills" / SKILL_NAME, path)
            note(f"{name} -> {path}")

        if args.no_deps:
            warn("skipped Python dependencies (--no-deps)")
        else:
            step("Preparing the Python environment (2-4 min on first run)")
            create_venv(venv, use_uv=not args.no_uv)
            install_dependencies(venv, root / "requirements.txt", use_uv=not args.no_uv)
            for path in plan.values():
                (path / ".venv-path").write_text(str(venv) + "\n", encoding="utf-8", newline="\n")

        install_latex(args.with_latex, dry_run=False)
        write_state({name: str(path) for name, path in plan.items()}, venv, version)

        code = verify(next(iter(plan.values())), venv)

        step("Ready")
        for name in plan:
            say(f"    {manifest['platforms'][name]['label']:<16} {INVOKE[name]}")
        say("\n    Restart your agent, then ask for a video, for example:")
        say('      "Make a 90 second video on why the derivative of x squared is 2x"')
        if code != 0:
            warn("the environment check reported blocking issues; see the table above")
        return code
    finally:
        if holder is not None:
            holder.cleanup()


if __name__ == "__main__":
    sys.exit(main())
