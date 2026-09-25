"""
Whole-API shadowing audit.

A declared endpoint is unreachable when an *earlier* route with a path parameter
matches its path first — Starlette resolves in declaration order. This class of
bug is invisible to handler-level tests (which call the coroutine directly) and
to "the route exists" assertions, because the route object really is registered;
only real resolution shows the truth.

Live example this was written for: ``/review/{dimension}`` declared above
``/review/score`` and ``/review/summary`` made both answer HTTP 400
"Unknown review dimension" while being documented as live.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "apps/backend/src"))


def _iter_routes(routes) -> List:
    """Flatten nested routers into a flat, declaration-ordered list of APIRoutes.

    FastAPI 0.14x wraps every ``include_router`` call in a ``_IncludedRouter``
    whose sub-routes live on ``original_router.routes`` (and are themselves
    wrapped, since api/router.py includes ~19 sub-routers). Naively reading
    ``route.routes`` finds nothing — that produced a vacuous audit that "passed"
    while only ever seeing ``/health``.
    """
    from fastapi.routing import APIRoute

    flat: List[APIRoute] = []
    for route in routes:
        if isinstance(route, APIRoute):
            flat.append(route)
            continue
        # _IncludedRouter (and any future wrapper): recurse into the original
        # router, preserving the order the app mounted things in.
        original = getattr(route, "original_router", None)
        if original is not None:
            flat.extend(_iter_routes(original.routes))
            continue
        for sub in getattr(route, "routes", None) or []:
            flat.extend(_iter_routes([sub]))
    return flat


def _paths_of(routes) -> Dict[str, List]:
    """Map path -> [(method, endpoint_name, declared_index)]."""
    out: Dict[str, List[Tuple[str, str, int]]] = {}
    for index, route in enumerate(_iter_routes(routes)):
        if "{" in route.path:
            continue  # parameterized routes are handled separately
        methods = sorted(m for m in (route.methods or set()) if m not in ("HEAD", "OPTIONS"))
        for method in methods:
            out.setdefault(route.path, []).append((method, route.endpoint.__name__, index))
    return out


def _resolver(routes):
    from starlette.routing import Match

    def resolve(path: str, method: str):
        for route in routes:
            matched, _ = route.matches(
                {"type": "http", "path": path, "root_path": "", "method": method, "headers": []}
            )
            if matched is Match.FULL:
                return route
        return None

    return resolve


@pytest.fixture(scope="module")
def app_routes():
    from services.main_api_server import app

    return _iter_routes(app.router.routes)


class TestNoShadowedEndpoints:
    def test_every_declared_endpoint_actually_serves_itself(self, app_routes):
        """Each literal path must be answered by the endpoint that declared it."""
        resolve = _resolver(app_routes)
        shadowed = []
        for path, declarations in _paths_of(app_routes).items():
            probe = path if path.endswith("/") or "." not in path.rsplit("/", 1)[-1] else path
            for method, endpoint_name, _ in declarations:
                served = resolve(probe, method)
                if served is None:
                    continue  # a 404 for an otherwise-unmatched shape is fine
                if served.endpoint.__name__ != endpoint_name:
                    shadowed.append(
                        f"{method} {path} declared by {endpoint_name}() "
                        f"but served by {served.endpoint.__name__}()"
                    )
        assert not shadowed, "shadowed endpoints (unreachable despite being declared):\n" + "\n".join(
            sorted(shadowed)
        )

    def test_parameterized_routes_are_declared_after_literals(self, app_routes):
        """Structural guard: a {param} route must not precede a literal it can match.

        Two paths can only collide when they have the same segment count and the
        parameterized route's fixed segments are identical to the literal's — e.g.
        ``/review/*`` can shadow ``/review/score`` but can never shadow
        ``/plugins/*/enable`` for ``/drive/files/sync`` (first segment differs).
        Comparing only segment counts produced ~40 false positives across
        unrelated routers.
        """
        literals: List[Tuple[int, str, Tuple[str, ...], str]] = []
        parameterized: List[Tuple[int, str, Tuple[str, ...], str]] = []
        for index, route in enumerate(app_routes):
            methods = getattr(route, "methods", None)
            if not methods:
                continue
            method_key = next(
                (m for m in sorted(methods) if m not in ("HEAD", "OPTIONS")), ""
            )
            shape = tuple(
                "*" if "{" in seg else seg for seg in route.path.strip("/").split("/")
            )
            if not shape or not method_key:
                continue
            entry = (index, method_key, shape, route.path)
            (parameterized if "{" in route.path else literals).append(entry)

        def can_shadow(param_shape, lit_shape) -> bool:
            if len(param_shape) != len(lit_shape):
                return False
            return all(p == "*" or p == lit for p, lit in zip(param_shape, lit_shape))

        # Shadowing happens when the {param} route is declared FIRST; a literal
        # declared before it is the correct order and must not be flagged.
        offenders = []
        for p_index, p_method, p_shape, p_path in parameterized:
            for lit_index, lit_method, lit_shape, lit_path in literals:
                if lit_method != p_method or p_index >= lit_index:
                    continue
                if can_shadow(p_shape, lit_shape):
                    offenders.append(
                        f"{lit_method} {lit_path} (index {lit_index}) is shadowed by "
                        f"{p_path} (index {p_index})"
                    )
        assert not offenders, "literal routes declared after a {param} route that can match them:\n" + "\n".join(
            sorted(set(offenders))
        )
