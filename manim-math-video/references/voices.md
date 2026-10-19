# Voice, language, and pronunciation

The voice is part of the series identity. Choose it once, record it, and reuse it. The default provider is **edge-tts** because it is free, has broad language coverage, and returns word boundaries for captions. The pipeline can also use a custom command (ElevenLabs, OpenAI TTS, Piper, a local model) or run silently for timing drafts.

## Selection order

1. Ask for the **narration language and locale** (for example `en-US`, `it-IT`, `es-MX`).
2. Ask for the **delivery style** (`warm-teacher`, `calm-documentary`, `energetic-explainer`, `authoritative-lecturer`, `friendly-conversational`).
3. Pick the default voice for that locale and style from `assets/voices.json`, or let the user name a voice.
4. Confirm **rate** and **pitch**. Start with the style defaults; adjust only if the sample sounds wrong.
5. Record all of it in `brief.json`:

```json
"output": {
  "language": "en-US",
  "subtitle_language": "en",
  "voice": {
    "provider": "edge",
    "id": "en-US-AvaMultilingualNeural",
    "style": "warm-teacher",
    "rate": "-3%",
    "pitch": "+0Hz",
    "volume": "+0%"
  }
}
```

## Curated default voices

| Locale | Default voice | Character |
|---|---|---|
| `en-US` | `en-US-AvaMultilingualNeural` | warm, clear, expressive |
| `en-GB` | `en-GB-SoniaNeural` | measured, documentary |
| `it-IT` | `it-IT-ElsaNeural` | warm, teacherly |
| `es-ES` | `es-ES-ElviraNeural` | warm, clear |
| `es-MX` | `es-MX-DaliaNeural` | warm, conversational |
| `fr-FR` | `fr-FR-DeniseNeural` | elegant, clear |
| `de-DE` | `de-DE-KatjaNeural` | clear, precise |
| `pt-BR` | `pt-BR-FranciscaNeural` | warm, friendly |
| `pt-PT` | `pt-PT-RaquelNeural` | clear, teaching |
| `nl-NL` | `nl-NL-FennaNeural` | clear, natural |
| `pl-PL` | `pl-PL-ZofiaNeural` | warm, teaching |
| `ru-RU` | `ru-RU-SvetlanaNeural` | warm, teacherly |
| `uk-UA` | `uk-UA-PolinaNeural` | warm, teaching |
| `tr-TR` | `tr-TR-EmelNeural` | warm, teaching |
| `ar-SA` | `ar-SA-ZariyahNeural` | warm, formal |
| `hi-IN` | `hi-IN-SwaraNeural` | warm, teaching |
| `zh-CN` | `zh-CN-XiaoxiaoNeural` | warm, natural |
| `ja-JP` | `ja-JP-NanamiNeural` | warm, natural |
| `ko-KR` | `ko-KR-SunHiNeural` | warm, teaching |

The full catalog is `assets/voices.json`. Any valid edge-tts voice id is accepted even if it is not listed, but the curated list is what the agent should offer.

## Style presets

| Style | Rate | Pitch | Use |
|---|---|---|---|
| `warm-teacher` | `-3%` | `+0Hz` | classroom, general audience |
| `calm-documentary` | `-8%` | `-2Hz` | long-form, history, essays |
| `energetic-explainer` | `+8%` | `+2Hz` | shorts, young audience |
| `authoritative-lecturer` | `-5%` | `-3Hz` | proofs, technical material |
| `friendly-conversational` | `+3%` | `+0Hz` | podcast-style, informal |

Do not stack rate changes. If the user asks for a slower voice, use `-5%` to `-10%`, not `-3%` plus a global slowdown. Very slow TTS sounds unnatural; shorten the script instead.

## Language handling

- The locale controls the voice, spelling, and default captions.
- On-screen mathematical notation usually stays international. Confirm local conventions: decimal comma, `\operatorname{tg}` vs `\tan`, `\mathrm{sen}` vs `\sin`, vector notation, interval notation.
- If captions are translated into another language, add a `caption` field to each beat. The `narration` and `speech` fields remain in the spoken language.
- Right-to-left scripts (Arabic, Hebrew) are supported by Pango but should be checked in a draft: line order, punctuation, and mixed math/LTR text can be wrong. Keep equations in separate mobjects.
- CJK line breaking needs a font with CJK coverage. The default templates fall back to system fonts; check the contact sheet. If the text renders as boxes, install Noto Sans CJK or set a CJK font explicitly in the episode's `theme.json`.

## Pronunciation

TTS will mispronounce some names, symbols, and abbreviations. Fix them in this order:

1. **Write a `speech` form for the beat.** This is the cleanest fix.

   ```json
   {
     "id": "euler",
     "narration": "Euler's identity connects five constants.",
     "speech": "OY-ler's identity connects five constants."
   }
   ```

2. **Add a pronunciation mapping** in `brief.json` for a repeated term:

   ```json
   "accuracy": {
     "pronunciations": {
       "Euler": "OY-ler",
       "Weierstrass": "VY-er-strahs",
       "Riemann": "REE-mahn",
       "Lebesgue": "luh-BEG",
       "Cauchy": "ko-SHEE",
       "measure": "MEH-zhur"
     }
   }
   ```

3. **Rewrite the sentence** to avoid an ambiguous symbol. For example, say "the absolute value of x" instead of "mod x" if the voice reads "mod" as a word.

4. **Use a custom provider** if the term is central and edge-tts cannot produce it acceptably.

Do not use SSML phoneme tags with edge-tts; the service accepts plain text. Do not insert hyphens into ordinary words to force pronunciation; it damages prosody. Use phonetic respelling only for the troublesome name.

## Math narration rules

- Read formulas as mathematics, not as punctuation: "f prime of x", "the integral from zero to one", "x squared", "the limit as h approaches zero".
- Use `speech` for formulas and symbols; keep the display caption readable.
- Avoid reading long expressions symbol by symbol. State the meaning, then the formula.
- Numbers: say "one half", not "one slash two"; say "zero point five" or "one half" depending on context.
- Units: say "meters per second", not "m slash s".
- Avoid "times" for the multiplication sign when it is ambiguous; say "two x" or "two times x" consistently.
- For a series, keep a glossary of spoken forms in `series.json`.

## Captions

- Captions are generated from the narration by Manim's `add_subcaption`, split at `captions.max_chars` from the template.
- Use `caption` when the written form should differ from the spoken form, for example a translated subtitle or a cleaner version of a formula.
- Keep captions under two lines at 1080p. The default 84 characters is a good starting point.
- Math in captions should be Unicode or plain words. SRT is not LaTeX.
- Check the SRT in a player before publishing. Manim writes it next to the MP4.

## Audio levels

- Edge TTS segments are normalized consistently. Do not apply per-segment gain unless a segment is clearly off.
- Background music, if used, should sit at roughly `-22 dB` to `-28 dB` under narration. Manim's `add_sound(..., gain=...)` accepts a gain in dB. Choose a track that is at least as long as the episode; Manim does not loop music.
- Leave `captions.tail_pad` (default 0.15 s) after each narration segment. It prevents clipped final consonants and gives the edit room to breathe.
- If the final audio is too quiet or too loud, normalize the whole program after rendering; do not normalize each segment differently.

## Custom providers

Set `output.voice.provider` to `custom` and provide a command template. The script writes the spoken text to `{text_file}` and expects audio at `{out_file}`.

```json
"voice": {
  "provider": "custom",
  "id": "elevenlabs-rachel",
  "command": [
    "python", "my_tts.py",
    "--text-file", "{text_file}",
    "--out", "{out_file}",
    "--voice", "{voice}",
    "--language", "{language}"
  ],
  "rate": "+0%",
  "pitch": "+0Hz"
}
```

Placeholders: `{text_file}`, `{out_file}`, `{voice}`, `{language}`, `{rate}`, `{pitch}`, `{volume}`. The command is run without a shell. If the provider outputs MP3, the pipeline converts it to WAV with PyAV or ffmpeg.

### Piper (offline)

```bash
python scripts/tts.py --episode <episode> \
  --provider piper \
  --piper-model /path/to/en_US-lessac-medium.onnx
```

Piper writes a WAV directly. It is fast and offline, but voice quality and language coverage vary. Use it when privacy or offline operation matters more than polish.

### OpenAI / ElevenLabs / Azure

Use the custom command adapter or write a small wrapper that accepts the placeholders above. Keep API keys in environment variables, never in `brief.json` or the storyboard. The skill does not store secrets.

## Sanity checks

Before accepting a voice track:

- Listen to the first, middle, and last segment.
- Check every proper name and every formula read aloud.
- Check that the pace leaves room for the visual. If a beat is too dense, cut words, not animation time.
- Check that the total duration is within 15% of the target.
- Check that the loudest segment is not clipping and the quietest is audible.
- Check captions against the audio, especially numbers and symbols.
- For a series, compare against the previous episode: same voice, same rate, same pronunciation glossary.
