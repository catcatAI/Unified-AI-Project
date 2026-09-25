#!/usr/bin/env python3

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/backend/src"))

from ai.agents.specialized.eda_agent import EdaAgent
from core.tools.eda_tool_adapter import EdaToolAdapter


async def run(rounds: int, output_root: str, clock_mhz: float | None) -> dict:
    agent = EdaAgent(
        agent_id="mvu_reference_cli",
        adapter=EdaToolAdapter(output_root=output_root),
    )
    return await agent.run_mvu_reference_experiment(rounds=rounds, clock_mhz=clock_mhz)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the software-only MVU reference model")
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--output-root", default="data/eda_runs")
    parser.add_argument("--clock-mhz", type=float)
    args = parser.parse_args()
    result = asyncio.run(run(args.rounds, args.output_root, args.clock_mhz))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
