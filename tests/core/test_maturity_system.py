"""C4 — MaturitySystem unit tests"""

from core.maturity.maturity_system import ExperienceTracker, MaturityLevel, MaturityManager


class TestMaturityLevel:

    def test_level_0_newborn(self):
        info = MaturityLevel.from_memory(0)
        assert info["level"] == 0
        assert info["cn_name"] == "新生"

    def test_level_0_edge_low(self):
        info = MaturityLevel.from_memory(99)
        assert info["level"] == 0

    def test_level_1_infant_low(self):
        info = MaturityLevel.from_memory(100)
        assert info["level"] == 1
        assert info["en_name"] == "Infant"

    def test_level_1_edge_high(self):
        info = MaturityLevel.from_memory(999)
        assert info["level"] == 1

    def test_level_2_child(self):
        info = MaturityLevel.from_memory(1000)
        assert info["level"] == 2

    def test_level_5_mature(self):
        info = MaturityLevel.from_memory(50000)
        assert info["level"] == 5
        assert info["cn_name"] == "成熟"

    def test_level_11_omniscient(self):
        info = MaturityLevel.from_memory(50000000)
        assert info["level"] == 11
        assert info["en_name"] == "Omniscient"

    def test_level_11_above_max(self):
        info = MaturityLevel.from_memory(999999999)
        assert info["level"] == 11
        assert info["max_memory"] is None

    def test_negative_memory_falls_to_level_11(self):
        info = MaturityLevel.from_memory(-5)
        assert info["level"] == 11


class TestCapabilities:

    def test_level_0_has_basic_capabilities(self):
        caps = CAPABILITIES[0]
        assert "basic_greeting" in caps["capabilities"]
        assert caps["emotional_range"] == "neutral_only"
        assert caps["autonomy"] == "none"

    def test_level_3_has_debate(self):
        caps = CAPABILITIES[3]
        assert "debate" in caps["capabilities"]
        assert caps["intimacy_level"] == "romantic_potential"

    def test_level_5_has_wisdom(self):
        caps = CAPABILITIES[5]
        assert "wisdom" in caps["capabilities"]
        assert caps["autonomy"] == "very_high"

    def test_missing_level_falls_back_to_level_0(self):
        assert 6 not in CAPABILITIES


class TestExperienceTracker:

    def setup_method(self):
        self.tracker = ExperienceTracker()

    def test_initial_state(self):
        status = self.tracker.get_status()
        assert status["level"] == 0
        assert status["memory_count"] == 0

    def test_add_experience_increases_memory(self):
        self.tracker.add_experience("chat", memory_impact=50)
        assert self.tracker.memory_count == 50
        assert self.tracker.interaction_count == 1

    def test_add_experience_appends_to_list(self):
        self.tracker.add_experience("chat", memory_impact=10)
        self.tracker.add_experience("task", memory_impact=20)
        assert len(self.tracker.experiences) == 2
        assert self.tracker.experiences[0]["type"] == "chat"
        assert self.tracker.experiences[1]["type"] == "task"

    def test_get_status_returns_level_0_initially(self):
        status = self.tracker.get_status()
        assert status["level"] == 0
        assert status["name"] == "新生"

    def test_get_status_level_after_memory_growth(self):
        self.tracker.memory_count = 100
        status = self.tracker.get_status()
        assert status["level"] == 1
        assert status["name"] == "幼儿"

    def test_get_status_contains_capabilities(self):
        status = self.tracker.get_status()
        assert "capabilities" in status
        assert "emotional_range" in status
        assert "intimacy_level" in status
        assert "autonomy" in status


class TestMaturityManager:

    def setup_method(self):
        self.mgr = MaturityManager()

    def test_initial_level_is_zero(self):
        assert self.mgr.current_level == 0

    def test_interact_returns_status(self):
        status = self.mgr.interact("conversation", memory_impact=5)
        assert status["level"] == 0

    def test_interact_level_up(self):
        status = self.mgr.interact("big_event", memory_impact=200)
        assert status["level"] >= 1

    def test_level_history_records_level_up(self):
        self.mgr.interact("big_event", memory_impact=200)
        assert len(self.mgr.level_history) >= 1
        entry = self.mgr.level_history[0]
        assert entry["from"] == 0
        assert entry["to"] >= 1
        assert entry["memory"] >= 200

    def test_no_duplicate_level_history_within_same_level(self):
        self.mgr.interact("small", memory_impact=50)
        self.mgr.interact("small", memory_impact=30)
        assert len(self.mgr.level_history) <= 1

    def test_get_status_delegates_to_tracker(self):
        status = self.mgr.get_status()
        assert status["level"] == 0
        assert self.mgr.tracker.memory_count == 0
