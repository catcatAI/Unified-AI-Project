import asyncio, sys, os, time, logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "backend", "src"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from services.angela_llm_service import get_llm_service

async def main():
    svc = await get_llm_service()
    ok = await svc.initialize()
    print("INIT ok=", ok, "is_available=", svc.is_available, "active_backend=", svc.active_backend_type, "llm_mode=", svc.llm_mode)
    for q in ["what is the capital of Japan", "what is the capital of Japan", "what is 2+2", "hello", "who is the tallest if Alice is taller than Bob"]:
        t = time.time()
        resp = await svc.generate_response(q, context={})
        dt = time.time() - t
        print(f"[{(dt*1000):.0f}ms] q={q!r} -> route={getattr(resp,'route',None)} backend={getattr(resp,'backend',None)} text={resp.text!r}")

asyncio.run(main())
