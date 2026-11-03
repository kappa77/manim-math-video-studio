"""Native Cartesia and ElevenLabs adapters for the narration pipeline.

The installer and tts.py keep the standard library only; these providers use
urllib and are disabled unless the corresponding API key is present.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from _common import load_voices, provider_info

_REFERENCE_HINTS = {
    "cartesia": {
        "401": "Check CARTESIA_API_KEY and its Cartesia-Version; see references/voices-cartesia.md.",
        "403": "The Cartesia key cannot use this voice; see references/voices-cartesia.md.",
        "422": "Check the Cartesia voice id, model, and generation config; see references/voices-cartesia.md.",
    },
    "elevenlabs": {
        "401": "The key needs text_to_speech; enable voices_read to list voices; see references/voices-elevenlabs.md.",
        "402": "Free plans cannot use library voices via the API; create a Voice Design voice in My Voices or upgrade; see references/voices-elevenlabs.md.",
        "400": "This voice may require Creator tier or another plan; see references/voices-elevenlabs.md.",
        "404": "The ElevenLabs voice id was not found; see references/voices-elevenlabs.md.",
    },
}


def _with_hint(provider: str, message: str) -> str:
    match = re.search(r"\((\d{3})\)", message)
    hint = _REFERENCE_HINTS.get(provider, {}).get(match.group(1)) if match else None
    return message + "\n" + hint if hint else message


def _parse_percent(value: str) -> float:
    match = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*%\s*$", str(value or ""))
    return float(match.group(1)) if match else 0.0


def _percent_multiplier(value: str, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, 1.0 + _parse_percent(value) / 100.0))


def api_url(provider: str, voices: dict[str, Any] | None = None) -> str:
    info = provider_info(provider, voices)
    env_name = f"{provider.upper()}_API_URL"
    return str(os.environ.get(env_name) or info.get("api_url") or "").rstrip("/")


def api_key(provider: str, voices: dict[str, Any] | None = None) -> str:
    info = provider_info(provider, voices)
    env_name = str(info.get("api_key_env") or "")
    value = os.environ.get(env_name, "").strip() if env_name else ""
    if not value:
        label = info.get("label", provider)
        keys_url = info.get("keys_url", "")
        raise RuntimeError(
            f"{label} requires {env_name}. Set it in the environment"
            + (f" (get a key at {keys_url})" if keys_url else "")
            + "."
        )
    return value


def _request(
    url: str,
    *,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 120,
) -> bytes:
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers or {},
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace").strip()
        raise RuntimeError(f"TTS request failed ({exc.code}): {body[:700]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"TTS request failed: {exc.reason}") from exc


def _post_json(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    timeout: float = 120,
) -> bytes:
    return _request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"},
        timeout=timeout,
    )


def _get_json(
    url: str,
    headers: dict[str, str],
    *,
    timeout: float = 60,
) -> dict[str, Any]:
    raw = _request(url, headers=headers, timeout=timeout)
    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - surface a useful API error
        raise RuntimeError(f"TTS voice list returned invalid JSON: {exc}") from exc
    return data if isinstance(data, dict) else {}


def provider_model(
    provider: str,
    voice_cfg: dict[str, Any],
    config: dict[str, Any],
    voices: dict[str, Any] | None = None,
) -> str:
    stored = config.get("providers", {})
    stored = stored.get(provider, {}) if isinstance(stored, dict) else {}
    return str(
        voice_cfg.get("model_id")
        or (stored.get("model_id") if isinstance(stored, dict) else None)
        or provider_info(provider, voices).get("default_model")
        or ""
    )


def provider_api_version(
    provider: str,
    voice_cfg: dict[str, Any],
    config: dict[str, Any],
    voices: dict[str, Any] | None = None,
) -> str:
    stored = config.get("providers", {})
    stored = stored.get(provider, {}) if isinstance(stored, dict) else {}
    return str(
        voice_cfg.get("api_version")
        or (stored.get("api_version") if isinstance(stored, dict) else None)
        or provider_info(provider, voices).get("api_version")
        or ""
    )


def elevenlabs_settings(voice_cfg: dict[str, Any], rate: str) -> dict[str, Any]:
    settings: dict[str, Any] = {
        "stability": 0.5,
        "similarity_boost": 0.75,
        "style": 0.0,
        "use_speaker_boost": True,
        "speed": _percent_multiplier(rate, 0.7, 1.2),
    }
    override = voice_cfg.get("voice_settings")
    if isinstance(override, dict):
        settings.update(override)
    settings["speed"] = _percent_multiplier(rate, 0.7, 1.2)
    return settings


def cartesia_config(voice_cfg: dict[str, Any], rate: str, volume: str) -> dict[str, Any]:
    config: dict[str, Any] = {
        "speed": _percent_multiplier(rate, 0.6, 1.5),
        "volume": _percent_multiplier(volume, 0.5, 2.0),
    }
    emotion = voice_cfg.get("emotion")
    if emotion:
        config["emotion"] = str(emotion)
    override = voice_cfg.get("generation_config")
    if isinstance(override, dict):
        config.update(override)
    return config


def cartesia_payload(
    text: str,
    voice: str,
    language: str,
    model_id: str,
    generation_config: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model_id": model_id,
        "transcript": text,
        "voice": voice,
        "output_format": {
            "container": "wav",
            "encoding": "pcm_s16le",
            "sample_rate": 44100,
        },
        "generation_config": generation_config,
    }
    if language:
        payload["language"] = language
    return payload


def elevenlabs_payload(
    text: str,
    model_id: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    return {
        "text": text,
        "model_id": model_id,
        "voice_settings": settings,
    }


def cartesia_generate(
    text: str,
    voice: str,
    language: str,
    rate: str,
    volume: str,
    out_wav: Path,
    *,
    voice_cfg: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    voices: dict[str, Any] | None = None,
) -> None:
    voice_cfg = voice_cfg or {}
    config = config or {}
    voices = voices or load_voices()
    key = api_key("cartesia", voices)
    model_id = provider_model("cartesia", voice_cfg, config, voices)
    api_version = provider_api_version("cartesia", voice_cfg, config, voices)
    generation_config = cartesia_config(voice_cfg, rate, volume)
    payload = cartesia_payload(text, voice, language, model_id, generation_config)
    try:
        raw = _post_json(
            f"{api_url('cartesia', voices)}/tts/bytes",
            payload,
            {
                "Authorization": f"Bearer {key}",
                "Cartesia-Version": api_version,
            },
        )
    except RuntimeError as exc:
        raise RuntimeError(_with_hint("cartesia", str(exc))) from exc
    out_wav.write_bytes(raw)


def elevenlabs_generate(
    text: str,
    voice: str,
    language: str,
    rate: str,
    out_mp3: Path,
    *,
    voice_cfg: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
    voices: dict[str, Any] | None = None,
) -> None:
    voice_cfg = voice_cfg or {}
    config = config or {}
    voices = voices or load_voices()
    key = api_key("elevenlabs", voices)
    model_id = provider_model("elevenlabs", voice_cfg, config, voices)
    payload = elevenlabs_payload(text, model_id, elevenlabs_settings(voice_cfg, rate))
    url = (
        f"{api_url('elevenlabs', voices)}/v1/text-to-speech/"
        f"{urllib.parse.quote(voice, safe='')}?output_format=mp3_44100_128"
    )
    try:
        raw = _post_json(
            url,
            payload,
            {
                "xi-api-key": key,
                "Accept": "audio/mpeg",
            },
        )
    except RuntimeError as exc:
        raise RuntimeError(_with_hint("elevenlabs", str(exc))) from exc
    out_mp3.write_bytes(raw)


def provider_voice_entries(
    provider: str,
    language: str,
    voices: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Return selectable voices for a provider; edge uses the curated catalog."""
    voices = voices or load_voices()
    if provider == "edge":
        from _common import voice_entries

        return voice_entries(language, voices)
    if provider == "cartesia":
        key = api_key("cartesia", voices)
        headers = {
            "Authorization": f"Bearer {key}",
            "Cartesia-Version": provider_api_version("cartesia", {}, {}, voices),
        }
        query = {"limit": 100}
        if language:
            query["language"] = language
        data = _get_json(
            f"{api_url('cartesia', voices)}/voices?{urllib.parse.urlencode(query)}",
            headers,
        )
        rows = data.get("data", [])
        if not rows and language:
            data = _get_json(f"{api_url('cartesia', voices)}/voices?limit=100", headers)
            rows = data.get("data", [])
        return [
            {
                "id": str(item.get("id", "")),
                "label": str(item.get("name") or item.get("id") or ""),
                "gender": str(item.get("gender") or ""),
                "style": str(item.get("tagline") or item.get("description") or ""),
                "best_for": [],
                "languages": sorted(
                    {
                        str(accent.get("locale"))
                        for accent in (item.get("accents") or [])
                        if accent.get("locale")
                    }
                ),
                "access": "own" if item.get("is_owner") else str(item.get("access") or ""),
                "category": "cartesia",
            }
            for item in rows
            if item.get("id")
        ]
    if provider == "elevenlabs":
        key = api_key("elevenlabs", voices)
        data = _get_json(
            f"{api_url('elevenlabs', voices)}/v2/voices?page_size=100",
            {"xi-api-key": key, "Accept": "application/json"},
        )
        rows = data.get("voices", [])
        return [
            {
                "id": str(item.get("voice_id", "")),
                "label": str(item.get("name") or item.get("voice_id") or ""),
                "gender": str((item.get("labels") or {}).get("gender", "")),
                "style": str(
                    item.get("description")
                    or (item.get("labels") or {}).get("description")
                    or (item.get("labels") or {}).get("use_case", "")
                ),
                "best_for": [],
                "languages": sorted(
                    {
                        str(lang.get("language"))
                        for lang in (item.get("verified_languages") or [])
                        if lang.get("language")
                    }
                ),
                "access": "own" if item.get("is_owner") else "library",
                "category": str(item.get("category") or ""),
            }
            for item in rows
            if item.get("voice_id")
        ]
    raise RuntimeError(f"Voice listing is not available for provider {provider!r}.")
