# Mathematical accuracy

A beautiful animation of a wrong argument is worse than a plain correct one. Accuracy is a production requirement, not a final polish step.

## Verify the chain, not just the formula

For every episode:

1. Write the thesis as a precise statement, including its hypotheses.
2. List the assumptions. Check that each is used.
3. Check each link in the chain against the previous one.
4. Re-derive the crux independently, without looking at the script.
5. Test the conclusion on a small example and an edge case.
6. Check the scope: does the conclusion hold for all stated inputs, or only for the example?
7. Check the visual: does it illustrate the actual claim, or a special case presented as general?

## Common mathematical errors

| Error | Example | Check |
|---|---|---|
| Cancelling without a domain condition | Dividing by \(h\) at \(h=0\) | State \(h \neq 0\) during the limit. |
| Treating a limit as evaluation | "Plug in \(h=0\)" before simplifying | The limit is about a punctured neighborhood. |
| Assuming continuity/differentiability | Differentiating a function with a corner | State the hypothesis. |
| Confusing average and instantaneous | Secant slope vs. tangent slope | Label both. |
| Ignoring branch cuts | \(\sqrt{x^2}=x\) | Check signs and domains. |
| Dropping absolute values | \(\sqrt{x^2}=|x|\) | Use the correct identity. |
| Misusing implication | \(A \Rightarrow B\) does not mean \(B \Rightarrow A\) | Check the converse. |
| Confusing necessary and sufficient | "Differentiable, therefore continuous" is true; the converse is false | State the direction. |
| Wrong quantifier order | \(\forall \epsilon \exists \delta\) vs. \(\exists \delta \forall \epsilon\) | Write the quantifiers explicitly. |
| Illegal interchange | Swapping limits, sums, integrals, derivatives | State the theorem that permits it. |
| Sampling artifacts | A plot of \(\sin(1/x)\) near 0 | Restrict the domain or explain the resolution. |
| Misleading axes | Truncated y-axis | Label the window and the scale. |
| Probability inversion | \(P(A|B)\) vs. \(P(B|A)\) | Use Bayes' theorem explicitly. |
| Base-rate neglect | A rare disease test | Show the natural frequencies or the full table. |
| Independence assumption | Multiplying probabilities | State independence or condition. |
| Simpson's paradox | Aggregated vs. grouped data | Show both levels. |
| Area/volume scaling | Forgetting the Jacobian | State the transformation. |
| Units | Adding quantities with different units | Carry units through. |
| Rounding | Intermediate rounding changing the conclusion | Keep exact values until the end. |

## Notation

- Fix notation in `brief.accuracy.notation` and do not drift mid-episode.
- Do not mix Newton (`f'`) and Leibniz (`df/dx`) notation in one derivation without a reason.
- State whether angles are radians or degrees.
- State the domain before using an inverse function.
- Use \(\mathbb{R}\), \(\mathbb{N}\), \(\mathbb{Z}\), \(\mathbb{Q}\), \(\mathbb{C}\) consistently.
- Distinguish a function from its value: \(f\) vs. \(f(x)\).
- Distinguish a variable from a bound variable: \(\sum_{k=1}^n k\).
- Use `\operatorname{}` for multi-letter operators.
- Keep units in axis labels and in the narration.
- For vectors, fix row/column convention, bold vs. arrow notation, and the norm.

## Proof and rigor

`brief.episode.rigor` is one of:

- `intuition`: no formal proof; the goal is a correct mental model and an honest statement of what is not proved.
- `sketch`: the main steps and the crux, with some details omitted. Say what is omitted.
- `proof`: a complete argument for the stated audience, with all hypotheses and quantifiers.
- `derivation`: a computation with justified steps and clear assumptions.

Never present a sketch as a proof. If the episode is intuition-only, say so in the narration and the recap. If a step is not justified, label it as an assumption or a conjecture.

## Visuals and truth

A graph is evidence for the eyes, not a proof. It can suggest a claim, illustrate a definition, or expose a misconception. It cannot replace a quantifier or a hypothesis.

- Label the window and the scale when the view is partial.
- Do not use a dense sampling of a discontinuous function to imply continuity.
- Do not animate a limit as if the value were reached.
- Do not use a single example to establish a universal claim.
- Show a counterexample when an assumption is dropped.
- If the visual is a special case, say "here is one example" and state the general claim separately.

## Sources and claims

- Use real sources only. Do not invent a textbook, paper, date, or quotation.
- For historical claims, prefer primary sources or a reputable history of mathematics.
- For a named theorem, state the hypotheses, not just the name.
- For "first", "only", "always", "never", require a source or remove the word.
- Put uncertain claims in `brief.accuracy.claims_to_verify`; do not render them as settled.
- Record sources in `brief.accuracy.sources`. The video can cite them in the description or a final card.
- If you use an image, record its license and attribution.

## Independent review

Before final render:

- Re-derive the crux on paper.
- Check every equation with a symbolic or numerical tool where possible.
- Evaluate each graph expression at three points and compare with the plot.
- Check the edge cases named in the brief.
- Have a second person watch the draft without the script. Ask them to state the thesis and the crux. If they cannot, the episode is not clear enough.
- Check that the narration and the visual make the same claim. A mismatch is a bug.

## Red flags

- "It is obvious that..." without a reason.
- A formula appears with no definition of its symbols.
- The example is used as proof.
- The graph is too zoomed to see the claimed behavior.
- The narration says "always" or "never" without scope.
- A limit is described as "plugging in".
- A probability is inverted.
- A derivative is taken at a point where the function is not differentiable.
- An integral is computed without checking convergence.
- A matrix is inverted without checking the determinant.
- A simulation is presented as a theorem.
- A citation is vague or unverifiable.

## Final accuracy checklist

- [ ] Thesis is precise and scoped.
- [ ] Assumptions are stated and used.
- [ ] Each chain link is justified.
- [ ] Crux independently re-derived.
- [ ] Edge cases checked.
- [ ] Notation consistent.
- [ ] Units consistent.
- [ ] Graphs match expressions and domains.
- [ ] Visual claim equals narration claim.
- [ ] Sources real and recorded.
- [ ] Uncertain claims marked, not asserted.
- [ ] Recap states the scope and the limits.
