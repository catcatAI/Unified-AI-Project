#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Flatten a volare sky130 SPICE model into a self-contained corner file.

Why
---
The volare PDK expresses its models as ``.param`` definitions in
``parameters/typical.spice`` and ``parameters/invariant.spice``, referenced from
binned ``.model`` cards as ``{expr}``. ngspice cannot resolve those, so a deck
that includes the PDK directly dies with "Cannot compute substitute", and a
caller that works around it by hand-rolling a model loses the binned parameters
that make the device model worth having.

The chip workspace already contains one such flattened file for nfet, produced
this way, and it is the same model the freeze packet's verified measurement came
from. This script extends the approach to pfet so a mixed-signal block (the CIM
sense chain needs both) can be simulated against real corner parameters.

It is deliberately a one-shot, offline tool: it writes a file, and the file is
then included normally.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# ``.param name = value`` possibly continued with ``+ name = value``
_PARAM_LINE = re.compile(r"^\s*\+?\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$")
_PARAM_BLOCK = re.compile(r"^\.param\b", re.IGNORECASE)
# ``{expr}`` substitutions inside model cards
_SUBST = re.compile(r"\{([^{}]+)\}")
# Monte-Carlo process blocks: ``{base + MC_x_SWITCH*RANDOM*(...)}`` or
# ``{MC_x_SWITCH*RANDOM*(...)}``. With MC disabled they must collapse to the
# deterministic base term, or to nothing.
_MC_TOKEN = re.compile(r"\bMC_\w+_SWITCH\b|\bAGAUSS\b|\bAUNIF\b|\bLUNIF\b|\bUNIF\b")
_MC_PREFIX = re.compile(r"^\s*([^{}]*?)\s*\+\s*MC_\w+_SWITCH\b")


def read_params(path: Path) -> Dict[str, str]:
    """Collect ``.param`` assignments from a file, joining ``+`` continuations."""
    params: Dict[str, str] = {}
    current: List[str] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if _PARAM_BLOCK.match(raw):
            current = [raw]
            continue
        if raw.lstrip().startswith("+") and current:
            current.append(raw)
            continue
        for line in current:
            body = line.lstrip().lstrip("+").strip()
            match = _PARAM_LINE.match(body)
            if match:
                params[match.group(1)] = match.group(2)
        current = []
    for line in current:
        match = _PARAM_LINE.match(line.lstrip().lstrip("+").strip())
        if match:
            params[match.group(1)] = match.group(2)
    return params


def collapse_monte_carlo(text: str) -> str:
    """Reduce Monte-Carlo process blocks to their deterministic value.

    The PDK writes process variation as expressions such as
    ``{4.148e-09+MC_MM_SWITCH*AGAUSS(0,1.0,1)*(...)}``. Substituting parameters
    into those leaves an expression full of undefined symbols, and picking the
    first identifier out of it silently corrupts a physics value rather than
    failing: it turned ``toxe`` from 4.148e-09 into 0.003443, and the resulting
    model was rejected by the simulator with nothing pointing at the cause.

    With MC disabled the whole guarded term is zero, so a block that has a
    leading base term reduces to that term and a block that has none reduces to
    zero.
    """

    def replace(match: re.Match[str]) -> str:
        expr = match.group(1)
        if not _MC_TOKEN.search(expr):
            return match.group(0)
        prefix = _MC_PREFIX.match(expr)
        if prefix and prefix.group(1).strip():
            return "{" + prefix.group(1).strip() + "}"
        return "{0.0}"

    previous = None
    current = text
    while previous != current:
        previous = current
        current = _SUBST.sub(replace, current)
    return current


def substitute(text: str, params: Dict[str, str], depth: int = 0) -> str:
    """Resolve ``{name}`` and ``{0+name}`` references until none remain.

    The PDK writes offsets as ``{0+name}`` so that a sign change is visible in
    the source; those are ordinary sums, so stripping the leading numeric term
    and keeping the identifier gives the value directly.
    """
    if depth > 40:
        return text

    def replace(match: re.Match[str]) -> str:
        expr = match.group(1).strip()
        # A brace left over after Monte-Carlo collapse is a pure numeric
        # expression. It has to be tried as a number *first*: scientific
        # notation contains an "e", so a letter test would reject 4.148e-09 and
        # leave it unresolved.
        try:
            # Bare number, no braces: leaving the braces in place would make the
            # replaced text identical to the input, so the reduction loop would
            # exit with the substitution still unresolved.
            return f"{float(eval(expr, {'__builtins__': {}}, {})):.10g}"  # nosec B307
        except (ValueError, ZeroDivisionError, TypeError, SyntaxError, NameError):
            pass
        for name in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr):
            if name in params:
                return params[name]
        return match.group(0)

    replaced = _SUBST.sub(replace, text)
    return substitute(replaced, params, depth + 1) if replaced != text else replaced


def flatten(
    model_files: List[Path],
    param_files: List[Path],
    output: Path,
) -> Tuple[int, List[str]]:
    """Write ``model_files`` with all parameters resolved into ``output``."""
    params: Dict[str, str] = {}
    for path in param_files:
        if path.is_file():
            params.update(read_params(path))
    lines: List[str] = [
        "* Flattened sky130 corner models, generated by flatten_sky130_spice.py",
        "* parameters resolved from: " + ", ".join(p.name for p in param_files),
        f"* parameter count: {len(params)}",
        "",
    ]
    cards = 0
    unresolved: List[str] = []
    for model in model_files:
        if not model.is_file():
            continue
        raw_text = model.read_text(encoding="utf-8", errors="replace")
        in_card = False
        for raw in collapse_monte_carlo(raw_text).splitlines():
            text = substitute(raw, params)
            for missing in _SUBST.findall(text):
                if missing not in unresolved:
                    unresolved.append(missing)
            if text.strip().lower().startswith(".model"):
                in_card = True
                cards += 1
            elif in_card:
                # A model card runs on "+" continuations and may carry "*"
                # comments between them -- the PDK puts a banner comment right
                # after the .model line. Dropping those comments ends the card
                # early, and then every "+" parameter line after it is discarded
                # too, which yields a card with a name and no physics: the
                # simulator then reports "could not find a valid modelname"
                # because the surviving header carries no binning at all.
                stripped = text.lstrip()
                if stripped.startswith("+") or stripped.startswith("*"):
                    lines.append(text)
                    continue
                in_card = False
                continue
            else:
                # The PDK also ships .subckt wrappers whose device lines
                # reference {l}, {w}, {ad} and friends. Those are neither
                # needed for a primitive-level deck nor resolvable offline, and
                # leaving them in makes the simulator discard the .model cards
                # beside them. The known-good flattened reference contains
                # nothing but model cards.
                continue
            lines.append(text)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return cards, unresolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="+", required=True, help="binned .model card files")
    parser.add_argument("--params", nargs="*", default=[], help="parameter definition files")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    cards, unresolved = flatten(
        [Path(item) for item in args.models],
        [Path(item) for item in args.params],
        args.out,
    )
    print(f"wrote {args.out} with {cards} model cards")
    if unresolved:
        print(f"WARNING: {len(unresolved)} unresolved substitutions, first few:")
        for name in unresolved[:10]:
            print(f"  {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
