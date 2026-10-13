#!/usr/bin/env python3
"""AI Models CLI — multi-LLM command-line interface."""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AIModelsCLI:
    """AI Models CLI interface."""

    def __init__(self) -> None:
        self.service: Optional[Any] = None

    async def initialize(self) -> None:
        _root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if _root not in sys.path:
            sys.path.insert(0, _root)
        _backend = os.path.join(_root, "apps", "backend")
        if _backend not in sys.path:
            sys.path.insert(0, _backend)

        from apps.backend.src.services.angela_llm_service import AngelaLLMService

        # AngelaLLMService uses tiered config system (no config_path needed)
        self.service = AngelaLLMService()
        await self.service.initialize()
        logger.info("AI model service initialized")

    async def list_models(self) -> None:
        if not self.service:
            await self.initialize()
        models = self.service.get_available_models()
        print("\nAvailable AI Models:")
        print("=" * 60)
        for model_id in models:
            info = self.service.get_model_info(model_id)
            status = "enabled" if info.get("enabled") else "disabled"
            print(f"\n  {model_id}")
            print(f"    Provider:    {info.get('provider', '?')}")
            print(f"    Model:       {info.get('model_name', '?')}")
            print(f"    Status:      {status}")
            print(f"    Max tokens:  {info.get('max_tokens', '?')}")
            print(f"    Cost/1K:     ${info.get('cost_per_1k_tokens', 0):.4f}")
            stats = info.get("usage_stats", {})
            if stats.get("total_requests", 0) > 0:
                print(f"    Requests:    {stats['total_requests']}")
                print(f"    Total cost:  ${stats.get('total_cost', 0):.4f}")
                print(f"    Avg latency: {stats.get('average_latency', 0):.2f}s")

    async def health_check(self) -> None:
        if not self.service:
            await self.initialize()
        print("Checking model health...")
        health_status = await self.service.health_check()
        for model_id, status in health_status.items():
            if status.get("status") == "healthy":
                print(f"  OK  {model_id} ({status.get('latency', 0):.2f}s)")
            elif status.get("status") == "disabled":
                print(f"  --  {model_id} disabled")
            else:
                print(f"  FAIL {model_id}: {status.get('error', 'unknown')}")

    async def usage_stats(self) -> None:
        if not self.service:
            await self.initialize()
        summary = self.service.get_usage_summary()
        print(f"\nTotal requests: {summary['total_requests']}")
        print(f"Total tokens:   {summary['total_tokens']}")
        print(f"Total cost:     ${summary['total_cost']:.4f}")
        print(f"Total errors:   {summary['total_errors']}")
        for model_id, info in summary.get("models", {}).items():
            stats = info.get("usage_stats", {})
            if stats.get("total_requests", 0) > 0:
                print(
                    f"  {model_id}: {stats['total_requests']} req, "
                    f"${stats.get('total_cost', 0):.4f}, "
                    f"{stats.get('average_latency', 0):.2f}s avg"
                )

    async def _emit_response(
        self,
        messages: List[Any],
        model_id: str,
        max_tokens: int,
        temperature: float,
        stream: bool,
    ) -> Tuple[Any, str]:
        """Print one completion and return ``(response, text)``.

        ``--stream`` used to call ``self.service.stream_completion()``
        unconditionally, but ``AngelaLLMService`` never implemented it — every
        ``--stream`` invocation died with AttributeError. Probe for the method
        and degrade to buffered ``chat_completion`` instead, matching the
        guarded fallback already used by ``ModelEnsemble.streaming_ensemble``.

        ``response`` is None on the streamed path (there is no single response
        object); ``text`` always carries the assistant's reply so callers can
        keep the conversation history intact either way.
        """
        stream_method = getattr(self.service, "stream_completion", None)
        if stream and callable(stream_method):
            chunks: List[str] = []
            async for chunk in stream_method(
                messages, model_id=model_id, max_tokens=max_tokens, temperature=temperature
            ):
                chunks.append(str(chunk))
                print(chunk, end="", flush=True)
            print()
            return None, "".join(chunks)
        if stream:
            print(
                "[stream] stream_completion() unavailable on this service; "
                "using buffered output",
                file=sys.stderr,
            )
        response = await self.service.chat_completion(
            messages, model_id=model_id, max_tokens=max_tokens, temperature=temperature
        )
        print(response.content)
        return response, response.content

    async def single_query(
        self,
        query: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
        verbose: bool = False,
    ) -> None:
        if not self.service:
            await self.initialize()
        model_id = model or self.service.default_model()
        from apps.backend.src.services.angela_llm_service import ChatMessage

        messages: List[Any] = []
        if system:
            messages.append(ChatMessage(role="system", content=system))
        messages.append(ChatMessage(role="user", content=query))
        response, _text = await self._emit_response(
            messages, model_id, max_tokens, temperature, stream
        )
        if verbose and response is not None:
            print(
                f"\nTokens: {getattr(response, 'usage', {})}  "
                f"Cost: ${getattr(response, 'cost', 0):.4f}  "
                f"Latency: {getattr(response, 'latency', 0):.2f}s"
            )

    async def chat(
        self,
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
        verbose: bool = False,
    ) -> None:
        if not self.service:
            await self.initialize()
        model_id = model or self.service.default_model()
        from apps.backend.src.services.angela_llm_service import ChatMessage

        messages: List[Any] = []
        if system:
            messages.append(ChatMessage(role="system", content=system))
        print(f"Chat with {model_id} (type 'quit' to exit)")
        while True:
            try:
                user_input = input("\n>>> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if user_input.lower() in ("quit", "exit", "q"):
                break
            if user_input.lower() in ("clear", "c"):
                messages.clear()
                if system:
                    messages.append(ChatMessage(role="system", content=system))
                print("History cleared")
                continue
            if not user_input:
                continue
            messages.append(ChatMessage(role="user", content=user_input))
            response, text = await self._emit_response(
                messages, model_id, max_tokens, temperature, stream
            )
            if verbose and response is not None:
                print(
                    f"\nTokens: {getattr(response, 'usage', {})}  "
                    f"Cost: ${getattr(response, 'cost', 0):.4f}  "
                    f"Latency: {getattr(response, 'latency', 0):.2f}s"
                )
            # The streamed path used to drop the turn entirely, so every later
            # request saw only user messages. Record it either way.
            if text:
                messages.append(ChatMessage(role="assistant", content=text))

    async def compare_models(
        self,
        query: str,
        models: Optional[List[str]] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        verbose: bool = False,
    ) -> None:
        if not self.service:
            await self.initialize()
        model_ids = models or self.service.get_available_models()[:3]
        from apps.backend.src.services.angela_llm_service import ChatMessage

        print(f"Comparing: {query}")
        results = []
        for model_id in model_ids:
            try:
                messages = [ChatMessage(role="user", content=query)]
                response = await self.service.chat_completion(
                    messages, model_id=model_id, max_tokens=max_tokens, temperature=temperature
                )
                results.append(
                    {
                        "model": model_id,
                        "response": response.content,
                        "usage": getattr(response, "usage", {}),
                        "cost": getattr(response, "cost", 0),
                        "latency": getattr(response, "latency", 0),
                    }
                )
                print(f"\n--- {model_id} ---")
                print(response.content[:500])
            except Exception as e:
                print(f"  {model_id} failed: {e}")
                logger.warning("Model %s comparison failed: %s", model_id, e)

        if verbose and results:
            print("\nSummary:")
            for r in results:
                print(f"  {r['model']}: ${r['cost']:.4f}  {r['latency']:.2f}s")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Models CLI")
    sub = parser.add_subparsers(dest="command", help="sub-command")
    sub.add_parser("list", help="List available models")
    hp = sub.add_parser("health", help="Health check")
    hp = sub.add_parser("stats", help="Usage statistics")
    qp = sub.add_parser("query", help="Single query")
    qp.add_argument("query", help="Query text")
    qp.add_argument("--model", "-m", help="Model ID")
    qp.add_argument("--system", "-s", help="System prompt")
    qp.add_argument("--max-tokens", type=int, default=4096)
    qp.add_argument("--temperature", type=float, default=0.7)
    qp.add_argument("--stream", action="store_true")
    qp.add_argument("--verbose", "-v", action="store_true")
    cp = sub.add_parser("chat", help="Interactive chat")
    cp.add_argument("--model", "-m", help="Model ID")
    cp.add_argument("--system", "-s", help="System prompt")
    cp.add_argument("--max-tokens", type=int, default=4096)
    cp.add_argument("--temperature", type=float, default=0.7)
    cp.add_argument("--stream", action="store_true")
    cp.add_argument("--verbose", "-v", action="store_true")
    comp = sub.add_parser("compare", help="Compare models")
    comp.add_argument("query", help="Query text")
    comp.add_argument("--models", nargs="+", help="Model IDs")
    comp.add_argument("--max-tokens", type=int, default=1024)
    comp.add_argument("--temperature", type=float, default=0.7)
    comp.add_argument("--verbose", "-v", action="store_true")
    return parser


async def main() -> None:
    parser = create_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    cli = AIModelsCLI()
    try:
        if args.command == "list":
            await cli.list_models()
        elif args.command == "health":
            await cli.health_check()
        elif args.command == "stats":
            await cli.usage_stats()
        elif args.command == "query":
            await cli.single_query(
                args.query,
                model=args.model,
                system=args.system,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                stream=args.stream,
                verbose=args.verbose,
            )
        elif args.command == "chat":
            await cli.chat(
                model=args.model,
                system=args.system,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                stream=args.stream,
                verbose=args.verbose,
            )
        elif args.command == "compare":
            await cli.compare_models(
                args.query,
                models=args.models,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                verbose=args.verbose,
            )
        else:
            parser.print_help()
    finally:
        if cli.service:
            await cli.service.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
