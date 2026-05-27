"""C4 — IntentModel unit tests"""

from core.life.intent_model import IntentCategory, SelfIntent, IntentManager


class TestSelfIntent:

    def test_default_values(self):
        intent = SelfIntent(id="test_1", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(1.0, 0.0, 0.0))
        assert intent.urgency == 0.5
        assert intent.strength == 1.0
        assert intent.decay_rate == 0.01

    def test_is_expired_false_when_positive(self):
        intent = SelfIntent(id="t1", category=IntentCategory.EXPLORATION,
                            target_dimension="gamma", target_coordinate=(0.0, 0.0, 0.0),
                            strength=0.001)
        assert not intent.is_expired()

    def test_is_expired_true_when_zero(self):
        intent = SelfIntent(id="t2", category=IntentCategory.SOCIAL_BOND,
                            target_dimension="delta", target_coordinate=(0.0, 0.0, 0.0),
                            strength=0.0)
        assert intent.is_expired()

    def test_is_expired_true_when_negative(self):
        intent = SelfIntent(id="t3", category=IntentCategory.SELF_PRESERVATION,
                            target_dimension="alpha", target_coordinate=(0.0, 0.0, 0.0),
                            strength=-0.5)
        assert intent.is_expired()


class TestIntentManager:

    def setup_method(self):
        self.mgr = IntentManager()

    def test_initial_intents_empty(self):
        assert self.mgr.intents == []
        assert self.mgr.active_intent_vector["alpha"] == (0.0, 0.0, 0.0)

    def test_add_intent_appends(self):
        intent = SelfIntent(id="a1", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(2.0, 0.0, 0.0))
        self.mgr.add_intent(intent)
        assert len(self.mgr.intents) == 1
        assert self.mgr.intents[0].id == "a1"

    def test_update_intents_decays_strength(self):
        intent = SelfIntent(id="d1", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(1.0, 0.0, 0.0),
                            strength=1.0, decay_rate=0.5)
        self.mgr.add_intent(intent)
        self.mgr.update_intents(delta_time=1.0)
        assert intent.strength == 0.5  # 1.0 * (1 - 0.5)^1 = 0.5

    def test_update_intents_removes_expired(self):
        intent = SelfIntent(id="e1", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(0.0, 0.0, 0.0),
                            strength=0.5, decay_rate=1.0)
        self.mgr.add_intent(intent)
        self.mgr.update_intents(delta_time=1.0)
        assert len(self.mgr.intents) == 0

    def test_update_intents_multiple_steps(self):
        intent = SelfIntent(id="m1", category=IntentCategory.EXPLORATION,
                            target_dimension="gamma", target_coordinate=(0.0, 0.0, 0.0),
                            strength=1.0, decay_rate=0.1)
        self.mgr.add_intent(intent)
        for _ in range(5):
            self.mgr.update_intents(delta_time=1.0)
        assert 0.5 < intent.strength < 0.6  # ~0.59049 after 5 steps

    def test_calculate_active_vectors_single_intent(self):
        intent = SelfIntent(id="v1", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(10.0, 0.0, 0.0),
                            strength=1.0, urgency=1.0)
        self.mgr.add_intent(intent)
        self.mgr._calculate_active_vectors()
        vec = self.mgr.get_intent_influence("alpha")
        assert vec == (10.0, 0.0, 0.0)

    def test_calculate_active_vectors_two_intents(self):
        self.mgr.add_intent(SelfIntent(id="v2a", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(10.0, 0.0, 0.0),
                            strength=1.0, urgency=0.5))
        self.mgr.add_intent(SelfIntent(id="v2b", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(0.0, 5.0, 0.0),
                            strength=1.0, urgency=0.5))
        self.mgr._calculate_active_vectors()
        vec = self.mgr.get_intent_influence("alpha")
        assert vec == (5.0, 2.5, 0.0)  # weighted average

    def test_get_intent_influence_nonexistent_dimension(self):
        vec = self.mgr.get_intent_influence("nonexistent")
        assert vec == (0.0, 0.0, 0.0)

    def test_get_intent_influence_after_update(self):
        intent = SelfIntent(id="g1", category=IntentCategory.EXPLORATION,
                            target_dimension="gamma", target_coordinate=(3.0, 4.0, 0.0),
                            strength=1.0, urgency=0.5)
        self.mgr.add_intent(intent)
        self.mgr.update_intents(delta_time=0)  # no decay, just recalc
        vec = self.mgr.get_intent_influence("gamma")
        assert vec == (3.0, 4.0, 0.0)

    def test_empty_after_clear_and_update(self):
        self.mgr.add_intent(SelfIntent(id="c1", category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha", target_coordinate=(1.0, 1.0, 1.0),
                            strength=0.0, decay_rate=1.0))
        self.mgr.update_intents(delta_time=1.0)
        assert len(self.mgr.intents) == 0
        vec = self.mgr.get_intent_influence("alpha")
        assert vec == (0.0, 0.0, 0.0)

    def test_scan_memory_proximity_empty_bridge_returns_no_intents(self):
        class MockBridge:
            def retrieve_by_spatial_proximity(self, x, y, z, radius=5.0):
                return []
        self.mgr.scan_memory_proximity(MockBridge(), {"alpha": {"coordinate": (1.0, 2.0, 3.0)}})
        assert len(self.mgr.intents) == 0

    def test_generate_homeostatic_intents_high_energy_no_new_intent(self):
        intent = SelfIntent(id="TestIntent_HOMEOSTASIS_alpha_9988776655",
                            category=IntentCategory.HOMEOSTASIS,
                            target_dimension="alpha",
                            target_coordinate=(0.0, 0.0, 0.0))
        self.mgr.add_intent(intent)
        count_before = len(self.mgr.intents)
        state = {"alpha": {"energy": 1.0}, "gamma": {"happiness": 1.0}, "delta": {"bond": 1.0}}
        self.mgr.generate_homeostatic_intents(state)
        assert len(self.mgr.intents) == count_before  # no new intents added
