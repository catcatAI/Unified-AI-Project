"""
與 Angela 的對話測試（支援 Ollama / Google Gemini）
"""
import os, sys, asyncio, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

SRC = str(Path("apps/backend/src").resolve())
if SRC not in sys.path:
    sys.path.insert(0, SRC)

dotenv = Path(".env")
if dotenv.exists():
    for line in dotenv.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

MESSAGES = [
    "你好 Angela！我對天文學很感興趣，特別是黑洞。你能跟我聊聊這個話題嗎？",
    "我聽說黑洞的事件視界是無法返回的邊界，那在超越事件視界之後，時間和空間會發生什麼變化？",
    "史瓦西半徑是怎麼計算的？如果太陽變成黑洞，它的史瓦西半徑會有多大？",
    "那如果地球變成黑洞，史瓦西半徑大概是多少？我記得可以用公式 R = 2GM/c² 來算。",
    "所以黑洞其實不是洞，而是一個密度極高的天體？那霍金輻射又是怎麼回事？",
    "對了，我叫小明，我最喜歡的天體是獵戶座星雲。你有記住我的資訊嗎？",
    "那我剛剛說我最喜歡的天體是什麼？還有我叫什麼名字？",
    "Angela，聊了這麼多天文學，你自己對宇宙有什麼感覺或想法嗎？你喜歡這些話題嗎？",
    "幫我計算 2 的 10 次方是多少？",
]


async def build_ollama_cfg():
    key = os.environ.get("OLLAMA_API_KEY", "")
    return {
        "ollama-local": {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model_name": "qwen3.5:0.8b",
            "api_key": key,
            "enabled": True,
            "timeout": 120,
        },
        "llm_mode": "standard",
        "_routing_policy": {},
        "_fallback_chain": [],
        "_intent_routing": {},
    }


async def build_gemini_cfg():
    key = os.environ.get("GEMINI_API_KEY", "")
    return {
        "google-gemini": {
            "provider": "google",
            "model_name": "gemini-3.1-flash-lite",
            "api_key": key,
            "enabled": True,
        },
        "llm_mode": "standard",
        "_routing_policy": {},
        "_fallback_chain": [],
        "_intent_routing": {},
    }


async def main():
    import aiohttp

    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        try:
            async with aiohttp.ClientSession() as s:
                hdrs = {"Content-Type": "application/json"}
                body = '{"contents":[{"parts":[{"text":"ping"}]}]}'
                r = await s.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={gemini_key}",
                    headers=hdrs, data=body, timeout=aiohttp.ClientTimeout(total=10),
                )
                if r.status == 200:
                    cfg = await build_gemini_cfg()
                    label = "Google Gemini 3.1 Flash Lite"
                else:
                    cfg = await build_ollama_cfg()
                    label = "Ollama (Gemini unavailable)"
        except Exception:
            cfg = await build_ollama_cfg()
            label = "Ollama (Gemini unavailable)"
    else:
        cfg = await build_ollama_cfg()
        label = "Ollama"

    from services.angela_llm_service import AngelaLLMService

    llm = AngelaLLMService(cfg)
    ok = await llm.initialize()
    backend = llm.active_backend_type.value if llm.active_backend else "none"
    print(f"LLM 後端: {backend} | 可用: {ok}")
    if not ok:
        print("❌ LLM 不可用")
        return

    from services.chat_service import AngelaChatService

    chat = AngelaChatService()
    await chat.initialize()

    print(f"\n{'='*70}")
    print(f"🔥 {label}")
    print(f"{'='*70}")

    for i, msg in enumerate(MESSAGES, 1):
        try:
            resp = await chat.generate_response(msg, "天文学爱好者")
            print(f"\n--- Round {i} ---")
            print(f"👤: {msg}")
            print(f"🤖: {resp}")
        except Exception as e:
            import traceback
            print(f"\n--- Round {i} ---")
            print(f"👤: {msg}")
            print(f"💥: {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(main())
