#!/usr/bin/env bash
# Build and run the installer verification suite in clean Linux containers.
#
#   tests/docker/run.sh                     # fast matrix: Python 3.10-3.13 + Alpine
#   tests/docker/run.sh --scope runtime     # real venv and dependencies
#   tests/docker/run.sh --scope runtime --render   # plus a smoke render
#   tests/docker/run.sh --scope all         # both
#   tests/docker/run.sh --image python:3.11-slim-bookworm --scope fast
#
# Options:
#   --scope fast|runtime|all   Which suite to run (default: fast)
#   --image IMAGE              Run one base image instead of the default matrix
#   --render                   Run the Manim smoke render (runtime only)
#   --no-cache                 Pass --no-cache to docker build
#   --pull                     Pass --pull to docker build
#   -h, --help                 Show this help
#
# Set DOCKER="podman" to use a drop-in replacement.

set -euo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
DOCKERFILE="$REPO_ROOT/tests/docker/Dockerfile"
DOCKER="${DOCKER:-docker}"

SCOPE="fast"
IMAGES=()
RENDER=0
NO_CACHE=0
PULL=0

usage() {
    sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --scope)
            SCOPE="${2:?--scope needs a value}"
            shift 2
            ;;
        --scope=*)
            SCOPE="${1#*=}"
            shift
            ;;
        --image)
            IMAGES+=("${2:?--image needs a value}")
            shift 2
            ;;
        --image=*)
            IMAGES+=("${1#*=}")
            shift
            ;;
        --render)
            RENDER=1
            shift
            ;;
        --no-cache)
            NO_CACHE=1
            shift
            ;;
        --pull)
            PULL=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

case "$SCOPE" in
    fast|runtime|all) ;;
    *)
        echo "unknown --scope: $SCOPE (choose fast, runtime, or all)" >&2
        exit 2
        ;;
esac

if ! command -v "$DOCKER" >/dev/null 2>&1; then
    echo "error: $DOCKER is not installed or not on PATH" >&2
    exit 2
fi

tag_for() {
    printf 'manim-math-video-tests-%s:%s' "$1" "$(printf '%s' "$2" | tr '/:@' '----' | tr '[:upper:]' '[:lower:]')"
}

run_one() {
    local image="$1" target="$2"
    local tag
    tag="$(tag_for "$target" "$image")"
    local -a build_args=(build --file "$DOCKERFILE" --target "$target" --build-arg "PYTHON_IMAGE=$image" --tag "$tag")
    local -a test_args=(python tests/install_matrix.py --scope "$target")

    [ "$NO_CACHE" = 1 ] && build_args+=(--no-cache)
    [ "$PULL" = 1 ] && build_args+=(--pull)
    [ "$RENDER" = 1 ] && [ "$target" = runtime ] && test_args+=(--render)

    echo
    echo "==> building $tag"
    "$DOCKER" "${build_args[@]}" "$REPO_ROOT"

    echo "==> $target suite: $image"
    "$DOCKER" run --rm "$tag" "${test_args[@]}"
}

run_scope() {
    local target="$1"
    local -a images=()

    if [ "${#IMAGES[@]}" -gt 0 ]; then
        images=("${IMAGES[@]}")
    elif [ "$target" = runtime ]; then
        images=("python:3.12-slim-bookworm")
    else
        images=(
            "python:3.10-slim-bookworm"
            "python:3.11-slim-bookworm"
            "python:3.12-slim-bookworm"
            "python:3.13-slim-bookworm"
            "python:3.12-alpine"
        )
    fi

    for image in "${images[@]}"; do
        run_one "$image" "$target"
    done
}

case "$SCOPE" in
    fast)
        run_scope fast
        ;;
    runtime)
        run_scope runtime
        ;;
    all)
        run_scope fast
        IMAGES=()
        run_scope runtime
        ;;
esac

echo
echo "installer test matrix finished: $SCOPE"
