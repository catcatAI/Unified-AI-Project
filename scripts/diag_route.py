import sys
import os
import asyncio
sys.path.insert(0, "D:/Projects/Unified-AI-Project/apps/backend/src")
import httpx

async def main():
    async with httpx.AsyncClient(timeout=60) as c:
        for q in ["what is 2+2", "what is the capital of Japan", "hello",
                  "who is the tallest if Alice is taller than Bob",
                  "what is the opposite of hot", "what color is the sky",
                  "what does a cat say", "tell me a joke"]:
            r = await c.post("http://127.0.0.1:8000/api/v1/chat/unified",
                             json={"message": q, "user_name": "tester", "session_id": "s1"})
            j = r.json()
            b = j.get("backend")
            m = j.get("model")
            rt = j.get("route")
            cf = j.get("confidence")
            txt = str(j.get("response"))[:45]
            print(f"{q!r:52} backend={b!r:14} model={m!r:14} route={rt!r:10} conf={cf} -> {txt!r}")

asyncio.run(main())
