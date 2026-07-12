#!/usr/bin/env python3
"""CLI runner — bootstraps the unified CLI with fallback mock."""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def _mock_response(command: str, args: argparse.Namespace) -> None:
    """Fallback mock response when CLI modules cannot be imported."""
    if command == "health":
        result = {
            "status": "healthy",
            "version": "7.5.0-dev",
            "services": [
                {"name": "API Server", "status": "active"},
                {"name": "LLM Router", "status": "active"},
                {"name": "Causal Engine", "status": "active"},
                {"name": "Emotion System", "status": "active"},
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"System Status: {result['status']}")
            print(f"Timestamp: {result['timestamp']}")
            print("Services:")
            for svc in result["services"]:
                print(f"  - {svc['name']}: {svc['status']}")
    elif command == "chat":
        result = {
            "response_text": "Mock AI response (CLI modules unavailable).",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"AI Response: {result['response_text']}")
    else:
        print(f"Mock mode does not support command: {command}")


def main():
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    sys.path.insert(0, str(script_dir.parent))

    try:
        from cli.unified_cli import main as cli_main
        cli_main()
        return
    except ImportError:
        pass

    try:
        from cli.__main__ import main as cli_main
        cli_main()
        return
    except ImportError:
        pass

    print("CLI modules unavailable — using fallback mock.")
    parser = argparse.ArgumentParser(description="Unified AI CLI")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("health", help="Check system health")
    sub.add_parser("chat", help="Chat with AI")
    args = parser.parse_args()
    if args.command:
        _mock_response(args.command, args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
