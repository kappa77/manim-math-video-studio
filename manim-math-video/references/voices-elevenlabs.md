# ElevenLabs voice selection

Read this file when `output.voice.provider` is `elevenlabs`. The general voice gate is in
[voices.md](voices.md).

## Requirements

- `ELEVENLABS_API_KEY` must be set in the environment. Get a key at
  <https://elevenlabs.io/app/settings/api-keys>. Never put it in `brief.json`.
- The key needs `text_to_speech` to generate audio and `voices_read` to list voices.
  A key without `voices_read` can still synthesize if you already know the voice id.
- **Plan and voice access.** Free API users cannot use library/premade voices via the
  API. A voice may also require Creator tier or above. Use a voice owned by your
  account (`Access: own` in the list), or upgrade the plan.
- The voice must be an ElevenLabs **voice id** (for example
  `Ilze0lNihfxGj7pq9g7s`), not a display name or a label.
- The adapter defaults to `eleven_multilingual_v2` and requests MP3, converted to WAV
  with PyAV or ffmpeg.
- The locale controls pronunciation through the model and the text; the adapter does
  not send `language_code` because multilingual v2 does not support it.

## Criteria

Choose a voice only after checking all of these:

1. **Access.** Prefer `Access: own`. `library` voices require a paid plan and produce
   `402 paid_plan_required` on free accounts.
2. **Plan tier.** Some owned or library voices produce
   `400 You need to be on the creator tier or above`. Use another voice or upgrade.
3. **Language.** Prefer a voice whose `Languages` column includes `it` for Italian
   narration. An English voice can pronounce Italian through the multilingual model,
   but the accent may be wrong; listen to a sample.
4. **Use case.** Match the description to the video: educator, warm storyteller,
   broadcaster. Listen before deciding.
5. **Series consistency.** Keep the same voice id across the series; record any change.
6. **Explicit choice.** Generate the same 18–25 word sentence in every candidate and
   wait for the user to name a number or id. A label is not a selection.
7. **Speed.** `rate` maps to `voice_settings.speed` (0.7–1.2). `pitch` and `volume` are
   not supported by this adapter; use the voice characteristics or provider settings.

## Workflow

```bash
# List voices with access, languages, and style
python scripts/tts.py --list-voices --provider elevenlabs --language it-IT

# Generate comparable samples with an id from your account
python scripts/voice_samples.py \
  --provider elevenlabs --language it-IT --style warm-teacher \
  --voices <voice-id-1>,<voice-id-2> --count 2 \
  --text "Cinque stipendi, uno molto più alto: la media sale subito, la mediana resta il valore di mezzo."
```

Record the explicit choice in `brief.json`:

```json
"voice": {
  "provider": "elevenlabs",
  "id": "<voice-id>",
  "model_id": "eleven_multilingual_v2",
  "style": "warm-teacher",
  "rate": "-3%",
  "pitch": "+0Hz",
  "volume": "+0%"
},
"voice_selection": {
  "status": "confirmed",
  "voice_id": "<voice-id>",
  "user_choice": "voice id provided by user",
  "sample_paths": []
}
```

Optional provider overrides:

```json
"voice_settings": {
  "stability": 0.5,
  "similarity_boost": 0.75,
  "style": 0.0,
  "use_speaker_boost": true
}
```

Install/update/repair default:

```bash
python install.py --tts-provider elevenlabs --tts-voice <voice-id>
```

Only the provider, model, and voice id are stored in
`~/.manim-math-video/tts.json`; the key stays in the environment.

## Errors

| Response | Meaning | Action |
|---|---|---|
| `401 missing_permissions voices_read` | Key cannot list voices | Enable `voices_read` on the key, or pass an existing voice id directly |
| `402 paid_plan_required: Free users cannot use library voices` | Voice is library/premade and the plan is free | Use a voice owned by the account, or upgrade |
| `400 You need to be on the creator tier or above` | The selected voice needs Creator+ | Choose another voice or upgrade |
| `404` | Voice id not found in this account | Re-list voices; check workspace and key |
| `422` | Invalid model or voice settings | Use `eleven_multilingual_v2` and supported `voice_settings` |

`check_env.py` shows ElevenLabs as `ok` when the key is visible and `optional` otherwise.
A visible key does **not** guarantee that the account may use a particular voice.
