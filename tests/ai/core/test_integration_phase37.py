"""
ANGELA-MATRIX: [L3-L4] [β] [A] [L3]
Phase 3.7 Integration Tests — Synonym Expansion, Math Eval, Reflex, Handlers, Full Pipeline.
"""

import asyncio
import os
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "src"))


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestSynonymExpansion:
    """Tests for dictionary_layer.py synonym expansion in _encode_locked."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from ai.ed3n.dictionary_layer import DictionaryLayer
        self.dl = DictionaryLayer()
        self.dl.load_preset_responses()

    def test_encode_greeting_includes_synonyms(self):
        keys = self.dl.encode("你好")
        assert "g1" in keys
        has_synonym = any(k in keys for k in ["g2", "g3", "g5", "g6"])
        assert has_synonym, f"Expected synonym of g1 in keys, got {keys}"

    def test_encode_english_greeting_includes_synonyms(self):
        keys = self.dl.encode("hello")
        assert "g1" in keys
        has_synonym = any(k in keys for k in ["g2", "g3", "g5", "g6"])
        assert has_synonym

    def test_synonym_expansion_broadens_recall(self):
        keys = self.dl.encode("早上好")
        assert "g2" in keys

    def test_encode_unknown_text_returns_empty(self):
        keys = self.dl.encode("こんにちは世界")
        assert keys == []

    def test_encode_capped_at_max_keys(self):
        keys = self.dl.encode("你好 早上好 晚上好 欢迎 嗨")
        assert len(keys) <= self.dl.MAX_ENCODE_KEYS

    def test_get_synonyms_transitivity(self):
        syns = self.dl.get_synonyms("g1")
        assert "g1" not in syns
        assert len(syns) >= 2

    def test_get_synonyms_nonexistent_key(self):
        syns = self.dl.get_synonyms("nonexistent_key_xyz")
        assert syns == []


class TestMathEvaluation:
    """Tests for ed3n_engine.py _try_math_eval."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from ai.ed3n.ed3n_engine import ED3NEngine
        self.engine = ED3NEngine()

    def test_addition_english(self):
        result = self.engine._try_math_eval("178 plus 101")
        assert result is not None
        assert "279" in result

    def test_subtraction_chinese(self):
        result = self.engine._try_math_eval("九减二")
        assert result is not None
        assert "7" in result

    def test_multiplication_chinese(self):
        result = self.engine._try_math_eval("三乘以五")
        assert result is not None
        assert "15" in result

    def test_division_chinese(self):
        result = self.engine._try_math_eval("六除以二")
        assert result is not None
        assert "3" in result

    def test_division_by_zero(self):
        result = self.engine._try_math_eval("五除以零")
        assert result is not None
        assert "除数不能为零" in result

    def test_integer_result(self):
        result = self.engine._try_math_eval("六除以三")
        assert result is not None
        assert "2" in result
        assert "2.0" not in result

    def test_float_result(self):
        result = self.engine._try_math_eval("五除以二")
        assert result is not None
        assert "2.5" in result

    def test_no_expression_returns_none(self):
        result = self.engine._try_math_eval("hello world")
        assert result is None

    def test_single_number_returns_none(self):
        result = self.engine._try_math_eval("42")
        assert result is None

    def test_question_mark_stripped(self):
        result = self.engine._try_math_eval("三加五等于多少？")
        assert result is not None
        assert "8" in result

    def test_engine_process_math(self):
        result = self.engine.process("1+1")
        assert result is not None
        assert "=" in result

    def test_engine_process_math_chinese(self):
        result = self.engine.process("三加五")
        assert result is not None
        assert "=" in result


class TestReflexExpansionPresets:
    """Tests for presets.json reflex patterns loading."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from ai.ed3n.ed3n_engine import ED3NEngine
        self.engine = ED3NEngine()
        config_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "apps", "backend", "src", "ai", "ed3n", "config"
        )
        self.engine.load_presets_from_config(config_dir)

    def test_reflex_loaded_from_config(self):
        assert len(self.engine.reflex.patterns) >= 30

    def test_reflex_file_operations(self):
        assert "创建文件" in self.engine.reflex.patterns
        assert "删除文件" in self.engine.reflex.patterns

    def test_reflex_task_patterns(self):
        assert "建立任务" in self.engine.reflex.patterns

    def test_reflex_system_patterns(self):
        assert "系统状态" in self.engine.reflex.patterns

    def test_reflex_emotion_patterns(self):
        assert "累" in self.engine.reflex.patterns
        assert "生气" in self.engine.reflex.patterns

    def test_reflex_personality_patterns(self):
        found = "你是谁" in self.engine.reflex.patterns or "你是誰" in self.engine.reflex.patterns
        assert found, f"'你是誰' or '你是谁' not in reflex patterns"

    def test_reflex_response_for_new_pattern(self):
        result = self.engine.process_reflex("创建文件")
        assert result is not None
        assert "创建" in result

    def test_reflex_case_insensitive_english(self):
        result = self.engine.process_reflex("HELLO")
        assert result is not None

    def test_reflex_priority_over_math(self):
        result = self.engine.process("你好")
        assert result is not None
        assert "=" not in result

    def test_math_priority_over_encode(self):
        result = self.engine.process("1+1")
        assert result is not None
        assert "=" in result


class TestHandlerFileOperation:
    """Tests for file_operation_handler.py."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from services.handlers.file_operation_handler import FileOperationHandler
        self.handler = FileOperationHandler()

    def test_create_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            result = _run_async(self.handler.handle("file_op_create", {"action": "create", "path": path}))
            assert "已建立" in result
            result = _run_async(self.handler.handle("file_op_read", {"action": "read", "path": path}))
            assert "test.txt" in result

    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            result = _run_async(self.handler.handle("file_op_write", {"action": "write", "path": path, "content": "hello"}))
            assert "寫入" in result
            result = _run_async(self.handler.handle("file_op_read", {"action": "read", "path": path}))
            assert "hello" in result

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            _run_async(self.handler.handle("file_op_create", {"action": "create", "path": path}))
            result = _run_async(self.handler.handle("file_op_delete", {"action": "delete", "path": path}))
            assert "刪除" in result

    def test_list_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_async(self.handler.handle("file_op_list", {"action": "list", "path": tmpdir}))
            assert "內容" in result

    def test_rename(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "old.txt")
            _run_async(self.handler.handle("file_op_create", {"action": "create", "path": path}))
            result = _run_async(self.handler.handle("file_op_rename", {"action": "rename", "path": path, "new_name": "new.txt"}))
            assert "重新命名" in result

    def test_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.txt")
            result = _run_async(self.handler.handle("file_op_exists", {"action": "exists", "path": path}))
            assert "不存在" in result

    def test_not_found(self):
        result = _run_async(self.handler.handle("file_op_read", {"action": "read", "path": "/nonexistent/path/file.txt"}))
        assert "不存在" in result or "不安全" in result

    def test_no_path(self):
        result = _run_async(self.handler.handle("file_op_create", {"action": "create"}))
        assert "請指定" in result


class TestHandlerCodeExecution:
    """Tests for code_execution_handler.py."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from services.handlers.code_execution_handler import CodeExecutionHandler
        self.handler = CodeExecutionHandler()

    def test_simple_code(self):
        result = _run_async(self.handler.handle("print(2+2)"))
        assert "4" in result

    def test_no_output(self):
        result = _run_async(self.handler.handle("x = 1"))
        assert "無輸出" in result

    def test_syntax_error(self):
        result = _run_async(self.handler.handle("def"))
        assert "錯誤" in result

    def test_empty_code(self):
        result = _run_async(self.handler.handle(""))
        assert "請提供" in result

    def test_too_long(self):
        result = _run_async(self.handler.handle("x = 1\n" * 5000))
        assert "過長" in result

    def test_extract_code_fenced(self):
        code = self.handler._extract_code("```python\nprint(1)\n```")
        assert code == "print(1)"

    def test_extract_code_backtick(self):
        code = self.handler._extract_code("`print(1)`")
        assert code == "print(1)"

    def test_no_import_in_sandbox(self):
        result = _run_async(self.handler.handle("import os; print(os.listdir('/'))"))
        assert "錯誤" in result or "import" in result.lower()


class TestHandlerSystemCommand:
    """Tests for system_command_handler.py."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from services.handlers.system_command_handler import SystemCommandHandler
        self.handler = SystemCommandHandler()

    def test_safe_command(self):
        import platform
        cmd = "hostname" if platform.system() == "Windows" else "whoami"
        result = _run_async(self.handler.handle(cmd))
        assert "輸出" in result or "執行完成" in result

    def test_unsafe_command_rejected(self):
        result = _run_async(self.handler.handle("rm -rf /"))
        assert "不安全" in result

    def test_python_rejected(self):
        result = _run_async(self.handler.handle("python -c 'print(1)'"))
        assert "不安全" in result

    def test_no_command(self):
        result = _run_async(self.handler.handle(""))
        assert "請提供" in result


class TestHandlerTaskManager:
    """Tests for task_manager_handler.py."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from services.handlers.task_manager_handler import TaskManagerHandler, _TASKS_FILE, _load_tasks, _save_tasks
        self.handler = TaskManagerHandler()
        self._original_tasks = _load_tasks()
        _save_tasks([])

    def teardown_method(self):
        from services.handlers.task_manager_handler import _save_tasks
        _save_tasks(self._original_tasks)

    def test_create_task(self):
        result = _run_async(self.handler.handle("建立任務：買菜"))
        assert "已建立" in result

    def test_list_tasks(self):
        _run_async(self.handler.handle("建立任務：買菜"))
        result = _run_async(self.handler.handle("任務列表"))
        assert "任務列表" in result

    def test_complete_task(self):
        _run_async(self.handler.handle("建立任務：買菜"))
        result = _run_async(self.handler.handle("完成任務 #1"))
        assert "已標記" in result

    def test_delete_task(self):
        _run_async(self.handler.handle("建立任務：買菜"))
        result = _run_async(self.handler.handle("刪除任務 #1"))
        assert "已刪除" in result

    def test_no_tasks(self):
        result = _run_async(self.handler.handle("任務列表"))
        assert "沒有任何任務" in result


class TestFullPipelineIntegration:
    """End-to-end tests: classifier → gate → handlers + ED3N."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from ai.core.query_classifier import QueryClassifier
        from ai.core.execution_gate import ExecutionGate
        from ai.ed3n.ed3n_engine import ED3NEngine
        self.clf = QueryClassifier()
        self.gate = ExecutionGate()
        self.engine = ED3NEngine()
        self.engine.load_presets()

    def test_greeting_reflex(self):
        result = self.engine.process("你好")
        assert result is not None
        assert len(result) > 0

    def test_math_pipeline(self):
        result = self.engine.process("三加五等于多少")
        assert result is not None
        assert "8" in result

    def test_search_auto_execute(self):
        r = self.clf.classify("搜寻台北天气")
        d = self.gate.decide(r.primary_type.value, r.action_type, "搜寻台北天气", r.confidence, {})
        assert d.action == "auto_execute"
        assert d.handler == "web_search"

    def test_delete_rejects(self):
        r = self.clf.classify("删除 temp.txt")
        d = self.gate.decide(r.primary_type.value, r.action_type, "删除 temp.txt", r.confidence, {})
        assert d.action == "reject"

    def test_negation_rejects(self):
        r = self.clf.classify("不要搜寻")
        d = self.gate.decide(r.primary_type.value, r.action_type, "不要搜寻", r.confidence, {})
        assert d.action == "reject"
        assert d.reason == "negation_detected"

    def test_execute_system_rejects(self):
        r = self.clf.classify("执行这个命令")
        d = self.gate.decide(r.primary_type.value, r.action_type, "执行这个命令", r.confidence, {})
        assert d.action == "reject"

    def test_file_read_auto_execute(self):
        r = self.clf.classify("读取 temp.txt")
        d = self.gate.decide(r.primary_type.value, r.action_type, "读取 temp.txt", r.confidence, {})
        assert d.action == "auto_execute"
        assert d.handler == "file_ops"

    def test_vision_has_handler(self):
        r = self.clf.classify("看图片")
        d = self.gate.decide(r.primary_type.value, r.action_type, "看图片", r.confidence, {})
        assert d.action in ("auto_execute", "confirm_then_execute")

    def test_knowledge_no_handler(self):
        r = self.clf.classify("什么是Python?")
        d = self.gate.decide(r.primary_type.value, r.action_type, "什么是Python?", r.confidence, {})
        assert d.action in ("confirm_then_execute", "reject")

    def test_classifier_gate_full_chain_search(self):
        r = self.clf.classify("搜寻台北天气")
        d = self.gate.decide(r.primary_type.value, r.action_type, "搜寻台北天气", r.confidence, {})
        assert d.handler == "web_search"

    def test_classifier_gate_full_chain_task(self):
        r = self.clf.classify("建立任务")
        d = self.gate.decide(r.primary_type.value, r.action_type, "建立任务", r.confidence, {})
        assert d.handler in ("file_ops", "task_mgr")

    def test_reflex_priority_over_math(self):
        result = self.engine.process("你好")
        assert "=" not in result

    def test_math_priority_over_encode(self):
        result = self.engine.process("1+1")
        assert "=" in result

    def test_encode_synonym_expansion(self):
        keys = self.engine.dictionary.encode("hello")
        assert len(keys) > 0

    def test_load_all_presets(self):
        config_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "apps", "backend", "src", "ai", "ed3n", "config"
        )
        self.engine.load_presets_from_config(config_dir)
        assert len(self.engine.reflex.patterns) >= 30
        assert len(self.engine.dictionary.entries) >= 30
