# Why the derivative of x² is 2x

**Series:** Path of Knowledge · s01e001
**Template:** clean-light | **Quality:** standard
**Language:** en-US | **Voice:** en-US-AvaMultilingualNeural
**Target:** 180 s | **Estimate:** 181 s | **Words:** 432
**Thesis:** The derivative is the limit of secant slopes, and that limit turns the geometry of x² into the algebra of 2x.

---

## 01. title — title (not recorded)

**Narration:** Here is a question that the derivative formula hides. At a single point, a curve has no width, so what could its slope possibly mean?

**Visual:**
- Subtitle: A limit you can see

**Notes:** Open with the conceptual tension, not the formula.

## 02. the-question — section (not recorded)

**Narration:** The answer is a process. Start with an average slope over an interval, then shrink the interval toward a single point.

**Visual:**
- Subheading: Average slope versus instantaneous slope

**Notes:** Set up the two quantities the episode will connect.

## 03. what-we-know — bullets (not recorded)

**Narration:** For a straight line, slope is rise over run. For a parabola, the slope changes at every point. So we need a slope that belongs to one point, not to an interval.

**Visual:**
- A line has one slope: rise over run.
- A parabola changes steepness at every point.
- An interval has an average slope; a point needs a limit.

**Notes:** Bridge from prior knowledge to the need for a limit.

## 04. secant-1-3 — graph (not recorded)

**Narration:** Take x squared and two inputs, one and three. The secant line through those points has slope four. That is the average rate over the interval.

**Visual:**
- Graph: cartesian | animation: draw
  plot: y = x**2
  annotation: point P
  annotation: point Q
  annotation: secant average slope = 4

**Notes:** This graph shows that the secant slope is an average rate because it uses two distinct inputs.

## 05. secant-1-2 — graph (not recorded)

**Narration:** Now move the second point closer: from three to two. The average slope drops to three. The interval is smaller, and the average is closer to what we want.

**Visual:**
- Graph: cartesian | animation: draw
  plot: y = x**2
  annotation: point P
  annotation: point Q
  annotation: secant average slope = 3

**Notes:** This graph shows the average slope changing as the interval shrinks; it motivates the limit.

## 06. approaching-two — bullets (not recorded)

**Narration:** Keep shrinking h. The average slopes are four, three, two point five, two point one. They are converging to two, but no single average is the answer.

**Visual:**
- h = 2: average slope 4
- h = 1: average slope 3
- h = 0.5: average slope 2.5
- h = 0.1: average slope 2.1
- Limit as h → 0: 2

**Notes:** Make the numerical pattern explicit before the visual limit.

## 07. secant-to-tangent — graph (not recorded)

**Narration:** Watch the secant line as h goes to zero. The line pivots toward the tangent, and the average slope approaches two. That limiting line is the derivative at x equals one.

**Visual:**
- Graph: cartesian | animation: {'type': 'secant_to_tangent', 'x': 1, 'h_start': 2, 'h_end': 0.02, 'expr': 'x**2', 'show_triangle': True}
  plot: y = x**2

**Notes:** This graph shows the crux visually: the secant line's limiting position is the tangent, and its slope is the derivative.

## 08. definition — equation (not recorded)

**Narration:** Formally, the derivative is the limit of the difference quotient as h approaches zero. The quotient is an average slope; the limit is the instantaneous slope.

**Visual:**
- LaTeX: `f'(x) = \lim_{h \to 0} \frac{f(x+h)-f(x)}{h}`

**Notes:** The formal bridge from geometry to algebra.

## 09. expand — equation (not recorded)

**Narration:** For f of x equals x squared, the numerator becomes x plus h squared minus x squared. Expanding gives two x h plus h squared.

**Spoken form:** For f of x equals x squared, the numerator becomes x plus h, squared, minus x squared. Expanding gives two x h plus h squared.

**Visual:**
- LaTeX: `\frac{(x+h)^2 - x^2}{h} = \frac{2xh + h^2}{h}`

**Notes:** Keep the h in the denominator visible: the cancellation is the next beat.

## 10. cancel — equation (not recorded)

**Narration:** Dividing by h is allowed because h is not zero during the limit. The quotient simplifies to two x plus h. Then the limit is two x.

**Visual:**
- LaTeX: `f'(x) = \lim_{h \to 0} (2x + h) = 2x`

**Notes:** The crux: cancellation is valid before the limit because h is nonzero on a punctured neighborhood.

## 11. tangent-at-one — graph (not recorded)

**Narration:** At x equals one, the formula gives a slope of two. The tangent line is y equals two x minus one, and it touches the parabola at one, one.

**Visual:**
- Graph: cartesian | animation: draw
  plot: y = x**2
  annotation: point (1, 1)
  annotation: tangent slope = 2

**Notes:** This graph shows the formula as a geometric object: the tangent line at (1,1) has slope 2.

## 12. misconception — compare (not recorded)

**Narration:** The common mistake is to set h equal to zero too early. That gives zero over zero. The correct move is to cancel h first, then let h approach zero.

**Visual:**
- Left: Common mistake
  - Set h = 0 immediately.
  - Get 0 / 0.
  - Conclude the slope is undefined.
- Right: Correct move
  - Keep h ≠ 0 while simplifying.
  - Cancel the common factor h.
  - Then let h → 0.

## 13. why-cancellation — bullets (not recorded)

**Narration:** This is why the cancellation step is the crux. It removes the thing that would make the denominator zero, and it leaves a finite expression whose limit we can read.

**Visual:**
- The limit never evaluates the quotient at h = 0.
- Cancellation is valid for every h ≠ 0.
- The simplified expression has a finite limit.

**Notes:** Make the logical status of the cancellation explicit.

## 14. derivative-function — graph (not recorded)

**Narration:** The derivative is also a function. For x squared, f prime of x equals two x. At each x, the height of the line gives the slope of the parabola.

**Visual:**
- Graph: cartesian | animation: draw
  plot: y = x**2
  plot: y = 2*x
  annotation: vertical_line x = 2
  annotation: point slope here = 4

**Notes:** This graph shows the derivative as a new function: its height at x is the slope of x² at x.

## 15. recap — recap (not recorded)

**Narration:** So the derivative is not a formula to memorize. It is the limit of an average slope, and the algebra is what survives the limit.

**Visual:**
- A secant slope is an average rate over an interval.
- The limit turns that average into an instantaneous rate.
- Cancelling h is the step that makes the limit finite.
- For x², the result is 2x.

## 16. outro — outro (not recorded)

**Narration:** Next time: what happens when the curve is not a parabola, and the average slope does not settle down?

**Visual:**
- Next: What happens when the function is not a parabola?
- CTA: Follow the path for the next episode.

---

## Accuracy checklist

- [ ] Every formula re-derived.
- [ ] Domains and edge cases checked.
- [ ] Notation consistent with the series.
- [ ] Sources real and cited.
- [ ] Pronunciations checked in the voice manifest.
