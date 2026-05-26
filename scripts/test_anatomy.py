import asyncio
from services.tactile_service import TactileService

async def test_anatomy():
    service = TactileService()
    parts = ["head", "cheeks", "chest", "shoulders"]
    print("--- 檢查 Angela 的感官映射 ---")
    for part in parts:
        res = await service.simulate_touch("test_check", {"body_part": part, "pressure": 0.9})
        print(f"刺激部位: {part} -> 反應: {res['reflex']}")

if __name__ == "__main__":
    asyncio.run(test_anatomy())
