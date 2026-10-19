# The brief

`brief.json` is the approved contract for one episode. It is not a scratchpad. Every generated file (theme, storyboard skeleton, voice manifest, render report) can be traced back to it.

A complete brief has four sections: `series`, `episode`, `output`, and `accuracy`. The machine-readable schema is `assets/brief.schema.json`; a filled example is `assets/brief.example.json`.

## Quality presets

| Preset | Resolution | FPS | Approx. relative render time | Use |
|---|---|---|---|---|
| `draft` | 854x480 | 15 | 1x | review, timing, layout |
| `standard` | 1920x1080 | 30 | 6-10x | default final |
| `high` | 1920x1080 | 60 | 12-20x | smooth motion, camera moves |
| `4k` | 3840x2160 | 60 | 30-60x | large displays, archival |

Render time depends heavily on graph complexity, text, and caching. A 7-minute episode with simple graphs may render in 5-15 minutes at `standard` on a modern laptop; a 4K render with many transforms can take hours. Always render `draft` first.

## Aspect ratios

`16:9` is the default and the best-tested layout. The runtime also supports `9:16`, `1:1`, and `4:3` with automatic frame sizing; `render.py` swaps the output dimensions accordingly. Vertical layouts stack the two `compare` columns. Review a `draft` contact sheet for overflow, caption fit, and graph scale before committing to a vertical series.

| Ratio | Standard render | Use |
|---|---|---|
| `16:9` | 1920x1080 | YouTube, lectures, desktop |
| `9:16` | 1080x1920 | Shorts, Reels, TikTok |
| `1:1` | 1080x1080 | Square social posts |
| `4:3` | 1440x1080 | Classroom projectors, archival |

## `series`

```json
"series": {
  "title": "Path of Knowledge",
  "slug": "path-of-knowledge",
  "season": 1,
  "episode_number": 1,
  "template": "clean-light",
  "premise": "One mathematical idea per episode, built from a question to a visual proof.",
  "audience": "Curious adults and first-year university students.",
  "visual_motif": "A thin accent line becomes the graph, the proof, or the path.",
  "consistency_note": null
}
```

- `slug` is lowercase, hyphenated, and stable. It is used in file names.
- `episode_number` is an integer. Output names are zero-padded to three digits.
- `template` must match a file in `assets/templates/`.
- `premise` and `visual_motif` are series-level, not episode-level.
- `consistency_note` records an approved exception to the series lock.

## `episode`

```json
"episode": {
  "title": "Why the derivative of x² is 2x",
  "slug": "why-derivative-x-squared",
  "thesis": "The derivative is the limit of secant slopes, and that limit turns the geometry of x² into the algebra of 2x.",
  "question": "Why does the slope of x² at x equal 2x, rather than something that depends on h?",
  "audience": "First-year calculus students who know functions and slopes but are shaky on limits.",
  "prerequisites": ["functions", "slope of a line", "informal limits"],
  "goals": [
    "Explain the derivative as a limit of secant slopes.",
    "Derive 2x for x² from the limit definition.",
    "Recognize the cancellation step as the crux."
  ],
  "rigor": "sketch",
  "tone": "curious, precise, unhurried",
  "target_duration_seconds": 420,
  "platform": "youtube",
  "aspect_ratio": "16:9",
  "key_points": [
    "A secant slope is an average rate.",
    "The limit turns average into instantaneous.",
    "The h cancels before h reaches zero."
  ],
  "misconceptions": [
    "The derivative is just a formula to memorize.",
    "Setting h to zero is allowed before cancelling.",
    "The tangent is the secant at a single point."
  ],
  "visuals": [
    "Secant line closing onto a tangent as h shrinks.",
    "The rise/run triangle with h and f(x+h)-f(x) labeled.",
    "The graph of x² with the tangent slope at x = 1."
  ],
  "next_teaser": "What happens when the function is not a parabola?",
  "previous_recap": null
}
```

- `thesis` is one sentence. If it needs two, the episode is not scoped.
- `rigor` accepts `intuition`, `sketch`, `proof`, or `derivation`.
- `target_duration_seconds` is a target, not a hard cut. Aim within 15%.
- `platform` is descriptive; it does not change rendering except through `aspect_ratio`.
- `key_points` are the 3-7 claims of the argument, in order.
- `misconceptions` should be stated as the audience's belief, then corrected in the episode.
- `visuals` are candidates; the storyboard chooses the ones that carry the argument.

## `output`

```json
"output": {
  "quality": "standard",
  "language": "en-US",
  "subtitle_language": "en",
  "captions": true,
  "latex_fallback": false,
  "music": null,
  "music_gain_db": -24,
  "voice": {
    "provider": "edge",
    "id": "en-US-AvaMultilingualNeural",
    "style": "warm-teacher",
    "rate": "-3%",
    "pitch": "+0Hz",
    "volume": "+0%",
    "command": null,
    "piper_model": null
  }
}
```

- `language` is the narration locale. Use a full locale when possible.
- `subtitle_language` is the caption locale. It may differ from `language`.
- `latex_fallback` should be `false` for final work. If `true`, equation beats render as Unicode approximations and a warning is emitted. Use only for silent drafts.
- `music` is an optional path relative to the episode directory. `music_gain_db` is negative dB under narration.
- `voice.provider` accepts `edge`, `piper`, `custom`, or `none`.
- `voice.command` is required for `custom`; `voice.piper_model` is required for `piper`.
- `rate`, `pitch`, and `volume` use edge-tts syntax (`+0%`, `-3%`, `+2Hz`). For other providers, they are passed through if supported.

## `accuracy`

```json
"accuracy": {
  "notation": [
    "Use f'(x) for the derivative; do not mix Leibniz and Newton notation in one derivation.",
    "Use \\mathbb{R} for the domain unless a restriction is stated."
  ],
  "conventions": "Angles in radians. Decimal point, not comma.",
  "pronunciations": {
    "Euler": "OY-ler",
    "Riemann": "REE-mahn"
  },
  "sources": [
    "Stewart, Calculus, chapter 2 (for the limit definition)"
  ],
  "claims_to_verify": [
    "The cancellation is valid for h ≠ 0.",
    "The limit of 2x + h is 2x."
  ],
  "reviewed_by": null
}
```

- `notation` is a list of rules the storyboard must follow.
- `conventions` records units, angle measure, decimal separator, and vector convention.
- `pronunciations` maps written terms to spoken respellings.
- `sources` are real references only. If a claim has no source, list it under `claims_to_verify`.
- `reviewed_by` can be a person or process. Leave `null` until verified.

## Defaults

If the user has no preference:

| Field | Default |
|---|---|
| `output.quality` | `standard` |
| `output.language` | series language, else `en-US` |
| `output.voice.style` | `warm-teacher` |
| `output.voice.id` | default voice for the locale |
| `output.captions` | `true` |
| `output.latex_fallback` | `false` |
| `series.template` | `clean-light` |
| `episode.rigor` | `sketch` |
| `episode.target_duration_seconds` | 420 |
| `episode.aspect_ratio` | `16:9` |

State the defaults you used in the confirmation block. Never hide them.

## Validation

```bash
python scripts/validate.py --brief path/to/brief.json
```

The validator checks required fields, template existence, quality, locale/voice compatibility, aspect ratio, duration, and suspicious values (for example, a 30-second target for a full proof). It does not judge the mathematics; that is the agent's job.

## Example

See `assets/brief.example.json` for a complete, valid brief that can be used with the demo storyboard.
