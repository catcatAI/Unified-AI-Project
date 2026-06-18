import pytest

from ai.ed3n.ed3n_engine import ED3NEngine


@pytest.fixture(scope="function")
def engine():
    e = ED3NEngine()
    e.load_presets()
    return e


@pytest.fixture(scope="function")
def trained_engine():
    e = ED3NEngine()
    e.load_presets()
    from ai.ed3n.ed3n_trainer import ED3NTrainer
    from ai.ed3n.training_types import TrainingBatch, TrainingExample

    trainer = ED3NTrainer(e)
    examples = [
        TrainingExample(
            input_text="hello",
            expected_output="hi",
            input_keys=["g1"],
            output_keys=["g5"],
            relation_pairs=[],
            confidence=0.8,
            metadata={},
        ),
        TrainingExample(
            input_text="bye",
            expected_output="goodbye",
            input_keys=["g1", "f1"],
            output_keys=["f2"],
            relation_pairs=[],
            confidence=0.8,
            metadata={},
        ),
    ]
    batch = TrainingBatch(examples=examples, batch_id="test")
    trainer.train_step(batch)
    return e
