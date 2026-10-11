"""Data dictionary harvested from the pydantic models in `core.schemas`.

`sweep()` walks every model and returns its docstring plus per-field type, required flag and a
description. A description comes from `Field(description=...)` first; failing that, from the
trailing `# comment` on the field's line (many models document that way); else it is missing.
`view_notes()` and `coverage()` use the models registered in `views.VIEW_MODELS` to annotate the
SQL views and to flag drift: a column with no description, or a model field the view no longer has.
"""

from __future__ import annotations

import ast
import importlib
import inspect
import io
import pkgutil
import tokenize
from functools import lru_cache

from pydantic import BaseModel

from core import schemas as _pkg


def _trailing_comments(src: str) -> dict[int, str]:
    out: dict[int, str] = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                out[tok.start[0]] = tok.string.lstrip("# ").strip()
    except (tokenize.TokenError, IndentationError):
        pass
    return out


def _field_comments(mod) -> dict[tuple[str, str], str]:
    """(class, field) -> trailing comment on the annotated assignment's line."""
    try:
        src = inspect.getsource(mod)
    except OSError:
        return {}
    comments = _trailing_comments(src)
    out = {}
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    c = comments.get(stmt.end_lineno or stmt.lineno)
                    if c:
                        out[(node.name, stmt.target.id)] = c
    return out


@lru_cache(maxsize=1)
def sweep() -> dict[str, dict]:
    """{"module.Model": {doc, fields: {name: {type, required, description, source}}}}."""
    result: dict[str, dict] = {}
    for info in pkgutil.iter_modules(_pkg.__path__):
        if info.name == "dictionary":
            continue
        mod = importlib.import_module(f"{_pkg.__name__}.{info.name}")
        comments = _field_comments(mod)
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if not issubclass(cls, BaseModel) or cls.__module__ != mod.__name__:
                continue
            fields = {}
            for fname, f in cls.model_fields.items():
                if f.description:
                    desc, source = f.description, "field"
                elif (name, fname) in comments:
                    desc, source = comments[(name, fname)], "comment"
                else:
                    desc, source = None, None
                fields[fname] = {"type": str(f.annotation), "required": f.is_required(),
                                 "description": desc, "source": source}
            result[f"{info.name}.{name}"] = {"doc": inspect.getdoc(cls) if cls.__doc__ else None, "fields": fields}
    return result


def sweep_stats() -> dict:
    """How well documented the models are, with the worst offenders listed."""
    total = described = 0
    by_model = []
    for key, m in sweep().items():
        n = len(m["fields"])
        d = sum(1 for f in m["fields"].values() if f["description"])
        total, described = total + n, described + d
        by_model.append((key, n, d))
    missing = sorted(((k, n - d) for k, n, d in by_model if n > d), key=lambda x: -x[1])
    return {"models": len(by_model), "fields": total, "described": described,
            "pct_described": round(100 * described / total, 1) if total else 100.0,
            "most_undocumented": [{"model": k, "missing": n} for k, n in missing[:10]]}


def _view_model(view: str):
    from core.schemas.views import VIEW_MODELS
    return VIEW_MODELS.get(view)


def view_notes(view: str) -> dict[str, str]:
    """column -> description for a view, from its registered model ({} if none)."""
    m = _view_model(view)
    if m is None:
        return {}
    return {n: f.description for n, f in m.model_fields.items() if f.description}


def coverage(view_columns: dict[str, list[str]]) -> dict[str, dict]:
    """Per view: documented/undocumented columns and model fields the view no longer has (drift)."""
    out = {}
    for view, cols in view_columns.items():
        m = _view_model(view)
        if m is None:
            out[view] = {"model": None, "undocumented": list(cols)}
            continue
        fields = m.model_fields
        out[view] = {
            "model": m.__name__,
            "documented": [c for c in cols if c in fields and fields[c].description],
            "undocumented": [c for c in cols if c not in fields or not fields[c].description],
            "stale_in_model": [f for f in fields if f not in cols],
        }
    return out
