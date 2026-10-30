"""Data-driven 2D graph construction for the storyboard runtime."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np
from manim import *  # noqa: F403 - Manim public API is the scene vocabulary


from .expr import compile_expr, numeric_derivative, sample_values
from .theme import Theme


class GraphSpecError(ValueError):
    pass


@dataclass
class GraphBundle:
    spec: dict[str, Any]
    axes: Axes
    group: VGroup
    plots: list[VMobject] = field(default_factory=list)
    annotations: VGroup = field(default_factory=VGroup)
    ticks: VGroup = field(default_factory=VGroup)
    axis_labels: VGroup = field(default_factory=VGroup)
    legend: VGroup | None = None
    grid: VMobject | None = None
    function: Callable[..., Any] | None = None
    plot_specs: list[dict[str, Any]] = field(default_factory=list)

    @property
    def all_plots(self) -> VGroup:
        return VGroup(*self.plots)


class GraphBuilder:
    def __init__(self, theme: Theme, latex_available: bool = False):
        self.theme = theme
        self.latex_available = latex_available
        self._first_expr: str | None = None

    # ------------------------------------------------------------------ labels
    def label(
        self,
        text: str,
        size: float | None = None,
        color: str | None = None,
        *,
        math_text: bool = False,
    ) -> VMobject:
        text = "" if text is None else str(text)
        size = float(size if size is not None else self.theme.size("label", 22))
        color = color or self.theme.color("ink")
        stripped = text.strip()
        use_math = math_text or (
            len(stripped) >= 2 and stripped.startswith("$") and stripped.endswith("$")
        )
        if use_math and self.latex_available:
            latex = stripped[1:-1] if stripped.startswith("$") else stripped
            mob = MathTex(latex, font_size=size, color=color)
        else:
            if use_math:
                text = stripped.strip("$")
            mob = Text(
                text,
                font=self.theme.font("body"),
                font_size=size,
                color=color,
            )
        max_width = float(config.frame_width) - 2 * float(self.theme.layout("margin", 0.7))
        if mob.width > max_width:
            mob.scale_to_fit_width(max_width)
        return mob

    def _color(self, spec: dict[str, Any], default: str = "primary") -> str:
        if spec.get("color"):
            return str(spec["color"])
        return self.theme.role(spec.get("color_role"), default)

    # ------------------------------------------------------------------ ranges
    @staticmethod
    def _range(value: Any, default: list[float], name: str) -> list[float]:
        if value is None:
            value = default
        if not isinstance(value, (list, tuple)) or len(value) < 2:
            raise GraphSpecError(f"{name} must be [min, max, step].")
        if len(value) == 2:
            value = [value[0], value[1], (value[1] - value[0]) / 10.0]
        minimum, maximum, step = float(value[0]), float(value[1]), float(value[2])
        if maximum <= minimum:
            raise GraphSpecError(f"{name} maximum must be greater than minimum.")
        if step <= 0:
            raise GraphSpecError(f"{name} step must be positive.")
        return [minimum, maximum, step]

    # ------------------------------------------------------------------ build
    def build(self, spec: dict[str, Any]) -> GraphBundle:
        if not isinstance(spec, dict):
            raise GraphSpecError("graph must be an object.")
        kind = str(spec.get("type", "cartesian"))
        x_range = self._range(spec.get("x_range"), [-5, 5, 1], "x_range")
        y_range = self._range(spec.get("y_range"), [-3, 3, 1], "y_range")
        x_length = float(spec.get("x_length", self.theme.layout("graph_width", 9.6)))
        y_length = float(spec.get("y_length", self.theme.layout("graph_height", 5.0)))
        margin = float(self.theme.layout("margin", 0.7))
        x_length = min(x_length, max(1.0, float(config.frame_width) - 2 * margin))
        equal_aspect = spec.get("equal_aspect")
        if equal_aspect is None:
            equal_aspect = kind == "parametric"
        if equal_aspect:
            x_span = x_range[1] - x_range[0]
            y_span = y_range[1] - y_range[0]
            scale = min(x_length / x_span, y_length / y_span)
            x_length = scale * x_span
            y_length = scale * y_span
        axis_color = self.theme.color("axis")
        axis_width = float(self.theme.graph_style("axis_stroke_width", 2.5))
        axes = Axes(
            x_range=x_range,
            y_range=y_range,
            x_length=x_length,
            y_length=y_length,
            axis_config={
                "color": axis_color,
                "stroke_width": axis_width,
                "include_ticks": True,
            },
            tips=True,
        )

        grid = None
        if spec.get("show_grid", False):
            grid = NumberPlane(
                x_range=x_range,
                y_range=y_range,
                x_length=x_length,
                y_length=y_length,
                background_line_style={
                    "stroke_color": self.theme.color("grid"),
                    "stroke_opacity": float(self.theme.graph_style("grid_opacity", 0.25)),
                    "stroke_width": 1.0,
                },
                axis_config={"stroke_opacity": 0.0, "include_ticks": False},
            )
            grid.move_to(axes.get_center())

        bundle = GraphBundle(spec=spec, axes=axes, group=VGroup(), grid=grid)
        if grid is not None:
            bundle.group.add(grid)
        bundle.group.add(axes)

        show_ticks = spec.get("show_ticks")
        if show_ticks is None:
            show_ticks = kind not in {"parametric", "bars"}
        ticks = self._build_ticks(axes, x_range, y_range, bool(show_ticks))
        bundle.ticks = ticks
        bundle.group.add(ticks)

        axis_labels = self._build_axis_labels(axes, spec)
        bundle.axis_labels = axis_labels
        bundle.group.add(axis_labels)

        plots, plot_specs, function = self._build_plots(axes, spec, kind)
        bundle.plots = plots
        bundle.plot_specs = plot_specs
        bundle.function = function
        bundle.group.add(*plots)

        annotations = self._build_annotations(axes, spec, kind)
        bundle.annotations = annotations
        bundle.group.add(annotations)

        if spec.get("legend", True) and any(self._plot_label(p) for p in plot_specs):
            legend = self._build_legend(plot_specs)
            if legend is not None:
                bundle.legend = legend
                bundle.group.add(legend)

        return bundle

    # ------------------------------------------------------------------ ticks
    @staticmethod
    def _format_tick(value: float) -> str:
        if abs(value) < 1e-10:
            return "0"
        if abs(value - round(value)) < 1e-10:
            return str(int(round(value)))
        return f"{value:g}"

    @staticmethod
    def _tick_values(minimum: float, maximum: float, step: float, max_ticks: int = 10) -> list[float]:
        count = int(math.floor((maximum - minimum) / step + 1e-9)) + 1
        while count > max_ticks and step > 0:
            step *= 2
            count = int(math.floor((maximum - minimum) / step + 1e-9)) + 1
        values: list[float] = []
        value = math.ceil((minimum - 1e-9) / step) * step
        while value <= maximum + 1e-9:
            values.append(round(value, 10))
            value += step
        return values

    def _build_ticks(
        self,
        axes: Axes,
        x_range: list[float],
        y_range: list[float],
        show: bool,
    ) -> VGroup:
        ticks = VGroup()
        if not show:
            return ticks
        tick_size = float(self.theme.graph_style("tick_size", 18))
        color = self.theme.color("muted")
        buff = float(self.theme.graph_style("tick_label_buff", 0.12))
        font = self.theme.font("body")

        x_at_zero = min(max(0.0, x_range[0]), x_range[1])
        y_at_zero = min(max(0.0, y_range[0]), y_range[1])
        x_values = self._tick_values(x_range[0], x_range[1], x_range[2])
        y_values = self._tick_values(y_range[0], y_range[1], y_range[2])
        for value in x_values:
            if abs(value) < 1e-10:
                continue
            label = Text(
                self._format_tick(value),
                font=font,
                font_size=tick_size,
                color=color,
            )
            label.next_to(axes.c2p(value, y_at_zero), DOWN, buff=buff)
            ticks.add(label)
        for value in y_values:
            if abs(value) < 1e-10:
                continue
            label = Text(
                self._format_tick(value),
                font=font,
                font_size=tick_size,
                color=color,
            )
            label.next_to(axes.c2p(x_at_zero, value), LEFT, buff=buff)
            ticks.add(label)
        if x_range[0] <= 0 <= x_range[1] and y_range[0] <= 0 <= y_range[1]:
            zero = Text("0", font=font, font_size=tick_size, color=color)
            zero.next_to(axes.c2p(0, 0), DOWN + LEFT, buff=buff)
            ticks.add(zero)
        return ticks

    def _build_axis_labels(self, axes: Axes, spec: dict[str, Any]) -> VGroup:
        labels = VGroup()
        size = float(self.theme.graph_style("label_size", 22))
        color = self.theme.color("ink")
        x_text = spec.get("x_label")
        y_text = spec.get("y_label")
        if x_text:
            x_label = self.label(str(x_text), size=size, color=color)
            x_label.next_to(axes.x_axis.get_end(), RIGHT, buff=0.28)
            labels.add(x_label)
        if y_text:
            y_label = self.label(str(y_text), size=size, color=color)
            y_label.next_to(axes.y_axis.get_end(), UP, buff=0.22)
            labels.add(y_label)
        return labels

    # ------------------------------------------------------------------ plots
    @staticmethod
    def _plot_label(plot_spec: dict[str, Any]) -> str:
        return str(plot_spec.get("label") or "")

    def _build_plots(
        self,
        axes: Axes,
        spec: dict[str, Any],
        kind: str,
    ) -> tuple[list[VMobject], list[dict[str, Any]], Callable[..., Any] | None]:
        plots: list[VMobject] = []
        plot_specs: list[dict[str, Any]] = []
        first_function: Callable[..., Any] | None = None
        default_roles = ("primary", "secondary", "success", "warning")

        if kind == "cartesian":
            raw_plots = spec.get("plots")
            if not raw_plots:
                if spec.get("expr"):
                    raw_plots = [{"expr": spec["expr"]}]
                else:
                    raise GraphSpecError("cartesian graph needs plots[] or expr.")
            for index, raw in enumerate(raw_plots):
                if isinstance(raw, str):
                    raw = {"expr": raw}
                if not raw.get("expr"):
                    raise GraphSpecError("Each cartesian plot needs an expr.")
                expr = str(raw["expr"])
                fn = compile_expr(expr)
                if first_function is None:
                    first_function = fn
                domain = raw.get("domain") or [spec.get("x_range", [-5, 5, 1])[0], spec.get("x_range", [-5, 5, 1])[1]]
                domain = [float(domain[0]), float(domain[1])]
                color = self._color(
                    raw,
                    default_roles[index % len(default_roles)],
                )
                graph = axes.plot(
                    lambda x, fn=fn: fn(x=x),
                    x_range=domain,
                    color=color,
                    stroke_width=float(
                        raw.get("stroke_width", self.theme.graph_style("stroke_width", 5))
                    ),
                    use_vectorized=True,
                )
                plots.append(graph)
                plot_specs.append({**raw, "expr": expr, "_color": color, "_graph": graph})

        elif kind == "parametric":
            if not spec.get("x_expr") or not spec.get("y_expr"):
                raise GraphSpecError("parametric graph needs x_expr and y_expr.")
            x_fn = compile_expr(str(spec["x_expr"]), variables=("t",))
            y_fn = compile_expr(str(spec["y_expr"]), variables=("t",))
            t_range = spec.get("t_range", [0, math.tau, 0.01])
            if len(t_range) < 2:
                raise GraphSpecError("t_range must be [min, max] or [min, max, step].")
            color = self._color(spec, "primary")
            graph = ParametricFunction(
                lambda t: axes.c2p(x_fn(t=t), y_fn(t=t)),
                t_range=[float(t_range[0]), float(t_range[1])],
                color=color,
                stroke_width=float(
                    spec.get("stroke_width", self.theme.graph_style("stroke_width", 5))
                ),
            )
            plots.append(graph)
            plot_specs.append({**spec, "_color": color, "_graph": graph})

        elif kind == "data":
            points = spec.get("points")
            if not points:
                x_values = spec.get("x_values") or []
                y_values = spec.get("y_values") or []
                if len(x_values) != len(y_values) or not x_values:
                    raise GraphSpecError("data graph needs points[] or equal x_values/y_values.")
                points = list(zip(x_values, y_values))
            points = [(float(point[0]), float(point[1])) for point in points]
            color = self._color(spec, "primary")
            scene_points = [axes.c2p(x, y) for x, y in points]
            data_group = VGroup()
            if spec.get("line", True) and len(scene_points) > 1:
                line = VMobject(color=color, stroke_width=float(
                    spec.get("stroke_width", self.theme.graph_style("stroke_width", 5))
                ))
                line.set_points_as_corners(scene_points)
                data_group.add(line)
            if spec.get("vertices", True):
                dots = VGroup(
                    *[
                        Dot(point, radius=float(self.theme.graph_style("dot_radius", 0.07)), color=color)
                        for point in scene_points
                    ]
                )
                data_group.add(dots)
            plots.append(data_group)
            plot_specs.append({**spec, "_color": color, "_graph": data_group})

        elif kind == "bars":
            categories = spec.get("categories") or []
            values = spec.get("values") or []
            if len(categories) != len(values) or not categories:
                raise GraphSpecError("bars graph needs equal categories[] and values[].")
            maximum = max(float(value) for value in values) or 1.0
            bar_group = VGroup()
            bar_width = 0.55
            for index, (category, value) in enumerate(zip(categories, values)):
                value = float(value)
                role = (spec.get("bar_colors") or [])[index] if index < len(spec.get("bar_colors") or []) else "primary"
                color = self.theme.role(role, "primary")
                bottom = axes.c2p(index + 0.5, max(0.0, 0.0))
                top = axes.c2p(index + 0.5, value)
                height = abs(top[1] - bottom[1])
                width = abs(axes.c2p(index + 0.5 + bar_width / 2, 0)[0] - axes.c2p(index + 0.5 - bar_width / 2, 0)[0])
                rect = Rectangle(
                    width=width,
                    height=height,
                    color=color,
                    fill_color=color,
                    fill_opacity=0.75,
                    stroke_width=0,
                )
                rect.move_to((bottom + top) / 2)
                label = Text(
                    str(category),
                    font=self.theme.font("body"),
                    font_size=float(self.theme.graph_style("tick_size", 18)),
                    color=self.theme.color("muted"),
                )
                label.next_to(axes.c2p(index + 0.5, axes.y_range[0] if hasattr(axes, "y_range") else spec.get("y_range", [0, 1, 1])[0]), DOWN, buff=0.15)
                value_label = Text(
                    self._format_tick(value),
                    font=self.theme.font("body"),
                    font_size=float(self.theme.graph_style("tick_size", 18)),
                    color=self.theme.color("ink"),
                )
                value_label.next_to(rect, UP, buff=0.08)
                bar_group.add(rect, label, value_label)
            plots.append(bar_group)
            plot_specs.append({**spec, "_color": self.theme.color("primary"), "_graph": bar_group})

        elif kind == "vector_field":
            if not spec.get("x_expr") or not spec.get("y_expr"):
                raise GraphSpecError("vector_field needs x_expr and y_expr.")
            vx = compile_expr(str(spec["x_expr"]), variables=("x", "y"))
            vy = compile_expr(str(spec["y_expr"]), variables=("x", "y"))
            x_unit = axes.get_x_unit_size()
            y_unit = axes.get_y_unit_size()
            scale = float(spec.get("scale", 1.0))
            x_range = list(axes.x_range)
            y_range = list(axes.y_range)
            x_scene = [axes.c2p(x_range[0], 0)[0], axes.c2p(x_range[1], 0)[0], float(spec.get("density", 1.0))]
            y_scene = [axes.c2p(0, y_range[0])[1], axes.c2p(0, y_range[1])[1], float(spec.get("density", 1.0))]

            def field(point: np.ndarray) -> np.ndarray:
                data_x, data_y = axes.p2c(point)[:2]
                return np.array(
                    [
                        float(vx(x=data_x, y=data_y)) * x_unit * scale,
                        float(vy(x=data_x, y=data_y)) * y_unit * scale,
                        0.0,
                    ]
                )

            color = self._color(spec, "primary")
            vector_field = ArrowVectorField(
                field,
                x_range=x_scene,
                y_range=y_scene,
                color=color,
                vector_config={"stroke_width": 2.0, "tip_length": 0.12},
            )
            plots.append(vector_field)
            plot_specs.append({**spec, "_color": color, "_graph": vector_field})

        else:
            raise GraphSpecError(f"Unsupported graph type {kind!r}.")

        return plots, plot_specs, first_function

    # ------------------------------------------------------------------ legend
    def _build_legend(self, plot_specs: list[dict[str, Any]]) -> VGroup | None:
        entries = VGroup()
        size = float(self.theme.graph_style("tick_size", 18))
        for plot_spec in plot_specs:
            label_text = self._plot_label(plot_spec)
            if not label_text:
                continue
            color = str(plot_spec.get("_color") or self.theme.color("primary"))
            swatch = Line(
                np.array([-0.28, 0.0, 0.0]),
                np.array([0.28, 0.0, 0.0]),
                color=color,
                stroke_width=float(self.theme.graph_style("stroke_width", 5)),
            )
            label = self.label(label_text, size=size, color=self.theme.color("ink"))
            entry = VGroup(swatch, label).arrange(np.array([1.0, 0.0, 0.0]), buff=0.14, aligned_edge=np.array([0.0, 0.0, 0.0]))
            entries.add(entry)
        if not entries:
            return None
        entries.arrange(np.array([0.0, -1.0, 0.0]), buff=0.1, aligned_edge=np.array([-1.0, 0.0, 0.0]))
        background = BackgroundRectangle(
            entries,
            color=self.theme.color("surface"),
            fill_opacity=0.88,
            buff=0.1,
            stroke_width=0,
        )
        return VGroup(background, entries)

    # ------------------------------------------------------------------ annotations
    def _expr_for(self, annotation: dict[str, Any], bundle_function: Callable[..., Any] | None) -> Callable[..., Any]:
        if annotation.get("expr"):
            return compile_expr(str(annotation["expr"]))
        if bundle_function is None:
            raise GraphSpecError(
                f"Annotation {annotation.get('type')!r} needs expr because the graph has no cartesian function."
            )
        return bundle_function

    def _build_annotations(
        self,
        axes: Axes,
        spec: dict[str, Any],
        kind: str,
    ) -> VGroup:
        annotations = VGroup()
        raw_annotations = spec.get("annotations") or []
        function = None
        if kind == "cartesian":
            raw_plots = spec.get("plots") or ([{"expr": spec["expr"]}] if spec.get("expr") else [])
            if raw_plots:
                first = raw_plots[0]
                if isinstance(first, str):
                    first = {"expr": first}
                if first.get("expr"):
                    function = compile_expr(str(first["expr"]))
        for raw in raw_annotations:
            if not isinstance(raw, dict):
                raise GraphSpecError("Each annotation must be an object.")
            annotation_type = str(raw.get("type", "")).lower()
            color = self._color(raw, "primary")
            size = float(self.theme.graph_style("label_size", 22))
            label_text = raw.get("label")
            label_latex = raw.get("latex")
            if label_latex is not None:
                label_text = str(label_latex)
                math_text = True
            else:
                math_text = False

            def make_label() -> VMobject | None:
                if not label_text:
                    return None
                return self.label(str(label_text), size=size, color=color, math_text=math_text)

            if annotation_type in {"point", "dot"}:
                x, y = float(raw["x"]), float(raw["y"])
                dot = Dot(
                    axes.c2p(x, y),
                    radius=float(raw.get("radius", self.theme.graph_style("dot_radius", 0.07))),
                    color=color,
                )
                group = VGroup(dot)
                label = make_label()
                if label is not None:
                    label.next_to(dot, np.array([1.0, 1.0, 0.0]), buff=0.08)
                    offset = raw.get("label_offset")
                    if offset:
                        label.shift(np.array([float(offset[0]), float(offset[1]), 0.0]))
                    group.add(label)
                annotations.add(group)

            elif annotation_type == "text":
                x, y = float(raw["x"]), float(raw["y"])
                label = make_label()
                if label is not None:
                    label.move_to(axes.c2p(x, y))
                    annotations.add(label)

            elif annotation_type in {"vertical_line", "vline"}:
                x = float(raw["x"])
                y0 = float(raw.get("y_min", spec.get("y_range", [-3, 3, 1])[0]))
                y1 = float(raw.get("y_max", spec.get("y_range", [-3, 3, 1])[1]))
                line = DashedLine(
                    axes.c2p(x, y0),
                    axes.c2p(x, y1),
                    color=color,
                    stroke_width=2.0,
                    dash_length=0.12,
                )
                group = VGroup(line)
                label = make_label()
                if label is not None:
                    label.next_to(line, np.array([1.0, 0.0, 0.0]), buff=0.1)
                    group.add(label)
                annotations.add(group)

            elif annotation_type in {"horizontal_line", "hline"}:
                y = float(raw["y"])
                x0 = float(raw.get("x_min", spec.get("x_range", [-5, 5, 1])[0]))
                x1 = float(raw.get("x_max", spec.get("x_range", [-5, 5, 1])[1]))
                line = DashedLine(
                    axes.c2p(x0, y),
                    axes.c2p(x1, y),
                    color=color,
                    stroke_width=2.0,
                    dash_length=0.12,
                )
                group = VGroup(line)
                label = make_label()
                if label is not None:
                    label.next_to(line, np.array([0.0, 1.0, 0.0]), buff=0.1)
                    group.add(label)
                annotations.add(group)

            elif annotation_type == "tangent":
                x0 = float(raw["x"])
                fn = self._expr_for(raw, function)
                slope = float(numeric_derivative(fn, x0))
                x_range = spec.get("x_range", [-5, 5, 1])
                line = axes.plot(
                    lambda t: fn(x=x0) + slope * (t - x0),
                    x_range=[float(x_range[0]), float(x_range[1])],
                    color=color,
                    stroke_width=float(raw.get("stroke_width", self.theme.graph_style("stroke_width", 4))),
                )
                group = VGroup(line)
                if raw.get("dot", True):
                    group.add(Dot(axes.c2p(x0, fn(x=x0)), radius=float(self.theme.graph_style("dot_radius", 0.07)), color=color))
                label = make_label()
                if label is not None:
                    label.next_to(axes.c2p(x0, fn(x=x0)), np.array([1.0, 1.0, 0.0]), buff=0.12)
                    group.add(label)
                annotations.add(group)

            elif annotation_type == "secant":
                x1, x2 = float(raw["x1"]), float(raw["x2"])
                fn = self._expr_for(raw, function)
                y1, y2 = float(fn(x=x1)), float(fn(x=x2))
                x_range = spec.get("x_range", [-5, 5, 1])
                slope = (y2 - y1) / (x2 - x1) if abs(x2 - x1) > 1e-12 else 0.0
                line = axes.plot(
                    lambda t: y1 + slope * (t - x1),
                    x_range=[float(x_range[0]), float(x_range[1])],
                    color=color,
                    stroke_width=float(raw.get("stroke_width", self.theme.graph_style("stroke_width", 4))),
                )
                group = VGroup(line)
                for x, y in ((x1, y1), (x2, y2)):
                    group.add(Dot(axes.c2p(x, y), radius=float(self.theme.graph_style("dot_radius", 0.07)), color=color))
                label = make_label()
                if label is not None:
                    midpoint = axes.c2p((x1 + x2) / 2, (y1 + y2) / 2)
                    label.move_to(midpoint + np.array([0.0, 0.35, 0.0]))
                    group.add(label)
                annotations.add(group)

            elif annotation_type in {"area", "integral"}:
                x1, x2 = float(raw["x1"]), float(raw["x2"])
                fn = self._expr_for(raw, function)
                graph = axes.plot(lambda t: fn(x=t), x_range=[x1, x2], color=color)
                area = axes.get_area(
                    graph,
                    x_range=(x1, x2),
                    color=color,
                    opacity=float(raw.get("opacity", self.theme.graph_style("area_opacity", 0.22))),
                )
                group = VGroup(area)
                label = make_label()
                if label is not None:
                    label.move_to(axes.c2p((x1 + x2) / 2, fn(x=(x1 + x2) / 2) / 2))
                    group.add(label)
                annotations.add(group)

            elif annotation_type == "riemann":
                x1, x2 = float(raw["x1"]), float(raw["x2"])
                n = int(raw.get("n", 8))
                fn = self._expr_for(raw, function)
                graph = axes.plot(lambda t: fn(x=t), x_range=[x1, x2], color=color)
                rects = axes.get_riemann_rectangles(
                    graph,
                    x_range=(x1, x2),
                    dx=(x2 - x1) / max(1, n),
                    input_sample_type=str(raw.get("sample_type", "left")),
                    color=color,
                    fill_opacity=float(raw.get("opacity", self.theme.graph_style("area_opacity", 0.22))),
                    stroke_width=1.0,
                    stroke_color=self.theme.color("background"),
                )
                group = VGroup(rects)
                label = make_label()
                if label is not None:
                    label.next_to(rects, np.array([0.0, 1.0, 0.0]), buff=0.12)
                    group.add(label)
                annotations.add(group)

            elif annotation_type == "brace":
                x1, x2, y = float(raw["x1"]), float(raw["x2"]), float(raw.get("y", 0.0))
                start, end = axes.c2p(x1, y), axes.c2p(x2, y)
                brace = Brace(Line(start, end), buff=0.08, color=color)
                group = VGroup(brace)
                label = make_label()
                if label is not None:
                    label.next_to(brace, np.array([0.0, -1.0, 0.0]), buff=0.1)
                    group.add(label)
                annotations.add(group)

            elif annotation_type == "arrow":
                start = raw["from"]
                end = raw["to"]
                arrow = Arrow(
                    axes.c2p(float(start[0]), float(start[1])),
                    axes.c2p(float(end[0]), float(end[1])),
                    buff=0.0,
                    color=color,
                    stroke_width=float(raw.get("stroke_width", 3.0)),
                )
                group = VGroup(arrow)
                label = make_label()
                if label is not None:
                    label.next_to(arrow, np.array([1.0, 1.0, 0.0]), buff=0.1)
                    group.add(label)
                annotations.add(group)

            elif annotation_type == "slope_triangle":
                x1, x2 = float(raw["x1"]), float(raw["x2"])
                fn = self._expr_for(raw, function)
                y1, y2 = float(fn(x=x1)), float(fn(x=x2))
                p = axes.c2p(x1, y1)
                q = axes.c2p(x2, y2)
                corner = axes.c2p(x2, y1)
                horizontal = DashedLine(p, corner, color=color, stroke_width=2.0, dash_length=0.1)
                vertical = DashedLine(corner, q, color=color, stroke_width=2.0, dash_length=0.1)
                group = VGroup(horizontal, vertical)
                dx_label = raw.get("label_dx")
                dy_label = raw.get("label_dy")
                if dx_label:
                    text = self.label(str(dx_label), size=size, color=color)
                    text.next_to(horizontal, np.array([0.0, -1.0, 0.0]), buff=0.08)
                    group.add(text)
                if dy_label:
                    text = self.label(str(dy_label), size=size, color=color)
                    text.next_to(vertical, np.array([1.0, 0.0, 0.0]), buff=0.08)
                    group.add(text)
                annotations.add(group)

            elif annotation_type == "derivative":
                fn = self._expr_for(raw, function)
                x_range = spec.get("x_range", [-5, 5, 1])
                derivative = axes.plot(
                    lambda t: numeric_derivative(fn, t),
                    x_range=[float(x_range[0]), float(x_range[1])],
                    color=color,
                    stroke_width=float(raw.get("stroke_width", self.theme.graph_style("stroke_width", 4))),
                )
                group = VGroup(derivative)
                label = make_label()
                if label is not None:
                    label.next_to(derivative, np.array([1.0, 1.0, 0.0]), buff=0.12)
                    group.add(label)
                annotations.add(group)

            else:
                raise GraphSpecError(f"Unsupported annotation type {annotation_type!r}.")

        return annotations

    # ------------------------------------------------------------------ animations
    def make_secant_to_tangent(
        self,
        bundle: GraphBundle,
        *,
        x0: float,
        h_start: float,
        h_end: float,
        show_triangle: bool = True,
    ) -> tuple[VGroup, Any, VMobject]:
        """Return (moving group, ValueTracker, final tangent line)."""
        from manim import ValueTracker

        fn = bundle.function
        if fn is None:
            raise GraphSpecError("secant_to_tangent needs a cartesian function.")
        axes = bundle.axes
        primary = self.theme.color("primary")
        secondary = self.theme.color("secondary")
        h = ValueTracker(float(h_start))
        point = Dot(axes.c2p(x0, fn(x=x0)), color=primary, radius=float(self.theme.graph_style("dot_radius", 0.07)))
        moving_point = Dot(
            axes.c2p(x0 + h_start, fn(x=x0 + h_start)),
            color=secondary,
            radius=float(self.theme.graph_style("dot_radius", 0.07)),
        )
        moving_point.add_updater(
            lambda mob: mob.move_to(
                axes.c2p(
                    x0 + h.get_value(),
                    fn(x=x0 + h.get_value()),
                )
            )
        )
        secant = always_redraw(
            lambda: Line(
                point.get_center(),
                moving_point.get_center(),
                color=secondary,
                stroke_width=float(self.theme.graph_style("stroke_width", 4)),
            )
        )
        group = VGroup(secant, point, moving_point)

        if show_triangle:
            horizontal = always_redraw(
                lambda: DashedLine(
                    point.get_center(),
                    axes.c2p(x0 + h.get_value(), fn(x=x0)),
                    color=secondary,
                    stroke_width=2.0,
                    dash_length=0.1,
                )
            )
            vertical = always_redraw(
                lambda: DashedLine(
                    axes.c2p(x0 + h.get_value(), fn(x=x0)),
                    moving_point.get_center(),
                    color=secondary,
                    stroke_width=2.0,
                    dash_length=0.1,
                )
            )
            h_label = self.label("h", size=self.theme.size("label", 22), color=secondary)
            h_label.add_updater(
                lambda mob: mob.next_to(
                    axes.c2p(x0 + h.get_value() / 2, fn(x=x0)),
                    np.array([0.0, -1.0, 0.0]),
                    buff=0.08,
                )
            )
            dy_label = self.label(
                "f(x+h) - f(x)",
                size=self.theme.size("label", 22) * 0.8,
                color=secondary,
            )
            dy_label.add_updater(
                lambda mob: mob.next_to(
                    axes.c2p(x0 + h.get_value(), (fn(x=x0) + fn(x=x0 + h.get_value())) / 2),
                    np.array([1.0, 0.0, 0.0]),
                    buff=0.08,
                )
            )
            group.add(horizontal, vertical, h_label, dy_label)

        final_slope = float(numeric_derivative(fn, x0))
        x_range = bundle.spec.get("x_range", [-5, 5, 1])
        final_tangent = axes.plot(
            lambda t: fn(x=x0) + final_slope * (t - x0),
            x_range=[float(x_range[0]), float(x_range[1])],
            color=self.theme.color("success"),
            stroke_width=float(self.theme.graph_style("stroke_width", 4)),
        )
        final_tangent.set_opacity(0.0)
        group.add(final_tangent)
        return group, h, final_tangent

    def make_riemann_groups(
        self,
        bundle: GraphBundle,
        *,
        x1: float,
        x2: float,
        steps: list[int],
        expr: str | None = None,
    ) -> list[VGroup]:
        fn = compile_expr(expr) if expr else bundle.function
        if fn is None:
            raise GraphSpecError("riemann animation needs a cartesian function.")
        color = self.theme.role(bundle.spec.get("riemann_color_role"), "primary")
        graph = bundle.axes.plot(lambda t: fn(x=t), x_range=[x1, x2], color=color)
        groups: list[VGroup] = []
        for n in steps:
            rects = bundle.axes.get_riemann_rectangles(
                graph,
                x_range=(x1, x2),
                dx=(x2 - x1) / max(1, int(n)),
                input_sample_type="left",
                color=color,
                fill_opacity=float(self.theme.graph_style("area_opacity", 0.22)),
                stroke_width=1.0,
                stroke_color=self.theme.color("background"),
            )
            groups.append(rects)
        return groups
