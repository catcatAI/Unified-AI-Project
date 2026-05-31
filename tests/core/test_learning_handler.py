"""P8-1c — LearningHandler unit tests"""


class TestLearningHandler:

    def setup_method(self):
        from services.handlers.learning_handler import LearningHandler
        self.handler = LearningHandler()

    def test_handler_instantiated(self):
        assert self.handler is not None
        assert hasattr(self.handler, "handle")

    def test_extract_fact_remember(self):
        f = self.handler._extract_fact("記住這個 API 金鑰在 .env")
        assert f == "API 金鑰在 .env"

    def test_extract_fact_learn(self):
        f = self.handler._extract_fact("學習 Python 的列表推導式")
        assert f == "Python 的列表推導式"

    def test_extract_fact_teach(self):
        f = self.handler._extract_fact("教我怎麼用 FastAPI")
        assert f == "怎麼用 FastAPI"

    def test_extract_fact_record(self):
        f = self.handler._extract_fact("記錄這個設定檔路徑")
        assert f == "這個設定檔路徑"

    def test_extract_fact_remember_english(self):
        f = self.handler._extract_fact("remember to check logs first")
        assert f == "to check logs first"

    def test_extract_fact_empty(self):
        f = self.handler._extract_fact("記住")
        assert f is None

    def test_extract_fact_chinese_about_prefix(self):
        f = self.handler._extract_fact("學習關於容器的知識")
        assert f == "容器的知識"

    def test_handle_empty_text(self):
        import asyncio
        result = asyncio.run(self.handler.handle("記住", "learning"))
        assert "想讓我記住什麼" in result

    def test_handle_valid_text(self):
        import asyncio
        result = asyncio.run(self.handler.handle("學習 AsyncIO 的基本用法", "learning"))
        assert "我記住了" in result
        assert "AsyncIO 的基本用法" in result
