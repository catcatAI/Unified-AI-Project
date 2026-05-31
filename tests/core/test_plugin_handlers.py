"""P6-1 — Plugin handler deployment E2E tests"""

import asyncio


class TestPluginHandlerDeployment:

    def setup_method(self):
        from core.plugin.plugin_manager import PluginManager
        from core.plugin.hook_registry import HookRegistry
        from core.plugin.handlers.message_logger import MessageLoggerHandler
        self.r = HookRegistry()
        self.pm = PluginManager(self.r)
        self.handler = MessageLoggerHandler()
        self.pm.register_plugin("test_logger", "1.0", "Test handler")
        self.pm.add_handler("test_logger", "on_message", self.handler)

    def test_handler_registered(self):
        """Handler appears in plugin hooks list."""
        stats = self.pm.get_stats()
        hooks = stats["hook_registry"]["hooks"]
        on_msg = [h for h in hooks if h["name"] == "on_message"]
        assert len(on_msg) == 1
        assert on_msg[0]["handler_count"] >= 1

    def test_handler_modifies_data(self):
        """Handler adds plugin_logged_at and plugin_message_seq to data."""
        results = asyncio.run(
            self.pm.execute_hook("on_message", {"user_message": "hello", "model_id": "gpt4"})
        )
        assert len(results) == 1
        assert results[0].success is True
        result = results[0].result
        assert "plugin_logged_at" in result
        assert "plugin_message_seq" in result
        assert result["plugin_message_seq"] == 1

    def test_pipeline_returns_modified_data(self):
        """execute_pipeline returns data modified by handler."""
        modified = asyncio.run(
            self.pm.execute_pipeline("on_message", {"user_message": "test", "model_id": "claude"})
        )
        assert modified["plugin_message_seq"] == 1
        assert "plugin_logged_at" in modified
        assert modified["user_message"] == "test"

    def test_counter_increments_across_calls(self):
        """Handler message counter increments with each call."""
        for i in range(3):
            asyncio.run(
                self.pm.execute_pipeline("on_message", {"user_message": f"msg{i}", "model_id": "x"})
            )
        assert self.handler.counter == 3

    def test_on_response_hook_no_handlers_by_default(self):
        """on_response is defined but has no handlers deployed yet."""
        stats = self.pm.get_stats()
        hooks = stats["hook_registry"]["hooks"]
        on_resp = [h for h in hooks if h["name"] == "on_response"][0]
        assert on_resp["handler_count"] == 0

    def test_api_flow_via_plugin_registration(self):
        """Simulate registration + handler + execute through API layer."""
        self.pm.register_plugin("api_plugin", "2.0")
        self.pm.add_handler("api_plugin", "on_message", self.handler)
        results = asyncio.run(
            self.pm.execute_hook("on_message", {"user_message": "api_test", "model_id": "test"})
        )
        assert len(results) >= 1
        assert results[0].success is True
