import asyncio
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "apps" / "backend" / "src"
sys.path.insert(0, str(SRC_PATH))

# Note: HybridBrain class does not exist in the current codebase.
# The script's LLM analysis functionality requires re-implementation.
from ai.memory.vector_store import VectorMemoryStore as VectorStore


async def main():
    # HybridBrain 在目前程式庫裡並不存在（見檔頭註解），這個腳本從
    # 2026-09 起就無法執行，但 scripts/ACTIVE_SCRIPTS.md 仍列它為 active，
    # 於是每次執行都第 24 行以難懂的 NameError 收場。這裡改成明確的前置
    # 檢查，讓失敗原因一眼可見（audit 2026-10-12）。
    raise SystemExit(
        "[ABORT] analyze_roadmap_from_logs.py requires HybridBrain, which does "
        "not exist in this codebase. The LLM-analysis path needs "
        "re-implementation (or the entry removed from scripts/ACTIVE_SCRIPTS.md)."
    )


async def _legacy_analyze(brain):
    """從日誌萃取 roadmap 的主流程。

    brain 以參數傳入而非自己 new：HybridBrain 尚未實作，寫成
    `brain = HybridBrain()` 只會得到一個未知名稱。等 HybridBrain 落地，
    由 main() 建好實例後呼叫即可，不必改動下面的分析邏輯。
    """
    print("[INFO] Initializing Brain and Memory...")
    # Force real LLM for analysis
    os.environ["USE_MOCK_LLM"] = "false"

    # We use the Brain's chat capability which likely uses the Orchestrator or direct RAG?
    # Actually, let's use the VectorStore directly to get chunks, then Brain to summarize.
    # But HybridBrain might not have a direct "summarize this list of chunks" method exposed easily
    # without going through the whole chat pipeline.
    #
    # Let's use the `retrieve_relevant_memories` from HAM (via VectorStore) and then prompt the Brain.

    store = VectorStore()
    # Note: store loads from disk, which might take time if not already loaded by a running backend.
    # But here we are a standalone script, so we load it independently.

    categories = [
        {
            "topic": "Project Goals & Philosophy",
            "query": "What are the core goals, philosophy, and ultimate vision of the Unified AI Project mentioned in the logs?",
        },
        {
            "topic": "Desktop Pet Features",
            "query": "What specific features, appearance, or behaviors are requested for the Desktop Pet (Angelica/Angela)?",
        },
        {
            "topic": "Economic System",
            "query": "Details about the Economic System: tokens, consumption, work, earning logic?",
        },
        {
            "topic": "Self-Evolution & Learning",
            "query": "How should the AI learn, evolve, and improve itself over time according to the logs?",
        },
        {
            "topic": "Immediate Next Steps",
            "query": "What are the suggested immediate next steps or todo items found in the conversation history?",
        },
    ]

    report_lines = ["# Development Roadmap & Insights (Derived from Activity Logs)\n"]

    print("[INFO] Starting Deep Analysis of Logs...")

    for cat in categories:
        topic = cat["topic"]
        query = cat["query"]
        print(f"\n--- Analyzing: {topic} ---")

        # 1. Retrieve raw chunks
        print(f"    Searching Vector Store for: '{query}'")
        # Increase top_k to get a broad context
        results = await store.query_memories(query_text=query, top_k=10)

        if not results:
            print("    [WARN] No relevant memories found.")
            report_lines.append(f"## {topic}\n*No relevant data found in logs.*\n")
            continue

        # 2. Synthesize with LLM
        context_str = "\n".join([f"- {r['document']}" for r in results])

        prompt = f"""
        You are a Technical Project Manager analyzing user activity logs.

        Context from User Logs:
        {context_str}

        Task:
        Synthesize a detailed summary for the topic: "{topic}".
        Focus on concrete technical requirements, design decisions, and philosophical pillars mentioned.
        Ignore general chitchat.

        Output format: Markdown bullet points.
        """

        print("    Synthesizing insights with LLM...")
        # We use brain.api_client or raw provider if accessible?
        # HybridBrain doesn't expose raw generation easily.
        # Let's assume we can use the chat interface but it might interpret it as a chat.
        # Better: Instantiate the provider directly or use a simple hack.
        # Actually `brain.chat()` with a system prompt override is best if supported.
        # But HybridBrain is complex.
        # Let's try to use `brain.providers['ollama'].generate(prompt)` if available.

        response_text = "Analysis Failed"

        try:
            # Check provider availability (provider definition is implicit in brain.class_a_provider)
            provider = brain.class_a_provider

            if provider:
                response_text = await provider.generate(prompt)
                if not response_text:
                    response_text = "LLM Generation returned empty. (Ollama might be down)"
            else:
                response_text = "No LLM Provider available."

        except Exception as e:
            print(f"    [ERROR] LLM Generation failed: {e}")
            response_text = f"Error generating summary: {e}"

        print("    Done.")
        report_lines.append(
            f"## {topic}\n### AI Summary\n{response_text}\n\n### Raw Stored Memories (Context)\n{context_str}\n"
        )

    # Save Report
    output_path = PROJECT_ROOT / "docs" / "01-summaries-and-reports" / "ROADMAP_FROM_LOGS.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n[SUCCESS] Roadmap Analysis saved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
