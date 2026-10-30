"""A small, safe expression evaluator for graph specifications.

The storyboard is data, not code. Expressions are parsed with :mod:`ast` and a
strict allow-list before evaluation. No builtins, attributes, subscripts, or
imports are available.
"""

from __future__ import annotations

import ast
import math
import re
from typing import Any, Callable

import numpy as np

_ALLOWED_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Compare,
    ast.BoolOp,
    ast.IfExp,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Pow,
    ast.Mod,
    ast.FloorDiv,
    ast.USub,
    ast.UAdd,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.And,
    ast.Or,
    ast.Not,
)

_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,
    "arcsin": np.arcsin,
    "arccos": np.arccos,
    "arctan": np.arctan,
    "sinh": np.sinh,
    "cosh": np.cosh,
    "tanh": np.tanh,
    "exp": np.exp,
    "log": np.log,
    "ln": np.log,
    "log10": np.log10,
    "log2": np.log2,
    "sqrt": np.sqrt,
    "abs": np.abs,
    "floor": np.floor,
    "ceil": np.ceil,
    "sign": np.sign,
    "min": np.minimum,
    "max": np.maximum,
    "clip": np.clip,
    "where": np.where,
    "round": np.round,
}

_CONSTANTS: dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def normalize_expr(expr: str) -> str:
    """Normalize friendly math notation into Python/NumPy syntax."""
    text = str(expr).strip()
    text = (
        text.replace("−", "-")
        .replace("–", "-")
        .replace("×", "*")
        .replace("÷", "/")
        .replace("·", "*")
        .replace("√", "sqrt")
        .replace("π", "pi")
    )
    text = text.replace("^", "**")
    # Protect scientific notation (2e-3, 1E6) while inserting implicit products.
    scientific: list[str] = []

    def protect_scientific(match: re.Match[str]) -> str:
        scientific.append(match.group(0))
        return f"SCI{len(scientific) - 1}"

    text = re.sub(r"\d(?:\.\d+)?[eE][+-]?\d+", protect_scientific, text)
    # 2x -> 2*x, 2(x+1) -> 2*(x+1)
    text = re.sub(r"(?<=\d)(?=[A-Za-z_])", "*", text)
    text = re.sub(r"(?<=\d)(?=\()", "*", text)
    # (x+1)(x-1) -> (x+1)*(x-1), (x+1)x -> (x+1)*x
    text = re.sub(r"(?<=\))(?=[A-Za-z_0-9(])", "*", text)
    for index, value in enumerate(scientific):
        text = text.replace(f"SCI{index}", value)
    return text


def _validate_tree(tree: ast.AST, variables: set[str]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(
                f"Unsupported expression syntax: {type(node).__name__}. "
                "Use arithmetic, comparisons, and the documented functions."
            )
        if isinstance(node, ast.Name):
            if node.id not in variables and node.id not in _FUNCTIONS and node.id not in _CONSTANTS:
                raise ValueError(
                    f"Unknown name {node.id!r}. Allowed variables: {sorted(variables)}. "
                    f"Allowed functions: {sorted(_FUNCTIONS)}."
                )
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCTIONS:
                raise ValueError("Only documented mathematical functions may be called.")
            if node.keywords:
                raise ValueError("Keyword arguments are not supported in graph expressions.")


def compile_expr(
    expr: str,
    variables: tuple[str, ...] = ("x", "t"),
) -> Callable[..., Any]:
    """Compile an expression into a callable.

    The callable accepts keyword arguments for variables, e.g.
    ``f(x=2.0)`` or ``f(x=np.linspace(...))``.
    """
    normalized = normalize_expr(expr)
    try:
        tree = ast.parse(normalized, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Could not parse expression {expr!r}: {exc.msg}") from exc
    _validate_tree(tree, set(variables))
    code = compile(tree, "<graph expression>", "eval")

    def evaluate(**kwargs: Any) -> Any:
        unknown = set(kwargs) - set(variables)
        if unknown:
            raise ValueError(f"Unknown variables passed to expression: {sorted(unknown)}")
        env: dict[str, Any] = {}
        env.update(_CONSTANTS)
        env.update(_FUNCTIONS)
        env.update(kwargs)
        with np.errstate(all="ignore"):
            value = eval(code, {"__builtins__": {}}, env)  # noqa: S307 - allow-listed AST
        array = np.asarray(value, dtype=float)
        if array.ndim == 0:
            # Broadcast constants over an array variable so axes.plot(...,
            # use_vectorized=True) receives a curve-shaped array.
            for argument in kwargs.values():
                if isinstance(argument, np.ndarray) and argument.ndim > 0:
                    return np.full(argument.shape, float(array), dtype=float)
            return float(array)
        return array

    return evaluate


def sample_values(
    expr_fn: Callable[..., Any],
    x_values: np.ndarray,
    variable: str = "x",
) -> np.ndarray:
    """Evaluate a function over an array and replace non-finite values with NaN."""
    values = expr_fn(**{variable: x_values})
    array = np.asarray(values, dtype=float)
    array = np.where(np.isfinite(array), array, np.nan)
    return array


def numeric_derivative(
    expr_fn: Callable[..., Any],
    x: float | np.ndarray,
    h: float | None = None,
) -> Any:
    """Central-difference derivative, suitable for plotting (not for proof)."""
    x_array = np.asarray(x, dtype=float)
    if h is None:
        step = np.maximum(1e-5, np.abs(x_array) * 1e-6)
    else:
        step = np.full_like(x_array, float(h))
    with np.errstate(all="ignore"):
        value = (expr_fn(x=x_array + step) - expr_fn(x=x_array - step)) / (2 * step)
    value = np.asarray(value, dtype=float)
    value = np.where(np.isfinite(value), value, np.nan)
    if value.ndim == 0:
        return float(value)
    return value


def validate_expr(
    expr: str,
    variable: str = "x",
    sample_points: tuple[float, ...] = (-2.0, -0.5, 0.5, 2.0),
) -> None:
    """Raise a readable error if an expression cannot be evaluated."""
    fn = compile_expr(expr, variables=(variable,))
    for point in sample_points:
        try:
            fn(**{variable: point})
        except Exception as exc:  # noqa: BLE001 - report the user's expression
            raise ValueError(
                f"Expression {expr!r} failed at {variable}={point}: {exc}"
            ) from exc
