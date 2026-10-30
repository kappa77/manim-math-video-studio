# Why 23 people are enough for a shared birthday

**Series:** Path of Knowledge · s01e001
**Template:** clean-light | **Quality:** standard
**Language:** en-US | **Voice:** en-US-AvaMultilingualNeural
**Target:** 110 s | **Estimate:** 113 s | **Words:** 269
**Thesis:** The birthday problem is about pairs, not people: 23 people create 253 pairs, so a 50% coincidence is unremarkable.

---

## 01. title — title (10.5s)

**Narration:** Twenty-three people in one room. The chance that two of them share a birthday is about fifty percent. That sounds impossible, so let's count it properly.

**Visual:**
- Subtitle: A fifty percent coincidence, once you count pairs

**Notes:** Open on the number, not the formula: 23 people, 50% is the whole puzzle.

## 02. the-claim — section (11.7s)

**Narration:** Assume three hundred sixty-five equally likely days, and ignore leap years. The question is whether any two people in the group match, not whether someone matches a particular person.

**Visual:**
- Subheading: 365 equally likely days, 23 people, one shared birthday

**Notes:** Pinning the assumptions here keeps the later arithmetic honest. The word any is the hinge.

## 03. why-it-feels-wrong — bullets (12.3s)

**Narration:** The usual mistake is to compare one person with the other twenty-two. That gives twenty-three small chances, about six percent in total. It also quietly assumes the question names somebody.

**Visual:**
- 365 days available
- Only 23 people
- Naive guess: 23 / 365, about 6%

**Notes:** Name the wrong model before replacing it; the viewer will recognise their own reasoning.

## 04. count-pairs — bullets (15.0s)

**Narration:** So count pairs instead of people. Every two people form one pair, and twenty-three people form twenty-three times twenty-two divided by two: two hundred fifty-three pairs. Each pair is a separate chance of a coincidence.

**Visual:**
- Every two people form one pair
- 23 times 22 over 2 equals 253 pairs
- Each pair is its own coincidence

**Notes:** The pivot of the episode: 253 comparisons is the quantity that grows, not 23 people.

## 05. the-curve — graph (13.6s)

**Narration:** Here is the exact probability against group size. It starts flat, then bends upward, because each newcomer pairs with everyone already in the room. At twenty-three people the curve crosses one half.

**Visual:**
- Graph: data | animation: draw
  annotation: point 23 people: 50.7%
  annotation: point 57 people: 99.0%

**Notes:** The graph earns its place by showing a rate change: the curve is flat at first, then accelerates. The crossing at 23 is a limit the viewer can see, not a number to trust.

## 06. the-formula — equation (20.5s)

**Narration:** The exact count is easier by complement. The chance that nobody matches is a product of shrinking fractions: three sixty-five over three sixty-five, then three sixty-four over three sixty-five, and so on. Subtract that product from one, and at twenty-three people you get fifty point seven percent.

**Visual:**
- LaTeX: `P(n) = 1 - \frac{365 \cdot 364 \cdots (365-n+1)}{365^{n}}`

**Notes:** Derive, do not announce: the product is the no-match path, and subtracting it from one is the complement rule.

## 07. intuition-vs-count — compare (12.2s)

**Narration:** So the intuition was not wrong about days. It was wrong about pairs. Twenty-three people look small next to three hundred sixty-five days, yet they create two hundred fifty-three comparisons.

**Visual:**
- Left: Intuition
  - 23 people vs 365 days
  - Each one looks unlikely
  - Guess: about 6%
- Right: Count
  - 253 pairs, each a chance
  - Pairs grow quadratically
  - Exact answer: 50.7%

**Notes:** The comparison is between two models of the same situation, not two facts.

## 08. recap — recap (13.9s)

**Narration:** Three things to keep. Pairs grow with the square of the group, so intuition fails early. Counting the complement beats counting matches. And fifty-seven people are enough for ninety-nine percent.

**Visual:**
- Pairs grow with the square of the group
- Counting the complement beats counting matches
- 23 people: 50.7%
- 57 people: 99.0%

**Notes:** Restate the mechanism, then the two landmark numbers.

## 09. outro — outro (4.7s)

**Narration:** Next time: more places where counting pairs beats counting people.

**Visual:**
- Next: Where else does counting pairs beat counting people?
- CTA: Follow the path for the next episode.

**Notes:** Close on the transferable idea, not on birthdays.

---

## Accuracy checklist

- [ ] Every formula re-derived.
- [ ] Domains and edge cases checked.
- [ ] Notation consistent with the series.
- [ ] Sources real and cited.
- [ ] Pronunciations checked in the voice manifest.
