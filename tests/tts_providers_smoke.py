#!/usr/bin/env python3
"""Smoke-test the native Cartesia and ElevenLabs adapters without real keys.

A local HTTP server stands in for both APIs. The test verifies request paths,
headers, payloads, WAV output, manifest metadata, and the ElevenLabs WAV
conversion path. Run with the shared runtime environment:

    python tests/tts_providers_smoke.py
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import av  # noqa: F401 - the runtime environment provides PyAV
except ImportError:
    av = None


def silent_wav(seconds: float = 0.2) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(44100)
        handle.writeframes(b"\0\0" * int(44100 * seconds))
    return buffer.getvalue()


class Handler(BaseHTTPRequestHandler):
    records: list[dict] = []
    wav = silent_wav()

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path.startswith("/voices"):
            payload = {
                "data": [
                    {
                        "id": "cartesia-voice",
                        "name": "Cartesia Voice",
                        "gender": "feminine",
                        "tagline": "warm",
                    }
                ],
                "has_more": False,
            }
        elif self.path.startswith("/v2/voices"):
            payload = {
                "voices": [
                    {
                        "voice_id": "eleven-voice",
                        "name": "Eleven Voice",
                        "labels": {"gender": "female", "description": "warm"},
                    }
                ]
            }
        else:
            self.send_error(404)
            return
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        Handler.records.append(
            {
                "path": self.path,
                "headers": {key.casefold(): value for key, value in self.headers.items()},
                "body": json.loads(body.decode("utf-8")),
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(Handler.wav)))
        self.end_headers()
        self.wfile.write(Handler.wav)

    def log_message(self, *args) -> None:
        pass


def write_episode(root: Path, provider: str, voice: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    brief = {
        "schema_version": 1,
        "episode": {"title": "Provider smoke", "slug": "provider-smoke", "target_duration_seconds": 2},
        "output": {
            "language": "en-US",
            "captions": True,
            "voice": {
                "provider": provider,
                "id": voice,
                "style": "warm-teacher",
                "rate": "-8%",
                "pitch": "+0Hz",
                "volume": "+0%",
            },
            "voice_selection": {"status": "confirmed", "voice_id": voice, "user_choice": "smoke"},
        },
        "accuracy": {"pronunciations": {}, "notation": [], "sources": [], "claims_to_verify": []},
    }
    storyboard = {
        "schema_version": 1,
        "episode_id": "s01e001",
        "episode_slug": "provider-smoke",
        "title": "Provider smoke",
        "language": "en-US",
        "template": "clean-light",
        "beats": [
            {
                "id": "title",
                "kind": "title",
                "title": "Provider smoke",
                "narration": "This is a short provider smoke test.",
                "duration_hint": 1.0,
            }
        ],
    }
    (root / "brief.json").write_text(json.dumps(brief, indent=2), encoding="utf-8")
    (root / "storyboard.json").write_text(json.dumps(storyboard, indent=2), encoding="utf-8")
    return root


def run_provider(
    repo: Path,
    provider: str,
    voice: str,
    port: int,
) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"tts-{provider}-") as temporary:
        episode = write_episode(Path(temporary) / "episode", provider, voice)
        env = dict(os.environ)
        env["MANIM_STUDIO_NO_REEXEC"] = "1"
        env["CARTESIA_API_KEY"] = "test-cartesia"
        env["CARTESIA_API_URL"] = f"http://127.0.0.1:{port}"
        env["ELEVENLABS_API_KEY"] = "test-elevenlabs"
        env["ELEVENLABS_API_URL"] = f"http://127.0.0.1:{port}"
        result = subprocess.run(
            [
                sys.executable,
                str(repo / "manim-math-video" / "scripts" / "tts.py"),
                "--episode",
                str(episode),
                "--provider",
                provider,
                "--voice",
                voice,
                "--force",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"{provider} tts failed ({result.returncode})\n{result.stdout}\n{result.stderr}"
            )
        manifest = json.loads((episode / "voice" / "manifest.json").read_text(encoding="utf-8"))
        return manifest


def run_samples(repo: Path, provider: str, voice: str, port: int) -> None:
    with tempfile.TemporaryDirectory(prefix=f"samples-{provider}-") as temporary:
        out_dir = Path(temporary) / "voice-samples"
        env = dict(os.environ)
        env["MANIM_STUDIO_NO_REEXEC"] = "1"
        env["CARTESIA_API_KEY"] = "test-cartesia"
        env["CARTESIA_API_URL"] = f"http://127.0.0.1:{port}"
        env["ELEVENLABS_API_KEY"] = "test-elevenlabs"
        env["ELEVENLABS_API_URL"] = f"http://127.0.0.1:{port}"
        result = subprocess.run(
            [
                sys.executable,
                str(repo / "manim-math-video" / "scripts" / "voice_samples.py"),
                "--provider",
                provider,
                "--language",
                "en-US",
                "--voices",
                voice,
                "--count",
                "1",
                "--out-dir",
                str(out_dir),
                "--force",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise AssertionError(
                f"{provider} samples failed ({result.returncode}): {result.stdout} {result.stderr}"
            )
        manifest = json.loads((out_dir / "samples.json").read_text(encoding="utf-8"))
        if manifest["provider"] != provider:
            raise AssertionError(f"{provider} sample manifest has the wrong provider")
        sample = Path(manifest["samples"][0]["path"])
        if not sample.is_file():
            raise AssertionError(f"{provider} sample file is missing: {sample}")
        expected_suffix = ".wav" if provider == "cartesia" else ".mp3"
        if sample.suffix != expected_suffix:
            raise AssertionError(f"{provider} sample suffix is {sample.suffix}, expected {expected_suffix}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root",
    )
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    if av is None:
        print("SKIP: PyAV is not available; run this test with the shared environment.")
        return 0

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        cartesia = run_provider(repo, "cartesia", "cartesia-voice", port)
        eleven = run_provider(repo, "elevenlabs", "eleven-voice", port)
        run_samples(repo, "cartesia", "cartesia-voice", port)
        run_samples(repo, "elevenlabs", "eleven-voice", port)
        env = dict(os.environ)
        env["MANIM_STUDIO_NO_REEXEC"] = "1"
        env["CARTESIA_API_KEY"] = "test-cartesia"
        env["CARTESIA_API_URL"] = f"http://127.0.0.1:{port}"
        env["ELEVENLABS_API_KEY"] = "test-elevenlabs"
        env["ELEVENLABS_API_URL"] = f"http://127.0.0.1:{port}"
        for provider, expected in (("cartesia", "cartesia-voice"), ("elevenlabs", "eleven-voice")):
            listed = subprocess.run(
                [
                    sys.executable,
                    str(repo / "manim-math-video" / "scripts" / "tts.py"),
                    "--list-voices",
                    "--provider",
                    provider,
                    "--language",
                    "en-US",
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if listed.returncode != 0 or expected not in listed.stdout:
                raise AssertionError(
                    f"{provider} voice listing failed ({listed.returncode}): "
                    f"{listed.stdout} {listed.stderr}"
                )
    finally:
        server.shutdown()

    if len(Handler.records) != 4:
        raise AssertionError(f"expected 4 API requests, got {len(Handler.records)}")
    cartesia_request, eleven_request = Handler.records[0], Handler.records[1]

    assert cartesia_request["path"] == "/tts/bytes"
    assert cartesia_request["headers"]["authorization"] == "Bearer test-cartesia"
    assert cartesia_request["headers"]["cartesia-version"] == "2026-08-14"
    assert cartesia_request["body"]["model_id"] == "sonic-3.6"
    assert cartesia_request["body"]["voice"] == "cartesia-voice"
    assert cartesia_request["body"]["output_format"]["container"] == "wav"
    assert cartesia_request["body"]["transcript"] == "This is a short provider smoke test."
    assert cartesia["provider"] == "cartesia"
    assert cartesia["model_id"] == "sonic-3.6"

    assert eleven_request["path"].startswith("/v1/text-to-speech/eleven-voice?")
    assert eleven_request["headers"]["xi-api-key"] == "test-elevenlabs"
    assert eleven_request["body"]["model_id"] == "eleven_multilingual_v2"
    assert eleven_request["body"]["text"] == "This is a short provider smoke test."
    assert eleven_request["body"]["voice_settings"]["speed"] == 0.92
    assert eleven["provider"] == "elevenlabs"
    assert eleven["model_id"] == "eleven_multilingual_v2"
    assert eleven["segments"][0]["audio"].endswith(".wav")

    print("ok   Cartesia request, payload, WAV, and manifest")
    print("ok   ElevenLabs request, payload, conversion, and manifest")
    print("ok   Cartesia and ElevenLabs voice listing")
    print("ok   Cartesia and ElevenLabs voice samples")
    return 0


if __name__ == "__main__":
    sys.exit(main())
