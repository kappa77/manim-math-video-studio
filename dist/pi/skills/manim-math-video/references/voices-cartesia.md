# Cartesia voice selection

Read this file when `output.voice.provider` is `cartesia`. The general voice gate is in
[voices.md](voices.md).

## Requirements

- `CARTESIA_API_KEY` must be set in the environment (it starts with `sk_car_`).
  Get a key at <https://play.cartesia.ai/keys>. Never put it in `brief.json`.
- Network access to `https://api.cartesia.ai`.
- The adapter sends `Cartesia-Version: 2026-08-14` and defaults to model `sonic-3.6`.
- The voice must be a Cartesia **voice id** (a UUID such as
  `ee16f140-f6dc-490e-a1ed-c1d537ea0086`), not a display name.
- The locale must be a Cartesia language or locale code (`it`, `it-IT`, `en-US`, ...).
  A voice can be native in one accent and speak other languages with that accent.
- PyAV or ffmpeg is required for duration/audio checks. With PyAV, the streaming WAV
  header Cartesia returns is read correctly (fixed in 0.5.1).

## Criteria

Choose a voice that satisfies all of these:

1. **Language.** List voices for the narration locale and prefer a voice whose
   `Languages` column contains that locale. Do not use an English-only voice for
   Italian narration just because its name sounds Italian.
2. **Access.** `Access: own` means your organization owns the voice. `public` voices
   are usable when the API key is allowed to use them; a `403` means it is not.
3. **Use case.** Match the style tagline to the video: teacherly for explainers,
   measured for documentary, energetic for shorts. Listen before deciding.
4. **Series consistency.** Use the same voice id for every episode of a series.
   Changing it requires an explicit decision and a recorded reason.
5. **Sample.** Generate the same 18–25 word sentence in every candidate and get an
   explicit choice from the user. A label is not a selection.
6. **Rate and volume.** `rate` maps to Cartesia `speed` (0.6–1.5) and `volume` to
   Cartesia `volume` (0.5–2.0). `pitch` is not supported by this adapter.

## Workflow

```bash
# List Italian voices with access and languages
python scripts/tts.py --list-voices --provider cartesia --language it-IT

# Generate comparable Italian samples (use ids from the list)
python scripts/voice_samples.py \
  --provider cartesia --language it-IT --style warm-teacher \
  --voices <id-1>,<id-2>,<id-3> --count 3 \
  --text "Cinque stipendi, uno molto più alto: la media sale subito, la mediana resta il valore di mezzo."
```

Record the explicit choice in `brief.json`:

```json
"voice": {
  "provider": "cartesia",
  "id": "<voice-id>",
  "model_id": "sonic-3.6",
  "style": "warm-teacher",
  "rate": "-3%",
  "pitch": "+0Hz",
  "volume": "+0%"
},
"voice_selection": {
  "status": "confirmed",
  "voice_id": "<voice-id>",
  "user_choice": "sample 4 — Lorenzo",
  "sample_paths": ["voice-samples/04-lorenzo.wav"]
}
```

For install/update/repair, set a default voice without putting the key anywhere:

```bash
python install.py --tts-provider cartesia --tts-model sonic-3.6 --tts-voice <voice-id>
```

The installer writes only the provider, model, and voice id to
`~/.manim-math-video/tts.json`. The conversation can override it per episode.

## Errors

| Response | Meaning | Action |
|---|---|---|
| `401` / `403` | Key missing, invalid, or not allowed for the voice | Check `CARTESIA_API_KEY`; use a voice your key can access |
| `422` | Unsupported voice id, model, language, or generation config | Re-list voices; validate `model_id` and locale |
| Duration looks enormous | Streaming WAV header from an older release | Upgrade to 0.5.1+ or use the current adapter |

`check_env.py` shows Cartesia as `ok` when the key is visible and `optional` otherwise.
