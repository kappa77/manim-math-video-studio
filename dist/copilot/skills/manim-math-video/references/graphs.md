# Graphs

Graphs are the main evidence in a math video. A graph is not a background; it is an argument. Before writing a graph spec, answer:

- What claim does this graph make visible?
- What changes on screen as the claim becomes true?
- What should the viewer look at first, second, and last?
- What would the viewer misunderstand if the graph were removed?

If there is no answer, use an equation transformation, a diagram, or a concrete example instead.

## Graph spec

A graph beat contains a `graph` object:

```json
{
  "kind": "graph",
  "narration": "...",
  "heading": "Average slope",
  "graph": {
    "type": "cartesian",
    "x_range": [-1, 4, 1],
    "y_range": [-1, 10, 2],
    "x_label": "x",
    "y_label": "f(x)",
    "plots": [
      {"expr": "x**2", "color_role": "primary", "label": "f(x) = x²"}
    ],
    "annotations": [],
    "animation": "draw"
  }
}
```

### Common fields

| Field | Default | Meaning |
|---|---|---|
| `type` | required | `cartesian`, `parametric`, `data`, `bars`, or `vector_field`. |
| `x_range` | `[-5, 5, 1]` | `[min, max, step]`. |
| `y_range` | `[-3, 3, 1]` | `[min, max, step]`. |
| `x_label`, `y_label` | none | Axis labels. Use plain text or a short Unicode symbol. |
| `x_length`, `y_length` | template layout | Axis length in scene units. |
| `show_ticks` | `false` for parametric/bars, else `true` | Draw numeric tick labels with theme fonts. |
| `show_grid` | `false` | Draw a faint grid. |
| `equal_aspect` | `true` for parametric, else `false` | Keep one scene unit per data unit on both axes, so circles stay circles. |
| `legend` | `true` if any plot has a label | Small legend inside the axes. |
| `animation` | `"draw"` | String or object; see below. |
| `notes` | none | Not rendered; record the claim the graph supports. |

### Expression syntax

Expressions are Python-like and evaluated with NumPy:

```text
x**2
sin(x) / x
exp(-x**2)
sqrt(abs(x))
2*x + 3
log(x)          # natural log
log10(x)
tan(x)
floor(x)
sign(x)
pi, e, tau
```

- Use `**` for powers. `^` is accepted and converted to `**`.
- `2x` and `2(x+1)` are accepted and converted to multiplication.
- Scientific notation such as `2e-3` and `1E6` is preserved.
- Use `*` explicitly elsewhere.
- `x` and `t` are the variables. A plot expression should use `x`; a parametric expression should use `t`.
- The evaluator is intentionally restricted to arithmetic, comparisons, and the functions listed in `manim_lib/expr.py`. It does not execute arbitrary Python.
- Discontinuities and asymptotes become `NaN` and are not drawn. Check the domain before trusting the picture.
- For a function with a restricted domain, set `domain: [a, b]` on the plot. Do not rely on a clipped view.

## Types

### Cartesian

Plot one or more functions of `x`.

```json
{
  "type": "cartesian",
  "x_range": [-6, 6, 1],
  "y_range": [-1.5, 1.5, 0.5],
  "x_label": "x",
  "y_label": "y",
  "plots": [
    {"expr": "sin(x)/x", "color_role": "primary", "label": "sinc(x)", "domain": [-6, 6]},
    {"expr": "1/x", "color_role": "secondary", "label": "1/x", "domain": [0.2, 6]}
  ],
  "annotations": [
    {"type": "horizontal_line", "y": 1, "label": "y = 1"},
    {"type": "point", "x": 0, "y": 1, "label": "removable hole"}
  ],
  "animation": "sweep"
}
```

Top-level `expr` is shorthand for a single plot:

```json
{"type": "cartesian", "expr": "x**2", "x_range": [-3, 3, 1], "y_range": [-1, 9, 1]}
```

### Parametric

Plot `(x(t), y(t))`.

```json
{
  "type": "parametric",
  "x_expr": "cos(t)",
  "y_expr": "sin(t)",
  "t_range": [0, 6.283, 0.01],
  "x_range": [-1.5, 1.5, 1],
  "y_range": [-1.5, 1.5, 1],
  "x_label": "x",
  "y_label": "y",
  "equal_aspect": true,
  "animation": "sweep"
}
```

Set `equal_aspect: true` for circles, angles, and geometric diagrams. Without it, the default 16:9 graph area stretches a circle into an ellipse.

### Data

Plot measured or discrete data.

```json
{
  "type": "data",
  "x_range": [0, 6, 1],
  "y_range": [0, 12, 2],
  "x_values": [0, 1, 2, 3, 4, 5],
  "y_values": [1, 2.4, 4.1, 5.8, 8.2, 10.1],
  "vertices": true,
  "line": true,
  "x_label": "time (s)",
  "y_label": "distance (m)"
}
```

You can also use `points: [[x, y], ...]`.

### Bars

Compare discrete categories. Use bars for counts and magnitudes, not for continuous functions.

```json
{
  "type": "bars",
  "categories": ["A", "B", "C"],
  "values": [12, 27, 19],
  "y_label": "count",
  "bar_colors": ["primary", "secondary", "success"]
}
```

### Vector field

Show direction and magnitude across a region.

```json
{
  "type": "vector_field",
  "x_range": [-3, 3, 1],
  "y_range": [-3, 3, 1],
  "x_expr": "-y",
  "y_expr": "x",
  "density": 1.0,
  "color_role": "primary",
  "animation": "draw"
}
```

## Annotations

Annotations are the labels, points, lines, and shaded regions that turn a plot into an argument. All coordinates are in data coordinates. `color_role` resolves through the template.

### `point`

```json
{"type": "point", "x": 1, "y": 1, "label": "P", "label_offset": [0.15, 0.15]}
```

### `text`

```json
{"type": "text", "x": 2, "y": 5, "text": "slope = 4", "color_role": "secondary"}
```

### `vertical_line` / `horizontal_line`

```json
{"type": "vertical_line", "x": 1, "label": "x = 1"}
{"type": "horizontal_line", "y": 2, "label": "y = 2"}
```

### `tangent`

Draw the tangent to `expr` at `x`.

```json
{"type": "tangent", "x": 1, "expr": "x**2", "label": "slope = 2"}
```

### `secant`

Draw the line through two points on `expr`.

```json
{"type": "secant", "x1": 1, "x2": 3, "expr": "x**2", "label": "average slope = 4"}
```

### `area`

Shade the area under `expr` between `x1` and `x2`.

```json
{"type": "area", "x1": 0, "x2": 2, "expr": "x**2", "label": "∫₀² x² dx"}
```

### `riemann`

Draw Riemann rectangles. Use with the `riemann` animation to refine them.

```json
{"type": "riemann", "x1": 0, "x2": 2, "n": 8, "expr": "x**2", "sample_type": "left"}
```

### `brace`

A brace between two x-coordinates at a given y.

```json
{"type": "brace", "x1": 0, "x2": 1, "y": -0.4, "label": "h"}
```

### `arrow`

```json
{"type": "arrow", "from": [1, 1], "to": [2, 2], "label": "Δy"}
```

### `slope_triangle`

Draw the rise/run triangle between two points on `expr`.

```json
{"type": "slope_triangle", "x1": 1, "x2": 2, "expr": "x**2", "label_dx": "h", "label_dy": "f(x+h) - f(x)"}
```

### `derivative`

Plot the numerical derivative of `expr` as a second curve.

```json
{"type": "derivative", "expr": "x**3", "label": "f'(x)", "color_role": "secondary"}
```

## Animations

`animation` can be a string or an object.

### `draw` (default)

Reveal axes, then plots, then annotations and legend.

### `sweep`

Draw the first plot, then move a dot along it. Use a `sweep` object to control timing:

```json
"animation": {"type": "sweep", "plot": 0, "run_time": 4.0}
```

If `run_time` is omitted, the runtime uses the remaining narration time.

### `secant_to_tangent`

Animate a secant line closing onto a tangent. This is the canonical derivative visual.

```json
"animation": {
  "type": "secant_to_tangent",
  "x": 1.5,
  "h_start": 2.0,
  "h_end": 0.02,
  "expr": "x**2",
  "show_triangle": true
}
```

The graph must have a matching plot expression. The runtime creates two movable points, a secant line, and optional rise/run labels.

### `riemann`

Refine rectangles in discrete steps.

```json
"animation": {"type": "riemann", "x1": 0, "x2": 2, "expr": "x**2", "steps": [4, 8, 16, 32]}
```

### `area`

Reveal the shaded area under a curve. Use with an `area` annotation.

### `none`

Add everything without animation. Use for a still that the narration discusses.

## Styling rules

- Use `color_role`, not raw hex, unless the spec is a one-off custom visual.
- Primary = the object under study. Secondary = comparison. Danger = misconception. Success = conclusion.
- Keep the number of curves at two or three. More than three needs a very good reason.
- Label curves near their ends or in a legend, not on top of the data.
- Axis labels include units when the quantities have units.
- Do not truncate the y-axis to exaggerate a difference unless the truncation is labeled.
- Keep scales honest. If the x and y units differ, say so or use separate axes.
- Show the origin when it is meaningful. Hide it when the interesting behavior is far away, but label the window.
- Avoid red/green as the only distinction. Use shape, line style, or direct labels.
- For inequalities, shade the feasible region and label the boundary.
- For limits, show the hole or the approach with an open dot and an arrow.

## Common pitfalls

| Pitfall | Fix |
|---|---|
| Plot looks wrong at asymptotes | Restrict the domain; use `NaN` gaps. |
| Labels collide | Move labels, reduce ticks, or use a legend. |
| Curves overlap | Change color role, line width, or split into two beats. |
| Graph is too dense | Zoom the window, reduce the number of curves, or animate a reveal. |
| Units missing | Add them to `x_label`/`y_label` and the narration. |
| Misleading scale | Label the window and avoid unequal aspect ratios for geometric claims. |
| Animation is too fast | Give the graph its own beat; do not rush the sweep. |
| The graph does not change | Use `sweep`, `secant_to_tangent`, or a parameter animation. |
| Equation and graph disagree | Check the expression and the plotted domain; the graph is not the proof. |

## 3D graphs

The default runtime handles 2D graphs. For surfaces, use a `custom` beat with a `ThreeDScene` or a separate scene. See `references/manim-recipes.md` for a complete surface example with camera orientation, color mapping, and axes.

## Verification checklist

- Evaluate the expression at three points and compare with the plot.
- Check the domain, especially division by zero, square roots, and logarithms.
- Check that the visual claim matches the narration.
- Check that the annotation coordinates are on the curve.
- Check that the axes labels and units are correct.
- Check the graph at 480p: can you still read the important labels?
- Check the graph without color: is the meaning still clear?
