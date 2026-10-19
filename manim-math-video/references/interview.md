# The argument interview

The goal is not to collect a topic. It is to reconstruct the argument the viewer will follow, then choose the smallest visual evidence that makes that argument feel inevitable.

Ask in rounds. Number the questions. Keep a round to 8 questions or fewer. Offer defaults so the user can answer quickly. Never ask for information that is already in `series.json` or the current brief.

## Round 0 — the four required parameters

Ask these before any creative work. If the user already supplied one, confirm it instead of asking it again.

### 1. Video quality

Explain the trade-off in one line, then offer:

| Answer | Meaning | Use |
|---|---|---|
| `draft` | 854x480, 15 fps | review and timing |
| `standard` | 1920x1080, 30 fps | default final for most platforms |
| `high` | 1920x1080, 60 fps | smooth motion, camera moves, calculus |
| `4k` | 3840x2160, 60 fps | large displays, archival, explicit request |

Default: `standard`. Never render a final at `draft`.

### 2. Language

Ask for the **narration language and locale**, not just "English". Locale matters for the voice, spelling, and pronunciation.

Examples: `en-US`, `en-GB`, `it-IT`, `es-ES`, `es-MX`, `fr-FR`, `de-DE`, `pt-BR`, `pt-PT`, `nl-NL`, `pl-PL`, `ru-RU`, `uk-UA`, `tr-TR`, `ar-SA`, `hi-IN`, `zh-CN`, `ja-JP`, `ko-KR`.

Also ask:

- Should subtitles use the same language as the narration? If not, provide translated caption text per beat.
- Should on-screen math notation stay standard/international, or follow a local convention (decimal comma, `\operatorname{tg}` vs `\tan`, etc.)?

### 3. Voice

Offer a style first, then a specific voice:

| Style | Delivery | Typical fit |
|---|---|---|
| `warm-teacher` | clear, patient, slightly slower | classroom, general audience |
| `calm-documentary` | measured, low energy, authoritative | long-form, history, essays |
| `energetic-explainer` | faster, brighter, higher energy | YouTube, shorts, young audience |
| `authoritative-lecturer` | precise, deliberate, minimal hype | university, proofs, technical |
| `friendly-conversational` | informal, close, conversational | podcasts, accessible intros |

Then confirm the exact voice id, rate, and pitch. The curated catalog is in `references/voices.md`; any edge-tts voice id is also accepted.

Ask whether the voice should be:

- one narrator for the whole series (recommended for consistency);
- alternating hosts (only if the series format supports it);
- a recurring character with a name and verbal tics.

### 4. Template

Offer the catalog with one-line descriptions and a recommendation:

- `clean-light` — bright, precise, graph-friendly.
- `dark-board` — deep navy, chalk-bright accents, dramatic.
- `paper-editorial` — warm paper, serif, essayistic.

Ask whether this is a new series or an existing one. If existing, inherit its template and do not offer a change unless the user asks.

## Round 1 — the argument core

These questions determine whether the episode is worth making.

1. **Thesis.** What is the one sentence the viewer should accept by the end? If you cannot write it in one sentence, the episode is not ready.
2. **Audience.** Who is this for, and what do they already know? Name the prerequisite, not just "beginners".
3. **Stakes.** Why should this audience care now? What question are they already asking?
4. **Crux.** What is the hard step, the surprising turn, or the thing that is commonly misunderstood?
5. **Outcome.** What should the viewer be able to do, explain, or predict after watching?
6. **Rigor.** Intuition only, sketch of a proof, full proof, or worked derivation?
7. **Duration and platform.** Target minutes, aspect ratio, and where it will be watched (lecture, YouTube, classroom, social).

### Good vs. weak answers

| Weak | Strong |
|---|---|
| "Explain derivatives." | "The derivative is the limit of secant slopes, and the algebra of limits turns that geometry into \(2x\) for \(x^2\)." |
| "For students." | "First-year calculus students who know functions and slopes but are shaky on limits." |
| "It should be visual." | "A secant line closes onto the tangent while \(h \to 0\); the same triangle gives the symbolic limit." |
| "About 10 minutes." | "6-8 minutes: 90 seconds of intuition, 3 minutes of derivation, 2 minutes of example and misconception." |

## Round 2 — the argument chain

Build the chain explicitly. Ask the user to list, or propose a list and ask them to correct it.

1. **Definitions.** What must be defined before the argument starts?
2. **Assumptions.** What are we taking as given? Domain, continuity, differentiability, independence, finiteness, existence?
3. **Claims.** What are the 3-7 steps from assumptions to thesis? Write each as a one-line claim.
4. **Crux.** Which step is the one the viewer will resist or misread? That step gets the most time and the best visual.
5. **Example.** What concrete example makes the chain checkable?
6. **Counterexample or edge case.** What breaks if an assumption is dropped?
7. **Misconception.** What does the audience currently believe that is wrong, incomplete, or backwards?
8. **Visual evidence.** What should be plotted, transformed, or compared? What changes on screen as the claim becomes true?
9. **Conclusion.** What is the precise takeaway, including its scope and limits?

If the user cannot supply the chain, propose a draft chain from the thesis and ask them to correct it. This is usually faster than more open questions.

### Chain template

```text
Definitions -> Assumptions -> Claim 1 -> Claim 2 -> Crux -> Claim 3 -> Thesis
                                      \-> Example / counterexample /
```

## Round 3 — accuracy and production

Ask only what is relevant.

1. **Notation.** Which symbols, conventions, units, and naming should be used? Any curriculum-specific notation?
2. **Pronunciation.** Names, acronyms, and terms that TTS will get wrong. Record them in `accuracy.pronunciations` or as a `speech` form.
3. **Sources.** Papers, textbooks, historical claims. Do not invent citations; if a claim needs a source, mark it as a claim to verify.
4. **Claims to verify.** Formulas, constants, dates, attributions, "first/only/always" statements.
5. **Series continuity.** Recap from the previous episode? Next-episode hook? Running notation or motif?
6. **Brand and rights.** Logo, intro/outro, music license, font license, images.
7. **Sensitivity.** Avoid jokes or examples that punch down; check cultural references and names.

## Confirmation block

Before writing the storyboard, present exactly this compact block and ask for approval:

```text
THESIS: <one sentence>
AUDIENCE: <who> + <prerequisite>
OUTCOME: <what they can do after>
DURATION: <target> | PLATFORM: <16:9 / 9:16>
TEMPLATE: <id> | QUALITY: <draft/standard/high/4k>
LANGUAGE: <locale> | VOICE: <id> (<style>, rate, pitch)
CRUX: <the hard/surprising step>
CHAIN:
  1. <claim>
  2. <claim>
  3. <claim>
VISUAL: <the one image that carries the argument>
MISCONCEPTION: <wrong belief -> correction>
TAKEAWAY: <scope + limit>
OPEN QUESTIONS: <anything still unresolved>
```

Ask: "Approve this, or change any line?" Do not proceed on silence.

## Adaptive question rules

- **Vague theme** ("calculus", "linear algebra"): ask for a specific question, a specific audience, and a specific misconception. Offer 2-3 episode-sized angles.
- **Too broad**: split by question, not by chapter. "Why is the derivative a limit?" is an episode; "Calculus" is a season.
- **User is an expert**: skip basics, ask for the crux, the notation, and the counterexample. Do not over-explain.
- **User is a beginner**: ask what they already know and what confused them. Use their confusion as the episode's question.
- **User says "you decide"**: choose defaults, state them, and ask for a single approval. Do not keep asking.
- **User gives a script**: reverse-engineer the thesis, chain, visual, and parameters; point out gaps; ask only about the gaps.
- **User wants a series**: run the series interview in `references/series.md` before episode 1. Lock the template, voice, language, quality, naming, and narrative rhythm.

## Question bank by topic type

### Calculus / analysis

- What is the limit, derivative, or integral doing geometrically?
- Which quantity is changing, with respect to what?
- What is the smallest example where the definition and the shortcut disagree?
- Which approximation is being controlled, and by what?
- What breaks without continuity/differentiability/convergence?
- Should the visual show secants, rectangles, areas, or a moving point?

### Algebra / linear algebra

- What is the invariant? What is preserved under the transformation?
- What does the matrix do to a vector, a basis, or a space?
- Which example makes the abstraction necessary?
- What is the geometric meaning of the determinant/eigenvector/rank?
- Which convention (row vs. column vectors, field, ordering) must be fixed?

### Probability / statistics

- What is the sample space and the conditioning event?
- Which probability is being confused with which conditional probability?
- What does the graph show: distribution, likelihood, posterior, or simulation?
- What is the base rate, and how does it change the intuition?
- What is the frequentist vs. Bayesian interpretation, if relevant?

### Geometry / topology

- What is being preserved: length, angle, area, connectivity, dimension?
- What is the construction, and which step is not obvious?
- What does the diagram assume that the proof does not?
- Which counterexample breaks the naive picture?
- Should the visual be static, a sequence of transformations, or a 3D surface?

### Discrete math / algorithms

- What is the state, the transition, and the invariant?
- What is the worst case, and what is the witness?
- Which small case reveals the pattern?
- What is the graph: dependency, flow, tree, or state diagram?
- What is the proof technique: induction, contradiction, pigeonhole, exchange?

### Applied / modeling

- What is the model, and what does it deliberately ignore?
- What are the units and the scales?
- Which parameter changes the qualitative behavior?
- What does the data show, and what does it not show?
- What is the uncertainty, and how should it be visualized?

## Anti-patterns

- Asking 20 questions in one message.
- Asking "What should the video be about?" after the user already gave a theme.
- Accepting "for everyone" as an audience.
- Writing narration before the chain is settled.
- Choosing a graph before knowing the claim it supports.
- Silently changing the series template or voice.
- Proceeding without a confirmed thesis.
- Treating a topic list as a storyboard.
