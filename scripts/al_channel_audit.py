#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L3]
# =============================================================================
"""Where does AL state reach generation, and how much of it survives the trip?

"AI + AL in one model" and "AI + AL as a prompt paragraph" look the same from the
outside: both change the reply when the state changes. They are not the same
thing, and the difference is not cosmetic:

* **B (prompt text)** — the state is serialised into the prompt. The model can
  *read* it, can *ignore* it, and a third party can *recover* it from the
  transcript. It is evidence shown to the model, not a property of the model.
* **C-param** — the state sets sampling parameters (temperature, max_tokens).
  The model cannot read it and cannot ignore it, but it also does not know it:
  the state acts on the distribution, not on the model.
* **C-logit** — the state biases token logits or adds a steering vector. Same
  status as C-param with finer resolution; still outside the weights.
* **C-state** — the state is carried in the model's own recurrence (a hidden
  state that persists and evolves). This is the only route where "one model"
  is literally true, and the only one where a restart test is meaningful for
  the *model* rather than for a file beside it.

The audit reports which of these exist in this repo, where, and at what
resolution — measured, not asserted: the prompt route's resolution is the number
of distinct values its format can print, and the sampling route's is the number
of distinct temperatures the negotiator can actually produce over the health
range. A channel with resolution 1 is a constant and should not be described as
"coupling".

What no channel can settle on its own: a state *injector* can reproduce B and
C-param exactly (write the text; set the temperature). So route choice answers
"is the model reading a sentence", not "is this alive". The life claim needs the
ladder (does the state evolve with time by itself) and provenance (which code
path produced the value) on top of whichever channel is used.

Usage:
    ./.venv/bin/python scripts/al_channel_audit.py
    ./.venv/bin/python scripts/al_channel_audit.py --report data/intelligence_reports/al_channels.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "backend" / "src"))

# Audit is static where possible: importing services.llm.router pulls the whole
# LLM stack (and possibly torch through a backend), which is exactly what a
# single-process XPU constraint cannot afford.

PROMPT_DECIMALS = 4  # services/llm/prompt_builder.py: _formula_life_intensity_line
HB_NEUTRAL = 0.5  # ai/meta/priority_negotiator.py
HB_BIAS_SCALE = 2.0
HB_UNHEALTHY = 0.3
HB_TEMP_SCALE = 0.5
HB_TOKENS_SCALE = 50
TEMP_MIN, TEMP_MAX = 0.1, 1.5  # services/llm/router.py: _apply_negotiator_bias
DEFAULT_TEMPERATURE = 0.7


def text_resolution(decimals: int = PROMPT_DECIMALS) -> int:
    """Distinct printed values of a [0, 1] quantity at the prompt's precision."""
    return 10**decimals + 1


def text_token_cost(decimals: int = PROMPT_DECIMALS) -> int:
    """Characters spent per value (`0.` + digits). Tokens are >= this / 4 for BPE
    and >= 1 per digit for the char-level tokenizer used by token_snn, so the
    honest statement is a range, not a number."""
    return 2 + decimals


def param_resolution(step: float = 1e-4) -> Dict[str, object]:
    """Distinct (routing_mode, temperature, max_tokens) the AL voters can cause.

    Reimplements the two production formulas from their constants rather than
    importing them, because the formula *is* the channel: health_bias rounds to
    3 decimals, so the resolution is decided by that rounding, not by the float.
    """
    temps = set()
    modes = set()
    tokens = set()
    steps = int(round(1.0 / step))
    for i in range(steps + 1):
        health = i * step
        health_bias = round((health - HB_NEUTRAL) * HB_BIAS_SCALE, 3)
        temp_bias = health_bias * HB_TEMP_SCALE
        tokens_bias = int(health_bias * HB_TOKENS_SCALE)
        mode = "conservative" if health < HB_UNHEALTHY else "neutral"
        temps.add(round(min(max(DEFAULT_TEMPERATURE + temp_bias, TEMP_MIN), TEMP_MAX), 6))
        tokens.add(max(128, min(1024, 512 + tokens_bias)))
        modes.add(mode)
    return {
        "distinct_temperatures": len(temps),
        "temperature_range": [min(temps), max(temps)],
        "distinct_max_tokens": len(tokens),
        "distinct_modes": len(modes),
        "modes": sorted(modes),
    }


def _channel(
    name: str,
    route: str,
    where: Optional[str],
    notes: str,
    resolution: Optional[int],
    readable: bool,
    ignorable: bool,
    injectable: bool,
) -> Dict[str, object]:
    return {
        "channel": name,
        "route": route,
        "where": where,
        "notes": notes,
        "resolution": resolution,
        "model_can_read_it": readable,
        "model_can_ignore_it": ignorable,
        "reproducible_by_an_injector": injectable,
        "implemented": where is not None and (resolution or 0) > 0,
    }


def audit() -> Dict[str, object]:
    channels: List[Dict[str, object]] = [
        _channel(
            "prompt_text",
            "B",
            "services/llm/prompt_builder.py:_formula_life_intensity_line",
            f"AL intensity printed as f'{{value:.{PROMPT_DECIMALS}f}}' into the prompt",
            text_resolution(),
            readable=True,
            ignorable=True,
            injectable=True,
        ),
        _channel(
            "sampling_param",
            "C-param",
            "services/llm/router.py:_apply_negotiator_bias <- "
            "ai/meta/priority_negotiator.py:heartbeat_voter,dli_state_voter",
            "AL health/lifecycle -> temperature_bias, tokens_bias -> generation params",
            param_resolution()["distinct_temperatures"],
            readable=False,
            ignorable=False,
            injectable=True,
        ),
        _channel(
            "logit_bias",
            "C-logit",
            None,
            "no code path biases logits or adds a steering vector from AL state",
            0,
            readable=False,
            ignorable=False,
            injectable=True,
        ),
        _channel(
            "model_state",
            "C-state",
            None,
            "no generation path carries AL state inside a recurrent model state",
            0,
            readable=False,
            ignorable=False,
            injectable=True,
        ),
        _channel(
            "routing",
            "routing",
            "services/llm/router.py:4434 context['al_state'] -> PriorityNegotiator voters",
            "selects which path answers; not a property of the generation itself",
            param_resolution()["distinct_modes"],
            readable=False,
            ignorable=False,
            injectable=True,
        ),
    ]

    implemented = [c["channel"] for c in channels if c["implemented"]]
    text = next(c for c in channels if c["channel"] == "prompt_text")
    return {
        "channels": channels,
        "summary": {
            "implemented": implemented,
            "prompt_route_resolution": text["resolution"],
            "sampling_route_resolution": param_resolution()["distinct_temperatures"],
            "sampling_route_range": param_resolution()["temperature_range"],
            "prompt_route_chars_per_value": text_token_cost(),
            "literal_one_model_route": "model_state",
            "one_model_implemented": False,
            "note": (
                "B and C-param are both reproducible by an injector, so neither "
                "settles real-vs-fake; the route answers whether the model reads a "
                "sentence, while the ladder answers whether the state evolves by itself"
            ),
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="AL->generation channel audit")
    ap.add_argument("--report", type=str, default="")
    args = ap.parse_args()

    result = audit()
    print(f"{'channel':<14}{'route':<10}{'resolution':>11}  read ignore inject  where")
    for c in result["channels"]:
        res = c["resolution"] if c["resolution"] is not None else 0
        flags = "".join(
            "  Y " if c[k] else "  . "
            for k in ("model_can_read_it", "model_can_ignore_it", "reproducible_by_an_injector")
        )
        print(
            f"{c['channel']:<14}{c['route']:<10}{res:>11}{flags}  {c['where'] or '(not implemented)'}"
        )
    s = result["summary"]
    print()
    print("implemented:", ", ".join(s["implemented"]))
    print(
        f"resolution: prompt {s['prompt_route_resolution']} values "
        f"({s['prompt_route_chars_per_value']} chars each) vs "
        f"temperature {s['sampling_route_resolution']} values "
        f"{s['sampling_route_range']}"
    )
    print("literal 'one model' route implemented:", s["one_model_implemented"])
    if args.report:
        out = ROOT / args.report
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("report:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
