# Installer and harness tests

The installer is the front door of this project: it detects agents, copies the
right prebuilt skill tree, provisions one shared Python environment, and records
what it did. These tests exercise that whole path against a simulated copy of
every supported harness.

The suite is standard-library only. Docker is the recommended way to get a
clean Linux machine and a Python-version matrix, not a requirement:

```bash
python tests/install_matrix.py --scope fast       # any Python 3.10+
python tests/install_matrix.py --scope runtime    # creates the real venv
```

## What gets verified

### `--scope fast`

No third-party packages and no network access. Every scenario runs in a
throwaway `HOME`, so it cannot touch your real agent installation.

| Check | What it proves |
|---|---|
| Manifest contract | `platforms/manifest.json` still matches the documented install roots, frontmatter edits, and Codex `agents/openai.yaml` rule |
| Generated trees | `python platforms/build.py --check` passes, so `dist/` is not stale |
| Re-exec symlinks | A managed venv whose `bin/python` is a symlink (the normal Linux/macOS layout) still triggers the switch to the shared environment |
| TTS provider selection | The installer persists Cartesia/ElevenLabs preferences and models without writing API keys; missing keys produce a warning, and dry runs write nothing |
| Native TTS checks | `tts.py --check` reports the provider model and rejects a missing Cartesia/ElevenLabs key |
| Personal install | For each of Claude Code, Codex, GitHub Copilot, and Pi: the skill lands in the right root, the tree is byte-identical to `dist/<harness>/`, frontmatter is correct, `INSTALL.md` and `LICENSE` are present, and the platform usage section is in `SKILL.md` |
| Codex roots | `~/.codex/skills`, `~/.agents/skills`, and the documented fallback all work |
| Auto-detection | Configuration directories (`~/.claude`, `~/.codex`, `~/.agents`, `~/.copilot`, `~/.pi`) and CLI names on `PATH` select the right harness; an empty machine falls back to Claude Code |
| Project installs | `--root` puts the skill under `.claude/skills`, `.agents/skills`, `.github/skills`, or `.pi/skills`, including paths with spaces |
| Invalid requests | Unknown platforms, `--root` with several platforms, and a bad `--source` fail without writing state |
| Dry runs | `--dry-run` and `--uninstall --dry-run` change nothing |
| Reinstall | Files are refreshed, a managed `.venv` is preserved, and no stash is left behind |
| Uninstall | Only recorded skill directories, the shared environment, and the state file are removed, including when `HOME` is a symlinked path |
| Wrappers | `install.sh` resolves the checkout and installs; the `python -c "exec(...)"` path downloads from `MMS_ARCHIVE_URL` (a local archive) and installs without `__file__` |

### `--scope runtime`

The runtime scope runs the fast suite first, then:

| Check | What it proves |
|---|---|
| Shared environment | One venv is created and `requirements.txt` installs successfully |
| `.venv-path` | Every installed harness records the shared environment |
| `check_env.py` | Python, Manim, the `manim` executable, edge-tts, PyAV, NumPy, Pillow, and skill assets are all `ok` for every harness |
| Re-exec | Calling a skill script with an interpreter that lacks the dependencies switches to the shared environment; `MANIM_STUDIO_NO_REEXEC=1` disables it |
| Skill self-test | The asset checks pass from every installed harness |
| Native TTS | A local mock API verifies Cartesia and ElevenLabs request paths, auth headers, payloads, WAV output, and manifest metadata |
| `--render` | A silent two-beat Manim render produces an MP4 (needs the native Pango/cairo libraries) |

## Docker

```bash
tests/docker/run.sh                              # fast matrix
tests/docker/run.sh --scope runtime --render     # real dependencies + smoke render
tests/docker/run.sh --scope all                  # both
tests/docker/run.sh --image python:3.11-slim-bookworm --scope fast
```

The fast matrix is:

| Image | Why |
|---|---|
| `python:3.10-slim-bookworm` | The minimum supported Python |
| `python:3.11-slim-bookworm` | Middle of the supported range |
| `python:3.12-slim-bookworm` | The runtime baseline |
| `python:3.13-slim-bookworm` | Newest CPython in the supported test matrix |
| `python:3.12-alpine` | No `apt-get`, musl libc, BusyBox userland |

The runtime target uses `python:3.12-slim-bookworm` plus `ffmpeg`, fonts,
Manim's cairo/pango libraries, and a C toolchain (pycairo and manimpango are
source builds on Linux). It needs network access to install `requirements.txt`
on the first run. The native TTS smoke test uses a local HTTP mock, not the real
Cartesia/ElevenLabs APIs. Other options: `--no-cache`, `--pull`, `DOCKER=podman`.

The image runs `platforms/build.py --check` at build time, so a stale `dist/`
fails before any test starts.

## Harness simulation

Each test writes the directory and CLI signals the real agent uses:

| Harness | Detection signals | Personal root | Project root |
|---|---|---|---|
| Claude Code | `claude` on `PATH`, `~/.claude` | `~/.claude/skills/` | `.claude/skills/` |
| Codex | `codex` on `PATH`, `~/.codex`, `~/.agents` | `~/.codex/skills/` or `~/.agents/skills/` | `.agents/skills/` |
| GitHub Copilot | `copilot` on `PATH`, `~/.copilot` | `~/.copilot/skills/` | `.github/skills/` |
| Pi | `pi` on `PATH`, `~/.pi` | `~/.pi/agent/skills/` | `.pi/skills/` |

Fake CLI scripts are empty executables: the installer only calls `shutil.which`,
so signing into a real agent is neither needed nor attempted. The contracts
being tested come from the Agent Skills specification and each harness's
documentation; if a host changes its discovery rules, update `EXPECTED` in
`tests/install_matrix.py`, `platforms/manifest.json`, and the matching
`platforms/<harness>/INSTALL.md` together.

## Adding a harness

1. Add the platform to `platforms/manifest.json`, `install.py`'s `PLATFORMS`
   and `INVOKE`/`CLI` maps, `platforms/<harness>/`, and the build.
2. Add it to `EXPECTED` and `SIGNAL_DIRS` in `tests/install_matrix.py`.
3. Add it to the harness table in `tests/README.md` and the docs.
4. Run the fast suite, rebuild `dist/`, then run the fast suite again.

## Keeping the suite healthy

- It runs against `dist/`, not the canonical tree. Rebuild after editing the
  skill; the first test fails with an actionable message when `dist/` is stale.
- Failures print the failing command, exit code, and trimmed stdout/stderr.
  Add `--verbose` to see every command and its tail, or `--keep` to inspect the
  temporary HOME trees.
- `--json` emits a machine-readable summary for CI dashboards.
- CI runs the fast matrix and the runtime suite in
  `.github/workflows/install-tests.yml`, plus the fast suite natively on Windows
  and macOS. A `package` job builds the wheel and sdist into `release-dist/`,
  runs `twine check`, installs both in clean environments, verifies the wheel is
  thin, and checks that the package version matches `VERSION`.
