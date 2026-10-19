"""
ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
The emotion state must be shared between processes.

The game agent and the main server are two processes; each used to keep its
own in-memory emotion state, so they never agreed on how the user felt. The
lifecycle state solved the same problem with a shared JSON file — the
emotion state now does the same.

The constructor deliberately does NOT read the file: an implicit read would
leak state between processes *and* between tests.
"""

import json

from ai.alignment.emotion_system import EmotionSystem, EmotionType


def _system(tmp_path):
    system = EmotionSystem()
    system.state_path = lambda: str(tmp_path / "emotion_state.json")  # type: ignore[method-assign]
    return system


def test_state_is_written_and_read_back(tmp_path):
    system = _system(tmp_path)
    state = system.analyze_emotional_context({"text": "I am so happy today!"})
    assert state.primary_emotion in tuple(EmotionType)

    path = tmp_path / "emotion_state.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["summary"]["dominant_emotion"]

    # A second process (a fresh instance) adopts the shared state.
    other = _system(tmp_path)
    assert other.adopt_shared_state() is True
    assert other.get_emotion_summary()["dominant_emotion"] == (
        system.get_emotion_summary()["dominant_emotion"]
    )


def test_adoption_is_explicit_not_automatic(tmp_path):
    """A fresh instance must not silently inherit the file's content."""
    system = _system(tmp_path)
    system.analyze_emotional_context({"text": "I am so happy today!"})

    other = _system(tmp_path)
    assert other.emotion_history == []
    assert other.adopt_shared_state() is True
    assert other.emotion_history


def test_missing_file_is_not_an_error(tmp_path):
    system = _system(tmp_path)
    assert system.adopt_shared_state() is False
    assert system.emotion_history == []


def test_corrupt_file_is_survivable(tmp_path):
    path = tmp_path / "emotion_state.json"
    path.write_text("{not json", encoding="utf-8")
    system = _system(tmp_path)
    assert system.adopt_shared_state() is False
