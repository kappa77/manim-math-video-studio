# syntax=docker/dockerfile:1
#
# Installer verification image. Two targets:
#
#   fast     stdlib-only harness/installer tests (no Python packages needed)
#   runtime  Manim's native libraries plus a real requirements.txt install and
#            an optional smoke render
#
# Build from the repository root:
#   docker build -f tests/docker/Dockerfile --target fast .
#   docker build -f tests/docker/Dockerfile --target runtime .
#
# tests/docker/run.sh does this for a matrix of Python versions.

ARG PYTHON_IMAGE=python:3.12-slim-bookworm

FROM ${PYTHON_IMAGE} AS fast

SHELL ["/bin/sh", "-c"]

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    NO_COLOR=1

WORKDIR /opt/manim-math-video

COPY . .

# bash is only needed for the install.sh wrapper test. Alpine images have no
# apt-get, so the same layer supports both Debian slim and Alpine.
RUN set -eux; \
    if command -v apt-get >/dev/null 2>&1; then \
        apt-get update; \
        apt-get install -y --no-install-recommends bash; \
        rm -rf /var/lib/apt/lists/*; \
    elif command -v apk >/dev/null 2>&1; then \
        apk add --no-cache bash; \
    fi

# Fail the image build before running tests if the generated trees are stale.
RUN python platforms/build.py --check

CMD ["python", "tests/install_matrix.py", "--scope", "fast"]


FROM fast AS runtime

# Manim's Cairo renderer needs Pango/cairo at runtime; the rest makes the
# environment check and the smoke render realistic.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        fonts-dejavu-core \
        libcairo2 \
        libcairo2-dev \
        libgdk-pixbuf-2.0-0 \
        libpango-1.0-0 \
        libpango1.0-dev \
        libpangocairo-1.0-0 \
        pkg-config; \
    rm -rf /var/lib/apt/lists/*

CMD ["python", "tests/install_matrix.py", "--scope", "runtime", "--render"]
