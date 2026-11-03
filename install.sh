#!/usr/bin/env bash
# One-command installer for the manim-math-video agent skill.
#
#   curl -fsSL https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --platform codex --with-latex
#   ./install.sh                      # from a clone
#   ./install.sh --platform claude --tts-provider cartesia
#
# Override the source with MMS_REPO=owner/name MMS_REF=main (or v0.1.0).
set -euo pipefail

REPO="${MMS_REPO:-kappa77/manim-math-video-studio}"
REF="${MMS_REF:-main}"

fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }

find_python() {
    for candidate in python3.13 python3.12 python3.11 python3.10 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' >/dev/null 2>&1; then
                printf '%s' "$candidate"
                return 0
            fi
        fi
    done
    if command -v py >/dev/null 2>&1; then
        if py -3 -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)' >/dev/null 2>&1; then
            printf 'py -3'
            return 0
        fi
    fi
    return 1
}

PYTHON="$(find_python)" || fail "Python 3.10+ not found. Install it from https://www.python.org/downloads/ and rerun."

# Running from a checkout: use the local installer and tree.
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-}")" 2>/dev/null && pwd || true)"
if [ -n "$HERE" ] && [ -f "$HERE/install.py" ]; then
    exec $PYTHON "$HERE/install.py" --source "$HERE" "$@"
fi

# Piped install: fetch the repository archive, then run the installer from it.
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

URL="https://codeload.github.com/$REPO/tar.gz/refs/heads/$REF"
printf 'Fetching %s@%s\n' "$REPO" "$REF"
if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$URL" -o "$WORK/repo.tar.gz" || fail "download failed: $URL"
elif command -v wget >/dev/null 2>&1; then
    wget -qO "$WORK/repo.tar.gz" "$URL" || fail "download failed: $URL"
else
    fail "need curl or wget to download the installer"
fi

mkdir -p "$WORK/src"
tar -xzf "$WORK/repo.tar.gz" -C "$WORK/src" --strip-components=1 || fail "could not unpack the archive"

$PYTHON "$WORK/src/install.py" --source "$WORK/src" "$@"
