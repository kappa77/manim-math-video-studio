# Content accuracy and consistency

Verify the claims the video actually makes. Match the review to the subject rather than requiring a mathematical proof for every topic.

## Shared checks

- State the central question or narrative promise and check that the progression fulfills it.
- Distinguish facts, interpretations, hypotheses, examples, and fictional material. Do not present a reconstruction or illustrative animation as documentary evidence.
- Verify names, dates, quotations, statistics, attributions, and causal claims against appropriate sources. Use current sources for changing facts and authoritative primary material when available.
- Record real sources in `accuracy.sources`; record unresolved claims in `accuracy.claims_to_verify`. Resolve, qualify, or remove uncertain assertions before final delivery.
- Keep terminology, pronunciations, units, and conventions consistent. Use `accuracy.notation` for terminology rules when useful, or an empty list when irrelevant.
- Check that narration, captions, and visuals make the same claim. Record image rights and attribution for third-party material.

## Choose the relevant review

| Topic | Check |
|---|---|
| History and culture | Chronology, context, source provenance, competing accounts, anachronisms. |
| Science | Evidence, mechanism, limits of the model, uncertainty, correlation versus causation. |
| Technology and procedures | Version and prerequisites, executable steps where practical, observable outcomes and failure cases. |
| Literature and philosophy | Accurate passages and attribution, distinction between the work and the interpretation, fair treatment of alternatives. |
| Fiction | Character motivations, setting rules, chronology, continuity, and the promised resolution. External sourcing is needed only for factual assertions presented as real. |
| Mathematics and quantitative claims | Read [accuracy-math.md](accuracy-math.md) for formulas, domains, proofs, notation, and graphs. |

## Before final render

Check the central claim or narrative progression independently of the narration. Confirm that the recap preserves the scope and uncertainty of the content. Review the draft for misleading simplifications, omitted steps, continuity errors, and visuals that imply unsupported conclusions. Apply domain-specific checks only where relevant.
