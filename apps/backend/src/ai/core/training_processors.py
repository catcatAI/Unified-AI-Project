# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [A] [L3]
# =============================================================================
"""
Training processors — the domain owners that actually train.

WHY this module exists: TrainingCoordinator owns a priority queue and a worker,
but a queue is not a trainer. Until now **no processor was ever registered**, so
every queued sample was deferred forever: the "sorted training execution"
feature (REFACTOR_PLAN §13.4) was implemented, tested, documented and unreachable
in exactly the way this repo has been accumulating dead features.

Rather than inventing a second trainer, this processor hands the queued
(user text, Angela reply) pairs to the learning owner that already runs:
``Backbone.trigger_learning()`` — the same entry point the chat pipeline uses,
which dispatches to the registered learners (GARDEN by default; the legacy ED3N
pipeline only under ANGELA_LEGACY_ED3N=1), performs its own dedup and records
its own metrics. The coordinator therefore owns *ordering and delivery*; the
learners keep *ownership of how learning happens*.
"""

import logging
from types import SimpleNamespace
from typing import Any, Dict

logger = logging.getLogger(__name__)


async def continuous_learning_processor(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Feed one queued (input, output) pair into the live learning owner.

    The owner is ``Backbone.trigger_learning()`` — the same entry point the chat
    pipeline itself uses. It dispatches to the registered learners (GARDEN by
    default; the legacy ED3N pipeline only when ANGELA_LEGACY_ED3N=1), performs
    its own dedup and records its own metrics, so learning policy stays with the
    learners and this module only owns delivery.

    WHY not ContinuousLearningPipeline directly: it is disabled by default
    (``chat_service.initialize`` builds it only when ANGELA_LEGACY_ED3N=1), so
    targeting it produced a processor that failed on every sample in a normal
    run — caught by probing a live server, not by the unit tests.

    Returns a small result dict. Raises on genuine failure so TrainingCoordinator
    counts it as ``failed`` rather than silently dropping the sample.
    """
    user_text = str(sample.get("input") or "").strip()
    response_text = str(sample.get("output") or "").strip()
    if not user_text or not response_text:
        raise ValueError("training sample must carry both input and output")

    # Imported here: api.lifespan imports the training coordinator, so a
    # module-level import would be circular. This is always awaited from inside
    # the running loop.
    from core.backbone import get_backbone

    backbone = get_backbone()
    if backbone is None:
        raise RuntimeError("Backbone is not initialised")

    # The learners read `response.text`; the queue stores plain strings.
    response_stub = SimpleNamespace(text=response_text)
    results = await backbone.trigger_learning(user_text, response_stub, {})
    results = results if isinstance(results, dict) else {}

    # A learner can swallow its own failure (dedup skip, engine not loaded) and
    # still report PAIRED, so surface the per-learner status instead of claiming
    # success. This is the only signal a user has that training actually ran.
    errors = {
        name: outcome.get("error")
        for name, outcome in results.items()
        if isinstance(outcome, dict) and outcome.get("status") == "ERROR"
    }
    if errors:
        raise RuntimeError(f"learner(s) failed: {errors}")
    logger.info(
        "[Training] delivered queued sample to learner(s): %s",
        ", ".join(sorted(results)) or "none registered",
    )
    return {"delivered_to": sorted(results), "owner": "backbone"}


def register_default_processors(coordinator: Any) -> Dict[str, str]:
    """Register the live learner for every domain the coordinator can queue.

    Returns {domain: description} for logging. All domains share the same owner
    because the learner coordinator decides internally what belongs to which
    subsystem — inventing per-domain trainers here would duplicate its gating.
    """
    from ai.core.training_coordinator import DOMAIN_OWNERSHIP

    registered: Dict[str, str] = {}
    for domain in sorted(DOMAIN_OWNERSHIP):
        coordinator.register_processor(domain, continuous_learning_processor)
        registered[domain] = "backbone.trigger_learning"
    logger.info(
        "[Training] registered %d domain processor(s) → backbone.trigger_learning",
        len(registered),
    )
    return registered
