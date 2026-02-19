#!/usr/bin/env python3
"""Test LLM service timeout and emotion recognition"""

import sys
import asyncio
import time
import os
import logging
logger = logging.getLogger(__name__)

# Add apps/backend to path
backend_path = os.path.join(os.path.dirname(__file__), 'apps/backend')
sys.path.insert(0, backend_path)

from src.services.angela_llm_service import AngelaLLMService, get_llm_service

async def test_llm_timeout():
    """Test LLM service timeout"""
    print("=" * 60)
    print("Testing LLM Service Timeout")
    print("=" * 60)

    # Get service
    service = await get_llm_service()

    # Test 1: Check backend status
    print("\n1. Backend Status:")
    print(f"   Available: {service.is_available}")
    print(f"   Active Backend: {service.active_backend_type.value if service.active_backend_type else 'None'}")
    print(f"   Available Backends: {list(service.backends.keys())}")

    # Test 2: Test response time
    print("\n2. Testing Response Time:")
    test_messages = [
        "你好",
        "今天天气怎么样？",
        "我有点难过",
        "我很开心",
        "你在做什么？"
    ]

    for msg in test_messages:
        start = time.time()
        result = await service.generate_response(msg)
        elapsed = (time.time() - start) * 1000

        print(f"\n   Message: '{msg}'")
        print(f"   Response: '{result.text[:50]}...'")
        print(f"   Backend: {result.backend}")
        print(f"   Response Time: {elapsed:.2f}ms")
        print(f"   Error: {result.error}")

        # Check if it's fallback (indicates timeout)
        if result.backend == "fallback-error":
            print(f"   ⚠️  WARNING: Fallback detected (likely timeout)")
        elif elapsed < 10:
            print(f"   ⚠️  WARNING: Response too fast (likely cache or fallback)")

    # Test 3: Test emotion recognition
    print("\n3. Testing Emotion Recognition:")
    test_emotions = [
        ("我很开心", "happy"),
        ("我很难过", "sad"),
        ("我有点害怕", "fear"),
        ("我很好奇", "curious"),
        ("我不开心", "sad/negative"),
        ("我不难过", "calm/negative"),
        ("好开心", "happy/intensifier"),
        ("太开心了", "happy/intensifier"),
        ("我不开心", "happy/negation"),
    ]

    for text, expected in test_emotions:
        result = service.analyze_emotion(text)
        print(f"\n   Text: '{text}'")
        print(f"   Expected: {expected}")
        print(f"   Detected: {result['emotion']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Intensity: {result['intensity']:.2f}")

        # Check if matches expected
        emotion_type = expected.split('/')[0]
        if result['emotion'] == emotion_type:
            print(f"   ✅ PASS")
        else:
            print(f"   ❌ FAIL")

async def main():
    await test_llm_timeout()

if __name__ == "__main__":
    asyncio.run(main())
