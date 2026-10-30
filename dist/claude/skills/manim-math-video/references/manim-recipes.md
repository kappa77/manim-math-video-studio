# Manim recipes for custom beats

The default `StoryboardScene` covers titles, sections, bullets, equations, 2D graphs, comparisons, recaps, outros, quotes, and images. Use this reference when a visual needs code the data-driven runtime cannot express.

## How custom beats work

1. Add a beat to `storyboard.json`:

```json
{
  "id": "local-linearity",
  "kind": "custom",
  "narration": "Zoom in far enough, and the curve looks straight.",
  "notes": "Camera zoom into (1,1), then reveal the tangent."
}
```

2. Override `custom_beat` in `episode.py`:

```python
from manim_lib.runtime import StoryboardScene

class Episode(StoryboardScene):
    def custom_beat(self, beat, vo):
        # vo.duration: narration length in seconds
        # vo.elapsed: time since this beat's narration began
        # vo.remaining: narration time left
        # vo.progress: 0..1
        dot = Dot(self.axes.c2p(1, 1))  # if you kept an axes reference
        self.play(FadeIn(dot), run_time=min(1.2, vo.duration * 0.25))
```

The runtime calls `custom_beat` inside the voiceover context, so any time you do not use is filled with a wait at the end. Keep animations within `vo.duration` to avoid visuals outliving the narration.

## Accessing the theme and brief

`StoryboardScene` exposes:

```python
self.theme.color("primary")
self.theme.font("heading")
self.theme.size("heading", 44)
self.theme.layout("margin", 0.7)
self.theme.graph_style("stroke_width", 5)
self.brief["episode"]["thesis"]
self.storyboard["beats"]
self.voice.get("local-linearity").duration
```

Use these instead of hardcoding colors, fonts, and sizes. That is how a custom beat stays inside the series template.

## A custom graph with a moving secant

```python
import numpy as np
from manim import *

class Episode(StoryboardScene):
    def custom_beat(self, beat, vo):
        axes = Axes(
            x_range=[-1, 4, 1],
            y_range=[-1, 10, 2],
            x_length=self.theme.layout("graph_width", 9.6),
            y_length=self.theme.layout("graph_height", 5.0),
            axis_config={
                "color": self.theme.color("axis"),
                "stroke_width": self.theme.graph_style("axis_stroke_width", 2.5),
            },
        )
        graph = axes.plot(
            lambda x: x**2,
            color=self.theme.color("primary"),
            stroke_width=self.theme.graph_style("stroke_width", 5),
        )
        self.play(Create(axes), Create(graph), run_time=1.5)

        x0 = 1.0
        h = ValueTracker(2.0)
        p = Dot(axes.c2p(x0, x0**2), color=self.theme.color("primary"))
        q = Dot(axes.c2p(x0 + h.get_value(), (x0 + h.get_value()) ** 2),
                color=self.theme.color("secondary"))
        q.add_updater(lambda m: m.move_to(
            axes.c2p(x0 + h.get_value(), (x0 + h.get_value()) ** 2)
        ))
        secant = always_redraw(lambda: Line(
            p.get_center(), q.get_center(),
            color=self.theme.color("secondary"),
            stroke_width=3,
        ))
        self.add(p, q, secant, h)
        self.play(h.animate.set_value(0.02), run_time=max(1.0, vo.remaining * 0.8))
```

If you need the axes later, store `self._last_axes = axes` in the custom method or build the whole visual in one beat.

## Camera moves

`StoryboardScene` inherits from `Scene`, not `MovingCameraScene`. For a camera move, either:

- animate the mobject group directly (scale and translate), or
- create a separate `MovingCameraScene` class and render it as its own episode scene.

A separate scene:

```python
from manim import *

class ZoomScene(MovingCameraScene):
    def construct(self):
        axes = Axes(x_range=[0, 2, 0.5], y_range=[0, 4, 1])
        graph = axes.plot(lambda x: x**2, color=BLUE)
        self.add(axes, graph)
        self.camera.frame.save_state()
        self.play(self.camera.frame.animate.scale(0.4).move_to(axes.c2p(1, 1)))
        self.wait(1)
        self.play(Restore(self.camera.frame))
```

Render it separately and concatenate, or use a custom beat that scales the mobjects instead. Camera moves interact with captions and layout; test at `draft`.

## 3D surfaces

3D needs `ThreeDScene` and a separate scene class. It does not use the data-driven graph runtime.

```python
import numpy as np
from manim import *

class SurfaceScene(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=70 * DEGREES, theta=-45 * DEGREES)
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-1, 9, 2],
        )
        surface = axes.plot_surface(
            lambda u, v: u**2 + v**2,
            u_range=[-2, 2],
            v_range=[-2, 2],
            resolution=(32, 32),
            fill_opacity=0.75,
        )
        surface.set_fill_by_value(
            axes=axes,
            colorscale=[(BLUE, 0), (YELLOW, 4), (RED, 8)],
            axis=2,
        )
        self.add(axes, surface)
        self.begin_ambient_camera_rotation(rate=0.15)
        self.wait(6)
        self.stop_ambient_camera_rotation()
```

For a narrated 3D segment, add the audio and subtitles manually:

```python
self.add_sound("voice/3d.wav")
self.add_subcaption("A paraboloid curves upward in every direction.", duration=6)
self.wait(6)
```

Then concatenate the scene with the rest of the episode, or build the whole episode as a single `ThreeDScene` with sound at each beat.

## Equations

### Transform through steps

```python
eq1 = MathTex(r"f'(x) = \lim_{h \to 0} \frac{f(x+h)-f(x)}{h}")
eq2 = MathTex(r"f'(x) = \lim_{h \to 0} \frac{2xh+h^2}{h}")
eq3 = MathTex(r"f'(x) = \lim_{h \to 0} (2x+h) = 2x")
self.play(Write(eq1))
self.play(TransformMatchingTex(eq1, eq2))
self.play(TransformMatchingTex(eq2, eq3))
```

If `TransformMatchingTex` misbehaves, use `ReplacementTransform`. Keep the number of isolated substrings small.

### Color a term

```python
eq = MathTex(
    r"f'(x) = \lim_{h \to 0} (2x+h)",
    substrings_to_isolate=["h"],
    tex_to_color_map={"h": YELLOW},
)
```

### Aligned derivations

```python
eq = MathTex(
    r"f'(x)", r"&=", r"\lim_{h \to 0} \frac{(x+h)^2-x^2}{h}", r"\\",
    r"", r"&=", r"\lim_{h \to 0} \frac{2xh+h^2}{h}", r"\\",
    r"", r"&=", r"\lim_{h \to 0} (2x+h)",
    tex_environment="align*",
)
```

`align*` requires the `amsmath` package in the LaTeX distribution. Test at draft.

## Text and typography

- Use the theme fonts: `font=self.theme.font("heading")`.
- Keep on-screen text shorter than the narration.
- Use `Text` for prose and `MathTex` for equations. Avoid mixing them in one mobject unless you use `Tex` with `\text{}`.
- Use `Paragraph` for multi-line prose.
- Use `scale_to_fit_width` to prevent overflow. Never scale text below ~20pt at 1080p.
- Use `t2c` to color a word: `Text("The limit", t2c={"limit": YELLOW})`.
- For emphasis, change color and weight, not size alone.

## Timers and updaters

```python
tracker = ValueTracker(0)
dot = Dot()
dot.add_updater(lambda m: m.move_to(axes.c2p(tracker.get_value(), f(tracker.get_value()))))
self.add(tracker, dot)
self.play(tracker.animate.set_value(2), run_time=3)
```

Remember to remove updaters before fading out if the updater depends on an object that is being removed:

```python
dot.clear_updaters()
```

## Sound and subtitles inside a custom scene

```python
self.add_sound(str(self.root / "voice" / "segment.wav"))
self.add_subcaption("The caption text.", duration=4.2, offset=0)
```

`add_sound` starts at the current scene time. `add_subcaption` also starts at the current scene time, plus `offset`.

## Performance

- Use `use_vectorized=True` on `axes.plot` for expression plots.
- Keep graph samples moderate: 100-300 points is usually enough.
- Avoid `always_redraw` with expensive `get_riemann_rectangles` every frame. Use a few discrete transforms.
- Cache partial movies while iterating. Use `--disable_caching` only when you suspect a stale cache.
- Render `draft` at 480p15 for layout and timing. Do not judge typography at 480p; use a still frame at 1080p for final type checks.
- Prefer `Create`, `FadeIn`, and `Transform` over many simultaneous animations.
- Long `TransformMatchingTex` chains are slow; split them into beats.

## CLI differences

Manim Community 0.22 uses `manim render ...`. Older versions use `manim ...`. `render.py` detects the version and chooses the correct form. If you invoke Manim manually, check `manim --help`.

## Debugging

- `manim checkhealth` reports missing LaTeX and dvisvgm.
- `manim render -ql --disable_caching episode.py Episode` renders a fast draft.
- Use `--format png -s` to save the last frame for layout inspection.
- If audio is missing, check that the manifest paths exist and that the WAV files are valid.
- If the video ends before the audio, the scene's visual time is shorter than the narration; add waits or animations.
- If captions are out of sync, check the storyboard IDs and rerun `tts.py`.
