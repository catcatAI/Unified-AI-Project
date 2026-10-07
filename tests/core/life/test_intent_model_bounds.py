# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""Intent model bounds: bulk adds without ticks must not OOM."""

from core.life.intent_model import IntentCategory, IntentManager, SelfIntent


def _intent(i: int) -> SelfIntent:
    return SelfIntent(
        id=f"intent_{i}",
        category=IntentCategory.EXPLORATION,
        target_dimension="alpha",
        target_coordinate=(0.1, 0.2, 0.3),
    )


def test_intent_list_bounded():
    from core.life.intent_model import MAX_INTENTS

    mgr = IntentManager()
    for i in range(MAX_INTENTS + 100):
        mgr.add_intent(_intent(i))
    assert len(mgr.intents) == MAX_INTENTS
    assert mgr.intents[0].id == f"intent_{100}"
