"""Quick test to verify response system imports"""

print("Testing imports...")

try:
    from apps.backend.src.ai.response.template_matcher import TemplateMatcher
    print("✓ TemplateMatcher imported successfully")
except Exception as e:
    print(f"✗ TemplateMatcher import failed: {e}")

try:
    from apps.backend.src.ai.response.composer import ResponseComposer
    print("✓ ResponseComposer imported successfully")
except Exception as e:
    print(f"✗ ResponseComposer import failed: {e}")

try:
    from apps.backend.src.ai.response.deviation_tracker import DeviationTracker
    print("✓ DeviationTracker imported successfully")
except Exception as e:
    print(f"✗ DeviationTracker import failed: {e}")

print("\n--- Quick functionality test ---")

try:
    matcher = TemplateMatcher()
    matcher.add_template(
        template_id="test_1",
        content="你好",
        patterns=["你好"],
        keywords=["你好"],
    )
    result = matcher.match("你好")
    print(f"✓ Template matching works: score={result.score}")
except Exception as e:
    print(f"✗ Template matching failed: {e}")

try:
    composer = ResponseComposer()
    response = composer.compose_response("你好", 0.9, {})
    print(f"✓ Response composition works: {response.text[:20]}...")
except Exception as e:
    print(f"✗ Response composition failed: {e}")

try:
    from apps.backend.src.ai.response.deviation_tracker import ResponseRoute
    tracker = DeviationTracker()
    tracker.record(
        user_input="test",
        match_score=0.9,
        route=ResponseRoute.COMPOSED,
        response_text="test response",
        tokens_used=50,
        response_time_ms=5.0,
    )
    print(f"✓ Deviation tracking works: {tracker.stats['total_responses']} responses tracked")
except Exception as e:
    print(f"✗ Deviation tracking failed: {e}")

print("\nAll tests completed!")
