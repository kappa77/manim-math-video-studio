# Series consistency

A series is more than a folder of videos. It is a promise: the same voice, the same visual grammar, the same notation, and the same kind of question. `series.json` is the machine-readable promise.

## Directory layout

```text
series/
  series.json
  episodes/
    001-why-derivative-x-squared/
      brief.json
      storyboard.json
      script.md
      episode.py
      theme.json
      manim_lib/
      voice/
      output/
      qa/
    002-what-happens-when-the-function-is-not-a-parabola/
```

`new_episode.py` creates this structure. The series root can be anywhere; pass it with `--series-dir`.

## `series.json`

```json
{
  "schema_version": 1,
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z",
  "series": {
    "title": "Path of Knowledge",
    "slug": "path-of-knowledge",
    "season": 1,
    "premise": "One mathematical idea per episode, built from a question to a visual proof.",
    "audience": "Curious adults and first-year university students.",
    "visual_motif": "A thin accent line becomes the graph, the proof, or the path.",
    "template": "clean-light",
    "template_version": "1.0.0"
  },
  "defaults": {
    "quality": "standard",
    "language": "en-US",
    "voice": {
      "provider": "edge",
      "id": "en-US-AvaMultilingualNeural",
      "style": "warm-teacher",
      "rate": "-3%",
      "pitch": "+0Hz",
      "volume": "+0%"
    }
  },
  "episodes": [
    {
      "id": "s01e001",
      "season": 1,
      "number": 1,
      "title": "Why the derivative of x² is 2x",
      "slug": "why-derivative-x-squared",
      "path": "episodes/001-why-derivative-x-squared",
      "template": "clean-light",
      "quality": "standard",
      "language": "en-US",
      "voice": "en-US-AvaMultilingualNeural",
      "status": "published",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
```

### Fields

| Field | Purpose |
|---|---|
| `series.premise` | The one-line promise of the whole series. |
| `series.visual_motif` | The recurring visual device. |
| `series.template` | Locked visual/narrative template id. |
| `series.template_version` | The version at the time the series started. |
| `defaults.quality` | Final render quality for the series. |
| `defaults.language` | Narration locale for the series. |
| `defaults.voice` | Narrator identity, rate, pitch, volume. |
| `episodes[].status` | `planned`, `draft`, `review`, `published`, `archived`. |
| `episodes[].path` | Relative to the series root, forward slashes. |
| `changes[]` | Optional audit log of approved style-drift events (`at`, `episode`, `reason`, `mismatches`). |

## Consistency rules

1. **One narrator per series.** A guest voice needs a format reason and a note in the episode brief.
2. **One locale per series.** Regional accents are part of the identity. Do not switch `en-US` to `en-GB` for convenience.
3. **One final quality per series.** Drafts may vary; published files should share resolution and fps.
4. **One template per series.** If the visual language must change, create `template-v2` and document the transition. Do not edit the old template in place.
5. **One title grammar.** Pick a pattern and keep it. Examples:
   - "Why <claim>?"
   - "<Object> is <surprise>"
   - "The <concept> behind <phenomenon>"
   - "What <assumption> buys you"
6. **One narrative rhythm.** Reuse a progression suited to the series: explanation, chronology, procedure, analysis, or story. Formalization and misconceptions belong only where relevant.
7. **One notation glossary.** Keep symbols, units, and spoken forms in `series.json` or a `glossary.json`.
8. **One episode id scheme.** `s<season two digits>e<episode three digits>`, zero-padded, never reused.
9. **One recap/outro contract.** Each episode recaps the chain and asks the next question.
10. **One color semantics.** Primary = object of study; secondary = comparison; danger = misconception; success = conclusion.

## Adding an episode

1. Read `series.json`.
2. Interview for the **episode-specific** content only: title, central question or promise, progression, visual approach, optional misconception, next hook.
3. Reuse the locked template, quality, language, title grammar, and rhythm. Before production, offer the saved voice with a short playable sample and ask the user to keep it for this episode or request alternatives, following `voices.md`. A prior explicit choice for this episode already satisfies this step; a saved default alone does not.
4. Create `brief.json` with the same series metadata and increment `episode_number`.
5. Run `new_episode.py`. It refuses a style drift unless `--allow-style-drift "reason"` is passed.
6. After approval, change the registry status from `draft` to `published` and add the output path.

## Deliberate change

Sometimes a series must evolve: a new season, a new visual identity, a new narrator. Treat that as a new series or a versioned template.

- **New season, same look:** increment `season`, keep the template id, reset the episode numbering to 001. Record the season theme in `series.json`.
- **New look:** create `assets/templates/<id>-v2.json` with a new id and version, update `series.template`, and note the transition episode in the registry.
- **New narrator:** record a `voice_change` event with the episode id and reason. Do not silently replace the voice.
- **New language:** create a separate series for each locale. Dubbing an existing series is a localization project, not an episode tweak.

## Continuity checklist

Before publishing an episode:

- [ ] Recap of the previous episode, if the series is serialized.
- [ ] Next-episode hook that is a real question, not a generic "stay tuned".
- [ ] Same title card grammar.
- [ ] Same narrator, rate, pitch, and pronunciation glossary.
- [ ] Same template and graph palette.
- [ ] Same notation and units.
- [ ] Episode number in the title card and file name.
- [ ] Registry updated with status, duration, and output path.
- [ ] Previous episode still renders with its own theme snapshot (no catalog drift).

## Migration

The episode's `theme.json` is a snapshot. If the catalog template changes, old episodes keep their look. To migrate an episode:

1. Copy the new template into the episode as `theme.json`.
2. Render a draft.
3. Compare the contact sheets side by side.
4. Update the episode's brief and registry `template_version`.
5. Re-render and re-QA.

Never migrate a published episode without a reason and a new output version.
