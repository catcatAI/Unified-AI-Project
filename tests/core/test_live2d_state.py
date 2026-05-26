"""C2 — Live2DIntegration get_live2d_state unit tests"""

import sys
sys.path.insert(0, 'apps/backend/src')


class TestLive2DState:

    def setup_method(self):
        from core.engine.live2d_integration import Live2DIntegration
        self.l2d = Live2DIntegration()

    def test_get_live2d_state_returns_dict(self):
        state = self.l2d.get_live2d_state()
        assert isinstance(state, dict)

    def test_get_live2d_state_has_expression(self):
        state = self.l2d.get_live2d_state()
        assert 'expression' in state
        assert state['expression'] == 'neutral'

    def test_get_live2d_state_has_motion(self):
        state = self.l2d.get_live2d_state()
        assert 'motion' in state
        assert state['motion'] == 'idle'

    def test_get_live2d_state_has_parameters(self):
        state = self.l2d.get_live2d_state()
        assert 'parameters' in state
        assert isinstance(state['parameters'], dict)
        assert 'ParamAngleX' in state['parameters']
        assert 'ParamMouthOpenY' in state['parameters']

    def test_get_live2d_state_expression_after_set(self):
        from core.engine.live2d_integration import ExpressionType
        self.l2d.set_expression(ExpressionType.HAPPY)
        state = self.l2d.get_live2d_state()
        assert state['expression'] == 'happy'

    def test_get_live2d_state_contains_parameter_values(self):
        state = self.l2d.get_live2d_state()
        params = state['parameters']
        assert isinstance(params['ParamAngleX'], (int, float))
        assert isinstance(params['ParamMouthOpenY'], (int, float))

    def test_get_all_parameters_matches_state(self):
        all_params = self.l2d.get_all_parameters()
        state_params = self.l2d.get_live2d_state()['parameters']
        assert all_params == state_params

    def test_get_all_parameters_types(self):
        params = self.l2d.get_all_parameters()
        for name, val in params.items():
            assert isinstance(name, str)
            assert isinstance(val, (int, float))

    def test_register_live2d_state_callback_fires(self):
        from core.engine.live2d_integration import ExpressionType
        results = []
        def cb(state):
            results.append(state['expression'])
        self.l2d.register_live2d_state_callback(cb)
        self.l2d.set_expression(ExpressionType.HAPPY)
        assert len(results) >= 1
        assert 'happy' in results
