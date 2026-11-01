#!/usr/bin/env python3
"""End-to-end tests for the installer, against simulated agent harnesses.

The fast scope needs only the standard library: it plants the configuration
directories and CLI names each agent uses, runs ``install.py`` in a throwaway
HOME, and checks the installed tree, frontmatter, state file, update path, and
uninstall path. The runtime scope additionally creates the shared virtual
environment, installs ``requirements.txt``, and runs the skill's own checks
against every installed harness.

Run it locally:

    python tests/install_matrix.py --scope fast
    python tests/install_matrix.py --scope runtime --render

or in a clean Linux container:

    tests/docker/run.sh
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

SKILL = "manim-math-video"

#: The harness contract this repository promises. Keep this in sync with
#: platforms/manifest.json and the per-platform INSTALL.md files; the manifest
#: test fails when they drift.
EXPECTED = {
    "claude": {
        "label": "Claude Code",
        "install_root": "~/.claude/skills",
        "project_root": ".claude/skills",
        "invoke": "/manim-math-video",
        "usage_heading": "## Using this skill in Claude Code",
        "frontmatter_add": ['argument-hint: "[topic, brief.json, or episode directory]"'],
        "frontmatter_drop": [],
        "include_agents": False,
    },
    "codex": {
        "label": "Codex",
        "install_root": "~/.codex/skills",
        "project_root": ".agents/skills",
        "invoke": "$manim-math-video",
        "usage_heading": "## Using this skill in Codex",
        "frontmatter_add": [],
        "frontmatter_drop": [],
        "include_agents": True,
    },
    "copilot": {
        "label": "GitHub Copilot",
        "install_root": "~/.copilot/skills",
        "project_root": ".github/skills",
        "invoke": "/manim-math-video",
        "usage_heading": "## Using this skill in GitHub Copilot",
        "frontmatter_add": ['argument-hint: "[topic, brief.json, or episode directory]"'],
        "frontmatter_drop": ["license", "metadata"],
        "include_agents": False,
    },
    "pi": {
        "label": "Pi",
        "install_root": "~/.pi/agent/skills",
        "project_root": ".pi/skills",
        "invoke": "/skill:manim-math-video",
        "usage_heading": "## Using this skill in Pi",
        "frontmatter_add": [],
        "frontmatter_drop": [],
        "include_agents": False,
    },
}

SIGNAL_DIRS = {
    "claude": ".claude",
    "codex": ".codex",
    "copilot": ".copilot",
    "pi": ".pi",
}


# --------------------------------------------------------------------------- #
# tiny test framework
# --------------------------------------------------------------------------- #


class Failure(AssertionError):
    """A test assertion failed."""


class SkipTest(Exception):
    """A test does not apply on this platform."""


@dataclass
class Test:
    name: str
    scope: str
    function: Callable[["Context"], None]


@dataclass
class Outcome:
    name: str
    status: str
    seconds: float
    message: str = ""


@dataclass
class Context:
    repo: Path
    python: str
    work: Path
    verbose: bool
    render: bool
    runtime: dict[str, object] = field(default_factory=dict)


TESTS: list[Test] = []


def test(scope: str = "fast"):
    def register(function: Callable[[Context], None]) -> Callable[[Context], None]:
        TESTS.append(Test(function.__name__, scope, function))
        return function

    return register


def require(condition: object, message: str) -> None:
    if not condition:
        raise Failure(message)


def tail(text: str | None, limit: int = 5000) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return "...\n" + value[-limit:]


def describe(result: subprocess.CompletedProcess) -> str:
    return (
        f"exit code {result.returncode}\n"
        f"--- stdout ---\n{tail(result.stdout)}\n"
        f"--- stderr ---\n{tail(result.stderr)}"
    )


def expect_success(result: subprocess.CompletedProcess, note: str) -> None:
    if result.returncode != 0:
        raise Failure(f"{note}\n{describe(result)}")


def run_command(
    ctx: Context,
    command: list[str],
    *,
    env: dict[str, str],
    cwd: Path | None = None,
    timeout: float = 600,
) -> subprocess.CompletedProcess:
    if ctx.verbose:
        print(f"      $ {shlex.join(command)}", flush=True)
    started = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise Failure(f"timed out after {timeout:.0f}s: {shlex.join(command)}") from exc
    except OSError as exc:
        raise Failure(f"could not run {command[0]}: {exc}") from exc
    if ctx.verbose:
        print(f"        exit {result.returncode} in {time.time() - started:.1f}s", flush=True)
        for stream, value in (("out", result.stdout), ("err", result.stderr)):
            for line in (value or "").splitlines()[-15:]:
                print(f"        {stream} | {line}", flush=True)
    return result


# --------------------------------------------------------------------------- #
# paths, environments, fake harnesses
# --------------------------------------------------------------------------- #


def clean_env(home: Path, *, path: str | None = None) -> dict[str, str]:
    """An isolated environment rooted at a throwaway HOME.

    Agent detection reads both PATH and the user's configuration directories,
    so tests always pin both. STATE_DIR is computed from HOME at import time in
    install.py, which is why HOME/USERPROFILE are set on the subprocess.
    """
    env = dict(os.environ)
    for key in list(env):
        if key.startswith("MMS_") or key in {
            "MANIM_STUDIO_VENV",
            "MANIM_STUDIO_NO_REEXEC",
            "MANIM_STUDIO_REEXEC",
            "MANIM_BIN",
            "VIRTUAL_ENV",
            "CONDA_PREFIX",
            "PYTHONHOME",
            "PYTHONPATH",
        }:
            env.pop(key, None)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["PYTHONIOENCODING"] = "utf-8"
    env["NO_COLOR"] = "1"
    if path is not None:
        env["PATH"] = path
    return env


def system_path() -> str:
    return os.environ.get("PATH", "")


def new_home(ctx: Context, *parts: str) -> Path:
    base = ctx.work.joinpath(*parts)
    if base.exists():
        shutil.rmtree(base)
    home = base / "home"
    home.mkdir(parents=True)
    return home


def create_signal_dir(home: Path, platform: str) -> None:
    (home / SIGNAL_DIRS[platform]).mkdir(parents=True, exist_ok=True)


def make_fake_cli(bin_dir: Path, names: list[str]) -> Path:
    bin_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        if os.name == "nt":
            executable = bin_dir / f"{name}.cmd"
            executable.write_text("@exit /b 0\r\n", encoding="ascii")
        else:
            executable = bin_dir / name
            executable.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
            executable.chmod(0o755)
    return bin_dir


def install_command(ctx: Context, arguments: list[str]) -> list[str]:
    return [
        ctx.python,
        str(ctx.repo / "install.py"),
        "--source",
        str(ctx.repo),
        "--no-uv",
        "--quiet",
        *arguments,
    ]


def run_installer(
    ctx: Context,
    home: Path,
    arguments: list[str],
    *,
    path: str | None = None,
    timeout: float = 600,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    env = clean_env(home, path=system_path() if path is None else path)
    if extra_env:
        env.update(extra_env)
    return run_command(
        ctx,
        install_command(ctx, arguments),
        env=env,
        timeout=timeout,
    )


def install_root_for(home: Path, platform: str) -> Path:
    """The personal skill root, including Codex's ~/.agents fallback."""
    root = EXPECTED[platform]["install_root"]
    if (
        platform == "codex"
        and not (home / ".codex").exists()
        and (home / ".agents").exists()
    ):
        root = "~/.agents/skills"
    return home / root[2:]


def personal_skill(home: Path, platform: str) -> Path:
    return install_root_for(home, platform) / SKILL


def norm(path: Path | str) -> str:
    return os.path.normcase(str(Path(path).resolve()))


# --------------------------------------------------------------------------- #
# tree, frontmatter, and state assertions
# --------------------------------------------------------------------------- #


def tree_digest(root: Path) -> dict[str, str]:
    digest: dict[str, str] = {}
    if not root.exists():
        return digest
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == ".venv-path" or relative.startswith(".venv/"):
            continue
        if "__pycache__" in relative.split("/") or relative.endswith((".pyc", ".pyo")):
            continue
        digest[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def diff_digests(expected: dict[str, str], actual: dict[str, str]) -> str:
    missing = sorted(set(expected) - set(actual))[:10]
    extra = sorted(set(actual) - set(expected))[:10]
    changed = sorted(
        path for path in set(expected) & set(actual) if expected[path] != actual[path]
    )[:10]
    parts = []
    if missing:
        parts.append(f"missing: {', '.join(missing)}")
    if extra:
        parts.append(f"extra: {', '.join(extra)}")
    if changed:
        parts.append(f"changed: {', '.join(changed)}")
    return "; ".join(parts) or "contents differ"


def read_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    require(bool(lines) and lines[0].strip() == "---", f"{path}: missing frontmatter opening")
    end = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    require(end is not None, f"{path}: frontmatter is not closed")
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        if line and not line[0].isspace() and ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip().strip('"')
    return fields, "\n".join(lines[end + 1 :])


def normalize_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def assert_skill_tree(ctx: Context, skill: Path, platform: str) -> None:
    expected = EXPECTED[platform]
    require(skill.is_dir(), f"{platform}: skill directory not found: {skill}")
    for relative in (
        "SKILL.md",
        "LICENSE",
        "INSTALL.md",
        "scripts/check_env.py",
        "scripts/render.py",
        "references",
        "assets/templates/clean-light.json",
        "assets/project/manim_lib/runtime.py",
    ):
        require((skill / relative).exists(), f"{platform}: missing {relative} in {skill}")

    dist = ctx.repo / "dist" / platform / "skills" / SKILL
    require(dist.is_dir(), f"missing generated build: {dist}")
    expected_tree = tree_digest(dist)
    actual_tree = tree_digest(skill)
    require(
        expected_tree == actual_tree,
        f"{platform}: installed tree differs from {dist}: {diff_digests(expected_tree, actual_tree)}",
    )

    fields, body = read_frontmatter(skill / "SKILL.md")
    require(fields.get("name") == SKILL, f"{platform}: frontmatter name is {fields.get('name')!r}")
    require(bool(fields.get("description")), f"{platform}: frontmatter has no description")
    for key in expected["frontmatter_drop"]:
        require(key not in fields, f"{platform}: frontmatter must not declare {key}")
    for key in ("license", "metadata"):
        if key not in expected["frontmatter_drop"]:
            require(key in fields, f"{platform}: frontmatter lost {key}")
    for line in expected["frontmatter_add"]:
        key, _, value = line.partition(":")
        key = key.strip()
        require(key in fields, f"{platform}: frontmatter is missing {key}")
        require(
            fields[key].strip().strip('"') == value.strip().strip('"'),
            f"{platform}: frontmatter {key} is {fields[key]!r}, expected {value.strip()!r}",
        )
    expects_argument_hint = any(
        line.startswith("argument-hint:") for line in expected["frontmatter_add"]
    )
    require(
        ("argument-hint" in fields) == expects_argument_hint,
        f"{platform}: argument-hint presence does not match the harness contract",
    )

    usage = normalize_text(ctx.repo / "platforms" / platform / "usage.md").strip()
    require(
        usage in body,
        f"{platform}: SKILL.md does not contain platforms/{platform}/usage.md",
    )
    for other, other_expected in EXPECTED.items():
        if other != platform:
            require(
                other_expected["usage_heading"] not in body,
                f"{platform}: SKILL.md contains the {other} usage section",
            )

    require(
        normalize_text(skill / "INSTALL.md")
        == normalize_text(ctx.repo / "platforms" / platform / "INSTALL.md"),
        f"{platform}: installed INSTALL.md is not the platform guide",
    )
    require(
        normalize_text(skill / "LICENSE") == normalize_text(ctx.repo / "LICENSE"),
        f"{platform}: installed LICENSE differs from the repository LICENSE",
    )

    agents = skill / "agents"
    if expected["include_agents"]:
        require((agents / "openai.yaml").is_file(), f"{platform}: missing agents/openai.yaml")
        require(
            normalize_text(agents / "openai.yaml")
            == normalize_text(ctx.repo / "platforms" / "codex" / "agents" / "openai.yaml"),
            f"{platform}: agents/openai.yaml differs from platforms/codex/agents/openai.yaml",
        )
    else:
        require(not agents.exists(), f"{platform}: agents/ should not be in this build")


def assert_state(
    ctx: Context,
    home: Path,
    platforms: dict[str, Path],
    *,
    venv: Path | None = None,
) -> dict:
    state_dir = home / ".manim-math-video"
    state_file = state_dir / "install.json"
    require(state_file.is_file(), f"state file not written: {state_file}")
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Failure(f"invalid state file {state_file}: {exc}") from exc
    version = (ctx.repo / "VERSION").read_text(encoding="utf-8").strip()
    require(state.get("version") == version, f"state version is {state.get('version')!r}, expected {version!r}")
    expected_venv = venv if venv is not None else state_dir / "venv"
    require(norm(state.get("venv", "")) == norm(expected_venv), f"state venv is {state.get('venv')!r}")
    require(bool(state.get("installed_at")), "state has no installed_at timestamp")
    recorded = state.get("platforms", {})
    require(set(recorded) == set(platforms), f"state platforms are {sorted(recorded)}, expected {sorted(platforms)}")
    for name, skill in platforms.items():
        require(norm(recorded[name]) == norm(skill), f"state path for {name} is {recorded[name]!r}, expected {skill}")
    return state


def assert_absent(skill: Path) -> None:
    require(not skill.exists(), f"unexpected installation: {skill}")


# --------------------------------------------------------------------------- #
# fast tests
# --------------------------------------------------------------------------- #


@test()
def manifest_matches_documented_harnesses(ctx: Context) -> None:
    manifest = json.loads((ctx.repo / "platforms" / "manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("skill") == SKILL, f"manifest skill is {manifest.get('skill')!r}")
    require(set(manifest.get("platforms", {})) == set(EXPECTED), "manifest platform list changed")
    for name, expected in EXPECTED.items():
        config = manifest["platforms"][name]
        for key in ("label", "install_root", "project_root", "include_agents"):
            require(
                config.get(key) == expected[key],
                f"{name}: manifest {key} is {config.get(key)!r}, expected {expected[key]!r}",
            )
        require(
            config.get("frontmatter_add", []) == expected["frontmatter_add"],
            f"{name}: manifest frontmatter_add drifted from the harness contract",
        )
        require(
            config.get("frontmatter_drop", []) == expected["frontmatter_drop"],
            f"{name}: manifest frontmatter_drop drifted from the harness contract",
        )


@test()
def dist_is_current(ctx: Context) -> None:
    home = new_home(ctx, "dist-check")
    result = run_command(
        ctx,
        [ctx.python, str(ctx.repo / "platforms" / "build.py"), "--check"],
        env=clean_env(home, path=system_path()),
        cwd=ctx.repo,
        timeout=120,
    )
    expect_success(result, "dist/ is stale; run: python platforms/build.py")


@test()
def reexec_handles_venv_symlinks(ctx: Context) -> None:
    """A venv's bin/python is normally a symlink to the base interpreter.

    The re-exec guard must compare the paths as invoked, not their resolved
    targets; otherwise Linux/macOS never switch to the managed environment.
    This runs with -S to make the dependency check deterministic even on a
    developer machine that has NumPy and Manim installed globally.
    """
    if os.name == "nt":
        raise SkipTest("venv python is not a symlink on Windows")
    home = new_home(ctx, "reexec-symlink")
    skill = home / ".claude" / "skills" / SKILL
    shutil.copytree(ctx.repo / "dist" / "claude" / "skills" / SKILL, skill)
    venv = home / ".manim-math-video" / "venv"
    (venv / "bin").mkdir(parents=True)
    os.symlink(ctx.python, venv / "bin" / "python")
    (skill / ".venv-path").write_text(str(venv) + "\n", encoding="utf-8")

    result = run_command(
        ctx,
        [ctx.python, "-S", str(skill / "scripts" / "check_env.py"), "--json", "--color", "never"],
        env=clean_env(home, path=system_path()),
        timeout=120,
    )
    require(
        "using the managed environment" in (result.stderr or ""),
        "check_env did not re-exec into a symlinked managed interpreter",
    )


@test()
def personal_install_for_every_harness(ctx: Context) -> None:
    for name, expected in EXPECTED.items():
        home = new_home(ctx, "personal", name)
        create_signal_dir(home, name)
        result = run_installer(
            ctx,
            home,
            ["--platform", name, "--no-deps"],
            timeout=180,
        )
        expect_success(result, f"{name}: personal install failed")
        skill = personal_skill(home, name)
        assert_skill_tree(ctx, skill, name)
        assert_state(ctx, home, {name: skill})
        require(expected["invoke"] in (result.stdout or ""), f"{name}: install output omits {expected['invoke']}")
        require(not (skill / ".venv-path").exists(), f"{name}: --no-deps wrote a .venv-path marker")
        require(
            not (home / ".manim-math-video" / "venv").exists(),
            f"{name}: --no-deps created an environment",
        )

        for other in EXPECTED:
            if other != name:
                assert_absent(personal_skill(home, other))


@test()
def codex_supports_both_skill_roots(ctx: Context) -> None:
    cases = [
        ("dot-codex", [".codex"], "~/.codex/skills"),
        ("agents", [".agents"], "~/.agents/skills"),
        ("default", [], "~/.codex/skills"),
    ]
    for label, directories, root in cases:
        home = new_home(ctx, "codex-roots", label)
        for directory in directories:
            (home / directory).mkdir(parents=True, exist_ok=True)
        result = run_installer(ctx, home, ["--platform", "codex", "--no-deps"], timeout=180)
        expect_success(result, f"codex/{label}: install failed")
        skill = home / root[2:] / SKILL
        assert_skill_tree(ctx, skill, "codex")
        assert_state(ctx, home, {"codex": skill})


@test()
def auto_detection_finds_the_right_harness(ctx: Context) -> None:
    cases = [
        ("claude-dir", [], [".claude"], ["claude"]),
        ("copilot-dir", [], [".copilot"], ["copilot"]),
        ("pi-dir", [], [".pi"], ["pi"]),
        ("codex-agents-dir", [], [".agents"], ["codex"]),
        ("codex-dotdir", [], [".codex"], ["codex"]),
        ("claude-cli", ["claude"], [], ["claude"]),
        ("all-signals", [], [".claude", ".codex", ".copilot", ".pi"], ["claude", "codex", "copilot", "pi"]),
        ("none", [], [], ["claude"]),
    ]
    for label, cli_names, directories, expected_names in cases:
        home = new_home(ctx, "auto-detect", label)
        for directory in directories:
            (home / directory).mkdir(parents=True, exist_ok=True)
        fake_bin = make_fake_cli(home.parent / "bin", cli_names)
        result = run_installer(
            ctx,
            home,
            ["--no-deps"],
            path=str(fake_bin),
            timeout=180,
        )
        expect_success(result, f"auto/{label}: install failed")
        mapping = {name: personal_skill(home, name) for name in expected_names}
        for name, skill in mapping.items():
            assert_skill_tree(ctx, skill, name)
        assert_state(ctx, home, mapping)
        for other in EXPECTED:
            if other not in mapping:
                assert_absent(personal_skill(home, other))
        if label == "none":
            require(
                "no agent installation detected" in (result.stdout or ""),
                "fallback to Claude Code was not announced",
            )


@test()
def project_install_uses_the_project_root(ctx: Context) -> None:
    for name, expected in EXPECTED.items():
        home = new_home(ctx, "project", name)
        suffix = "project with spaces" if name == "copilot" else "project"
        project = home.parent / suffix
        root = project / expected["project_root"]
        result = run_installer(
            ctx,
            home,
            ["--platform", name, "--root", str(root), "--no-deps"],
            timeout=180,
        )
        expect_success(result, f"{name}: project install failed")
        skill = root / SKILL
        assert_skill_tree(ctx, skill, name)
        assert_state(ctx, home, {name: skill})
        assert_absent(personal_skill(home, name))


@test()
def installer_rejects_invalid_requests(ctx: Context) -> None:
    home = new_home(ctx, "negative")
    cases = [
        (["--platform", "nope", "--no-deps"], "unknown platform"),
        (
            ["--platform", "all", "--root", str(home.parent / "project"), "--no-deps"],
            "single platform",
        ),
    ]
    for arguments, fragment in cases:
        result = run_installer(ctx, home, arguments, timeout=120)
        require(result.returncode != 0, f"expected failure for {arguments}: {describe(result)}")
        output = (result.stdout or "") + (result.stderr or "")
        require(fragment in output, f"missing {fragment!r} for {arguments}: {output}")
    require(not (home / ".manim-math-video" / "install.json").exists(), "failed runs wrote state")

    empty = home.parent / "empty-source"
    empty.mkdir(exist_ok=True)
    result = run_command(
        ctx,
        [
            ctx.python,
            str(ctx.repo / "install.py"),
            "--source",
            str(empty),
            "--platform",
            "claude",
            "--no-deps",
        ],
        env=clean_env(home, path=system_path()),
        timeout=120,
    )
    require(result.returncode != 0, f"empty --source was accepted: {describe(result)}")
    require("not a checkout" in (result.stderr or ""), "empty --source error is unclear")


@test()
def dry_run_changes_nothing(ctx: Context) -> None:
    home = new_home(ctx, "dry-run")
    result = run_installer(ctx, home, ["--platform", "all", "--no-deps", "--dry-run"], timeout=120)
    expect_success(result, "--dry-run failed")
    require("Dry run" in (result.stdout or ""), "--dry-run did not report its mode")
    require(not (home / ".manim-math-video").exists(), "--dry-run created state")
    for name in EXPECTED:
        assert_absent(personal_skill(home, name))

    uninstall = run_installer(ctx, home, ["--uninstall", "--dry-run"], timeout=120)
    expect_success(uninstall, "uninstall --dry-run failed")
    require("Dry run" in (uninstall.stdout or ""), "uninstall --dry-run did not report its mode")
    require(not (home / ".manim-math-video").exists(), "uninstall --dry-run created state")


@test()
def reinstall_keeps_the_environment_and_refreshes_files(ctx: Context) -> None:
    home = new_home(ctx, "reinstall")
    create_signal_dir(home, "claude")
    arguments = ["--platform", "claude", "--no-deps"]
    first = run_installer(ctx, home, arguments, timeout=180)
    expect_success(first, "first install failed")
    skill = personal_skill(home, "claude")
    (skill / ".venv").mkdir()
    (skill / ".venv" / "sentinel").write_text("keep me\n", encoding="utf-8")
    (skill / "STALE.txt").write_text("remove me\n", encoding="utf-8")

    second = run_installer(ctx, home, arguments, timeout=180)
    expect_success(second, "reinstall failed")
    require((skill / ".venv" / "sentinel").is_file(), "reinstall removed the managed .venv")
    require(
        (skill / ".venv" / "sentinel").read_text(encoding="utf-8") == "keep me\n",
        "reinstall changed the managed .venv",
    )
    require(not (skill / "STALE.txt").exists(), "reinstall left a stale file behind")
    require(
        not (skill.parent / f".{SKILL}-venv-stash").exists(),
        "reinstall left a .venv stash behind",
    )
    assert_skill_tree(ctx, skill, "claude")
    assert_state(ctx, home, {"claude": skill})


@test()
def uninstall_removes_only_managed_files(ctx: Context) -> None:
    home = new_home(ctx, "uninstall")
    for name in EXPECTED:
        create_signal_dir(home, name)
    result = run_installer(ctx, home, ["--platform", "all", "--no-deps"], timeout=180)
    expect_success(result, "install before uninstall failed")
    mapping = {name: personal_skill(home, name) for name in EXPECTED}
    state_dir = home / ".manim-math-video"
    venv = state_dir / "venv"
    (venv / "bin").mkdir(parents=True)
    (venv / "bin" / "python").write_text("sentinel\n", encoding="utf-8")
    unrelated = home / ".claude" / "skills" / "someone-elses-skill"
    unrelated.mkdir()

    dry = run_installer(ctx, home, ["--uninstall", "--dry-run"], timeout=120)
    expect_success(dry, "uninstall --dry-run failed")
    require("Dry run" in (dry.stdout or ""), "uninstall --dry-run did not report its mode")
    for skill in mapping.values():
        require(skill.exists(), f"uninstall --dry-run removed {skill}")
    require((state_dir / "install.json").is_file(), "uninstall --dry-run removed the state file")
    require(venv.exists(), "uninstall --dry-run removed the environment")

    result = run_installer(ctx, home, ["--uninstall"], timeout=120)
    expect_success(result, "uninstall failed")
    for name, skill in mapping.items():
        require(not skill.exists(), f"uninstall left {name} at {skill}")
    require(not venv.exists(), "uninstall left the environment behind")
    require(not (state_dir / "install.json").exists(), "uninstall left the state file behind")
    require(unrelated.exists(), "uninstall removed an unrelated skill")


@test()
def uninstall_handles_symlinked_home(ctx: Context) -> None:
    if os.name == "nt":
        raise SkipTest("symlinked HOME paths are a POSIX case")
    base = ctx.work / "uninstall-symlink"
    real_home = base / "real-home"
    real_home.mkdir(parents=True)
    link_home = base / "home-link"
    link_home.symlink_to(real_home, target_is_directory=True)
    for name in EXPECTED:
        create_signal_dir(link_home, name)
    result = run_installer(ctx, link_home, ["--platform", "all", "--no-deps"], timeout=180)
    expect_success(result, "install with symlinked HOME failed")
    state_dir = link_home / ".manim-math-video"
    venv = state_dir / "venv"
    (venv / "bin").mkdir(parents=True)
    (venv / "bin" / "python").write_text("sentinel\n", encoding="utf-8")

    result = run_installer(ctx, link_home, ["--uninstall"], timeout=120)
    expect_success(result, "uninstall with symlinked HOME failed")
    require(not venv.exists(), "uninstall left the environment behind with a symlinked HOME")
    require(not (state_dir / "install.json").exists(), "uninstall left the state file behind")


@test()
def install_sh_wrapper_uses_the_checkout(ctx: Context) -> None:
    if os.name == "nt":
        raise SkipTest("install.sh is POSIX-only")
    bash = shutil.which("bash")
    if not bash:
        raise SkipTest("bash is not available")
    home = new_home(ctx, "install-sh")
    create_signal_dir(home, "claude")
    result = run_command(
        ctx,
        [
            bash,
            str(ctx.repo / "install.sh"),
            "--platform",
            "claude",
            "--no-deps",
            "--quiet",
        ],
        env=clean_env(home),
        timeout=180,
    )
    expect_success(result, "install.sh failed")
    skill = personal_skill(home, "claude")
    assert_skill_tree(ctx, skill, "claude")
    assert_state(ctx, home, {"claude": skill})


@test()
def one_liner_download_and_install(ctx: Context) -> None:
    """Exercise the no-__file__ download path with a local archive.

    ``python -c "exec(...)"`` has no __file__, so install.py downloads the
    checkout. MMS_ARCHIVE_URL points that download at a tarball built here.
    """
    home = new_home(ctx, "one-liner")
    create_signal_dir(home, "claude")

    archive = home.parent / "repo.tar.gz"
    root_name = "manim-math-video-studio-main"
    included = ["install.py", "VERSION", "LICENSE", "requirements.txt", "platforms", "dist"]
    with tarfile.open(archive, "w:gz") as bundle:
        for relative in included:
            source = ctx.repo / relative
            require(source.exists(), f"repository is missing {relative}")
            bundle.add(source, arcname=f"{root_name}/{relative}")

    bootstrap = (
        "import sys\n"
        "path = sys.argv[1]\n"
        "sys.argv = [path, *sys.argv[2:]]\n"
        "with open(path, encoding='utf-8') as handle:\n"
        "    exec(compile(handle.read(), path, 'exec'))\n"
    )
    env = clean_env(home)
    env["MMS_ARCHIVE_URL"] = archive.as_uri()
    result = run_command(
        ctx,
        [
            ctx.python,
            "-c",
            bootstrap,
            str(ctx.repo / "install.py"),
            "--platform",
            "claude",
            "--no-deps",
            "--quiet",
        ],
        env=env,
        timeout=180,
    )
    expect_success(result, "python -c install failed")
    skill = personal_skill(home, "claude")
    assert_skill_tree(ctx, skill, "claude")
    assert_state(ctx, home, {"claude": skill})


# --------------------------------------------------------------------------- #
# runtime tests
# --------------------------------------------------------------------------- #


def runtime_install(ctx: Context) -> dict[str, object]:
    state = ctx.runtime.get("installed")
    if not isinstance(state, dict):
        raise SkipTest("runtime installation did not complete")
    return state


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


@test("runtime")
def runtime_install_builds_one_shared_environment(ctx: Context) -> None:
    home = new_home(ctx, "runtime")
    for name in EXPECTED:
        create_signal_dir(home, name)
    venv = home / ".manim-math-video" / "venv"
    result = run_installer(
        ctx,
        home,
        ["--platform", "all", "--venv", str(venv)],
        timeout=3600,
    )
    expect_success(result, "runtime install failed; see the pip output above")
    python = venv_python(venv)
    require(python.is_file(), f"installer did not create {python}")
    mapping = {name: personal_skill(home, name) for name in EXPECTED}
    for name, skill in mapping.items():
        assert_skill_tree(ctx, skill, name)
        marker = skill / ".venv-path"
        require(marker.is_file(), f"{name}: missing .venv-path")
        require(
            norm(marker.read_text(encoding="utf-8").strip()) == norm(venv),
            f"{name}: .venv-path points somewhere else",
        )
    assert_state(ctx, home, mapping, venv=venv)
    require("Ready" in (result.stdout or ""), "installer did not report Ready")
    for name, expected in EXPECTED.items():
        require(expected["invoke"] in (result.stdout or ""), f"{name}: invocation is not in the output")
    ctx.runtime["installed"] = {"home": home, "venv": venv, "skills": mapping}


@test("runtime")
def runtime_check_env_passes_every_harness(ctx: Context) -> None:
    state = runtime_install(ctx)
    home = state["home"]
    venv = state["venv"]
    python = venv_python(venv)
    for name, skill in state["skills"].items():
        result = run_command(
            ctx,
            [str(python), str(skill / "scripts" / "check_env.py"), "--json", "--color", "never"],
            env=clean_env(home, path=system_path()),
            timeout=180,
        )
        require(result.returncode == 0, f"{name}: check_env failed\n{describe(result)}")
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise Failure(f"{name}: check_env did not emit JSON: {exc}\n{tail(result.stdout)}") from exc
        require(report.get("ok") is True, f"{name}: environment is not ready: {report}")
        rows = {row["component"]: row for row in report["checks"]}
        for component in (
            "Python",
            "Manim",
            "manim executable",
            "edge-tts",
            "PyAV",
            "NumPy",
            "Pillow",
            "Skill assets",
        ):
            require(component in rows, f"{name}: check_env has no {component!r} row")
            require(rows[component]["status"] == "ok", f"{name}: {component} is {rows[component]['status']!r}")
        require(
            not any(row["status"] == "fail" for row in report["checks"]),
            f"{name}: check_env reported a blocking failure",
        )
        for component in ("LaTeX", "dvisvgm"):
            row = rows[component]
            if row["status"] != "warn":
                continue
            hint = row["recommendation"].lower()
            require(
                any(
                    token in hint
                    for token in ("apt", "dnf", "pacman", "brew", "winget", "tlmgr", "miktex")
                ),
                f"{name}: {component} warning has no install command: {row['recommendation']!r}",
            )


@test("runtime")
def runtime_reexec_finds_the_shared_environment(ctx: Context) -> None:
    state = runtime_install(ctx)
    home = state["home"]
    skills = state["skills"]
    probe = run_command(
        ctx,
        [ctx.python, "-c", "import manim, numpy, av, PIL"],
        env=clean_env(home, path=system_path()),
        timeout=60,
    )
    if probe.returncode == 0:
        raise SkipTest("the starting interpreter already has the runtime dependencies")

    for name, skill in skills.items():
        check = skill / "scripts" / "check_env.py"
        result = run_command(
            ctx,
            [ctx.python, str(check), "--json", "--color", "never"],
            env=clean_env(home, path=system_path()),
            timeout=180,
        )
        require(result.returncode == 0, f"{name}: re-exec check_env failed\n{describe(result)}")
        require(
            "using the managed environment" in (result.stderr or ""),
            f"{name}: check_env did not re-exec into the shared environment",
        )
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise Failure(f"{name}: re-exec produced invalid JSON: {exc}\n{tail(result.stdout)}") from exc
        require(report.get("ok") is True, f"{name}: re-exec environment is not ready")

        blocked_env = {**clean_env(home, path=system_path()), "MANIM_STUDIO_NO_REEXEC": "1"}
        blocked = run_command(
            ctx,
            [ctx.python, str(check), "--json", "--color", "never"],
            env=blocked_env,
            timeout=180,
        )
        require(blocked.returncode != 0, f"{name}: MANIM_STUDIO_NO_REEXEC did not block the re-exec")
        try:
            blocked_report = json.loads(blocked.stdout)
        except json.JSONDecodeError as exc:
            raise Failure(f"{name}: no-reexec check did not emit JSON: {exc}") from exc
        require(blocked_report.get("ok") is False, f"{name}: no-reexec unexpectedly reported a ready environment")


@test("runtime")
def runtime_selftest_passes_for_every_harness(ctx: Context) -> None:
    state = runtime_install(ctx)
    python = venv_python(state["venv"])
    for name, skill in state["skills"].items():
        result = run_command(
            ctx,
            [str(python), str(skill / "scripts" / "selftest.py")],
            env=clean_env(state["home"], path=system_path()),
            timeout=180,
        )
        expect_success(result, f"{name}: installed skill self-test failed")
        require("Self-test passed." in (result.stdout or ""), f"{name}: self-test did not pass")


@test("runtime")
def runtime_smoke_render(ctx: Context) -> None:
    if not ctx.render:
        raise SkipTest("pass --render to run the Manim smoke render")
    state = runtime_install(ctx)
    python = venv_python(state["venv"])
    skill = state["skills"]["claude"]
    result = run_command(
        ctx,
        [str(python), str(skill / "scripts" / "selftest.py"), "--full"],
        env=clean_env(state["home"], path=system_path()),
        timeout=1800,
    )
    expect_success(result, "Manim smoke render failed")
    require("ok   smoke render" in (result.stdout or ""), "smoke render produced no MP4")


# --------------------------------------------------------------------------- #
# runner
# --------------------------------------------------------------------------- #


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scope", choices=["fast", "runtime"], default="fast", help="fast layout checks or a full dependency install")
    parser.add_argument("--render", action="store_true", help="run the Manim smoke render in the runtime scope")
    parser.add_argument("--repo", default=str(Path(__file__).resolve().parents[1]), help="repository root")
    parser.add_argument("--python", default=sys.executable, help="interpreter used to run install.py")
    parser.add_argument("--verbose", action="store_true", help="show commands and their output")
    parser.add_argument("--keep", action="store_true", help="keep the temporary HOME tree")
    parser.add_argument("--json", action="store_true", help="emit a JSON summary")
    parser.add_argument("--list", action="store_true", help="list tests and exit")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    if args.list:
        for item in TESTS:
            print(f"{item.scope:8} {item.name}")
        return 0

    repo = Path(args.repo).resolve()
    require_repo = [
        repo / "install.py",
        repo / "platforms" / "manifest.json",
        repo / "dist" / "claude" / "skills" / SKILL / "SKILL.md",
    ]
    missing = [str(path) for path in require_repo if not path.exists()]
    if missing:
        print(f"not a complete checkout: missing {', '.join(missing)}", file=sys.stderr)
        return 2

    selected = [item for item in TESTS if item.scope == "fast" or args.scope == "runtime"]
    work = Path(tempfile.mkdtemp(prefix="mms-install-tests-"))
    ctx = Context(
        repo=repo,
        python=args.python,
        work=work,
        verbose=args.verbose,
        render=args.render,
    )

    outcomes: list[Outcome] = []
    started = time.time()
    if not args.json:
        print(
            f"install matrix: scope={args.scope} python={sys.version.split()[0]} "
            f"platform={sys.platform}",
            flush=True,
        )
        print(f"checkout: {repo}\nwork: {work}\n", flush=True)

    try:
        for item in selected:
            began = time.time()
            try:
                item.function(ctx)
                elapsed = time.time() - began
                outcomes.append(Outcome(item.name, "pass", elapsed))
                if not args.json:
                    print(f"  PASS  {item.name} ({elapsed:.1f}s)", flush=True)
            except SkipTest as exc:
                elapsed = time.time() - began
                outcomes.append(Outcome(item.name, "skip", elapsed, str(exc)))
                if not args.json:
                    print(f"  SKIP  {item.name} ({exc})", flush=True)
            except Failure as exc:
                elapsed = time.time() - began
                outcomes.append(Outcome(item.name, "fail", elapsed, str(exc)))
                if not args.json:
                    print(f"  FAIL  {item.name} ({elapsed:.1f}s)", flush=True)
                    for line in str(exc).splitlines():
                        print(f"        {line}", flush=True)
            except Exception as exc:  # noqa: BLE001 - show unexpected errors as failures
                elapsed = time.time() - began
                message = f"{type(exc).__name__}: {exc}"
                outcomes.append(Outcome(item.name, "fail", elapsed, message))
                if not args.json:
                    print(f"  FAIL  {item.name} ({elapsed:.1f}s)", flush=True)
                    for line in traceback.format_exc().splitlines():
                        print(f"        {line}", flush=True)
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)

    passed = sum(1 for item in outcomes if item.status == "pass")
    skipped = sum(1 for item in outcomes if item.status == "skip")
    failed = sum(1 for item in outcomes if item.status == "fail")
    elapsed = time.time() - started

    if args.json:
        payload = {
            "ok": failed == 0,
            "scope": args.scope,
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "seconds": round(elapsed, 2),
            "passed": passed,
            "skipped": skipped,
            "failed": failed,
            "tests": [item.__dict__ for item in outcomes],
            "work": str(work),
        }
        print(json.dumps(payload, indent=2))
    else:
        if args.keep:
            print(f"\nwork tree kept: {work}")
        print(f"\n{passed} passed, {skipped} skipped, {failed} failed in {elapsed:.1f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
