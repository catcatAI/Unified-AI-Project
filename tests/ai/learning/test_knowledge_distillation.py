import pytest
from unittest.mock import MagicMock, AsyncMock


class TestDistillationLoss:
    def test_init_default(self):
        from apps.backend.src.ai.learning.knowledge_distillation import DistillationLoss
        loss_fn = DistillationLoss()
        assert loss_fn.temperature == 1.0

    def test_init_custom_temperature(self):
        from apps.backend.src.ai.learning.knowledge_distillation import DistillationLoss
        loss_fn = DistillationLoss(temperature=4.0)
        assert loss_fn.temperature == 4.0

    def test_call_with_numbers(self):
        from apps.backend.src.ai.learning.knowledge_distillation import DistillationLoss
        loss_fn = DistillationLoss()
        loss = loss_fn(5.0, 3.0, None)
        assert loss == 4.0

    def test_call_with_identical_values(self):
        from apps.backend.src.ai.learning.knowledge_distillation import DistillationLoss
        loss_fn = DistillationLoss()
        loss = loss_fn(3.0, 3.0, None)
        assert loss == 0.0

    def test_call_with_non_numeric_falls_back(self):
        from apps.backend.src.ai.learning.knowledge_distillation import DistillationLoss
        loss_fn = DistillationLoss()
        loss = loss_fn('invalid', 3.0, None)
        assert loss == 0.0

    def test_call_with_integer_inputs(self):
        from apps.backend.src.ai.learning.knowledge_distillation import DistillationLoss
        loss_fn = DistillationLoss()
        loss = loss_fn(5, 3, None)
        assert loss == 4.0


class TestKnowledgeDistillationManagerInit:
    def test_init(self):
        from apps.backend.src.ai.learning.knowledge_distillation import KnowledgeDistillationManager
        teacher = MagicMock()
        student = MagicMock()
        manager = KnowledgeDistillationManager(teacher, student)
        assert manager.teacher_model is teacher
        assert manager.student_model is student
        assert manager.distillation_loss.temperature == 4.0


class TestKnowledgeDistillationManagerDistill:
    @pytest.mark.asyncio
    async def test_distill_knowledge_runs_without_error(self):
        from apps.backend.src.ai.learning.knowledge_distillation import KnowledgeDistillationManager
        teacher = MagicMock()
        teacher.predict = AsyncMock(return_value=0.9)
        student = MagicMock()
        student.predict = AsyncMock(return_value=0.7)
        manager = KnowledgeDistillationManager(teacher, student)
        await manager.distill_knowledge([1, 2, 3], epochs=2)
        assert teacher.predict.call_count == 6
        assert student.predict.call_count == 6

    @pytest.mark.asyncio
    async def test_distill_knowledge_empty_data(self):
        from apps.backend.src.ai.learning.knowledge_distillation import KnowledgeDistillationManager
        teacher = MagicMock()
        student = MagicMock()
        manager = KnowledgeDistillationManager(teacher, student)
        await manager.distill_knowledge([], epochs=1)
        teacher.predict.assert_not_called()
        student.predict.assert_not_called()


class TestKnowledgeDistillationManagerEvaluate:
    @pytest.mark.asyncio
    async def test_evaluate_with_evaluate_method(self):
        from apps.backend.src.ai.learning.knowledge_distillation import KnowledgeDistillationManager
        teacher = MagicMock()
        teacher.evaluate = AsyncMock(return_value=0.95)
        student = MagicMock()
        student.evaluate = AsyncMock(return_value=0.85)
        manager = KnowledgeDistillationManager(teacher, student)
        result = await manager.evaluate_distillation([1, 2, 3])
        assert result['teacher_accuracy'] == 0.95
        assert result['student_accuracy'] == 0.85
        assert result['distillation_ratio'] == pytest.approx(0.85 / 0.95)

    @pytest.mark.asyncio
    async def test_evaluate_without_evaluate_method_uses_default(self):
        from apps.backend.src.ai.learning.knowledge_distillation import KnowledgeDistillationManager
        teacher = MagicMock(spec=[])
        student = MagicMock(spec=[])
        manager = KnowledgeDistillationManager(teacher, student)
        result = await manager.evaluate_distillation([1, 2, 3])
        assert result['teacher_accuracy'] == 0.85
        assert result['student_accuracy'] == 0.85
        assert result['distillation_ratio'] == 1.0
