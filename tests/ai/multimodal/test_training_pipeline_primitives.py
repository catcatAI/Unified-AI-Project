"""Tests for PrimitiveTrainer and FullTrainingPipeline Phase 3d."""
import numpy as np
import pytest


@pytest.fixture
def pipeline():
    from ai.multimodal.training_pipeline import FullTrainingPipeline
    return FullTrainingPipeline()


class TestPrimitiveTrainer:
    """Test PrimitiveTrainer class directly."""

    @pytest.fixture
    def trainer(self):
        from ai.multimodal.primitives.primitive_encoder import PrimitiveEncoder
        from ai.multimodal.generator.sequence_generator import SequenceGenerator
        from ai.multimodal.training_pipeline import PrimitiveTrainer
        encoder = PrimitiveEncoder(embedding_dim=128)
        seq_gen = SequenceGenerator()
        return PrimitiveTrainer(encoder, seq_gen)

    def test_create_library_shapes_returns_list(self, trainer):
        shapes = trainer._create_library_shapes()
        assert len(shapes) > 50
        for s in shapes:
            assert hasattr(s, "to_vector")

    def test_populate_library(self, trainer):
        from ai.multimodal.primitives.primitive_library import PrimitiveLibrary
        shapes = trainer._create_library_shapes()
        lib = PrimitiveLibrary(embedding_dim=trainer._encoder.embedding_dim,
                               max_primitives=len(shapes))
        for i, shape in enumerate(shapes):
            emb = trainer._encoder.encode(shape)
            lib.add_primitive(f"t_{i:04d}", shape, emb)
        assert lib.size == len(shapes)

    def test_train_encoder(self, trainer):
        shapes = trainer._create_library_shapes()
        result = trainer._encoder.train(shapes, epochs=30, lr=0.01)
        assert result["best_loss"] < 0.1
        assert result["epochs_trained"] > 0

    def test_reencode_library_improves_reconstruction(self, trainer):
        from ai.multimodal.primitives.primitive_library import PrimitiveLibrary
        shapes = trainer._create_library_shapes()
        lib = PrimitiveLibrary(embedding_dim=trainer._encoder.embedding_dim,
                               max_primitives=len(shapes))
        for i, shape in enumerate(shapes):
            emb = trainer._encoder.encode(shape)
            lib.add_primitive(f"s_{i:04d}", shape, emb)

        before_errors = []
        for shape in shapes[:20]:
            emb = trainer._encoder.encode(shape)
            decoded = trainer._encoder.decode(emb)
            before_errors.append(np.mean((shape.to_vector() - decoded.to_vector()) ** 2))
        avg_before = np.mean(before_errors)

        trainer._encoder.train(shapes, epochs=30, lr=0.01)

        for name in lib._names:
            shape = lib.get_primitive(name)
            emb = trainer._encoder.encode(shape)
            lib._primitives[name]["embedding"] = emb
        lib._dirty = True

        after_errors = []
        for shape in shapes[:20]:
            emb = trainer._encoder.encode(shape)
            decoded = trainer._encoder.decode(emb)
            after_errors.append(np.mean((shape.to_vector() - decoded.to_vector()) ** 2))
        avg_after = np.mean(after_errors)

        assert avg_after < avg_before

    def test_train_runs_end_to_end(self, trainer):
        result = trainer.train(epochs=20, lr=0.01, seq_epochs=0)
        assert "encoder_result" in result
        assert result["encoder_result"]["best_loss"] < 0.2
        assert result["library_size"] == trainer._library.size
        assert result["library_size"] > 50
        assert "sequence_result" not in result

    def test_train_with_sequence_retrain(self, trainer):
        result = trainer.train(epochs=20, lr=0.01, seq_epochs=10, seq_lr=0.001, n_seq_samples=100)
        assert "sequence_result" in result
        assert result["sequence_result"]["final_loss"] < 0.5

    def test_library_property(self, trainer):
        from ai.multimodal.primitives.primitive_library import PrimitiveLibrary
        assert trainer.library is None
        shapes = trainer._create_library_shapes()
        lib = PrimitiveLibrary(embedding_dim=trainer._encoder.embedding_dim,
                               max_primitives=10)
        for i, shape in enumerate(shapes[:5]):
            emb = trainer._encoder.encode(shape)
            lib.add_primitive(f"p_{i:04d}", shape, emb)
        assert lib.size == 5


class TestFullPipelinePhase3d:
    """Test Phase 3d integration in FullTrainingPipeline."""

    def test_train_primitives_returns_dict(self, pipeline):
        result = pipeline.train_primitives(epochs=20, lr=0.01, seq_epochs=0)
        assert "encoder_result" in result
        assert "library_size" in result
        assert result["library_size"] > 50

    def test_train_primitives_encoder_trained(self, pipeline):
        assert pipeline._primitive_encoder is None
        pipeline.train_primitives(epochs=20, lr=0.01, seq_epochs=0)
        assert pipeline._primitive_encoder is not None
        assert pipeline._primitive_encoder.is_trained
        assert pipeline._primitive_library is not None
        assert pipeline._primitive_library.size > 50

    def test_train_primitives_loss_decreases(self, pipeline):
        result = pipeline.train_primitives(epochs=30, lr=0.01, seq_epochs=0)
        assert result["encoder_result"]["best_loss"] < 0.15
        assert "history" in result["encoder_result"]

    def test_train_primitives_weights_change(self, pipeline):
        snap_before = pipeline._sequence_generator._W_ho.copy()
        pipeline.train_primitives(epochs=20, lr=0.01, seq_epochs=15, seq_lr=0.001)
        assert not np.allclose(pipeline._sequence_generator._W_ho, snap_before)

    def test_image_generator_produces_structured_output_after_training(self, pipeline):
        from ai.multimodal.generator.image_generator import ImageGenerator
        pipeline.train_primitives(epochs=30, lr=0.01, seq_epochs=20, seq_lr=0.001)
        gen = ImageGenerator(
            sequence_generator=pipeline._sequence_generator,
            primitive_encoder=pipeline._primitive_encoder,
        )
        img = gen.generate_from_text("test", canvas_size=(64, 64))
        arr = np.array(img)
        unique_colors = len(np.unique(arr.reshape(-1, 3), axis=0))
        assert unique_colors >= 2
        assert not np.all(arr == arr[0, 0])


class TestPrimitiveEncoderPersistence:
    """Test save/load of PrimitiveEncoder weights through FullTrainingPipeline."""

    def test_primitive_encoder_weights_saved_in_pipeline_save(self, pipeline, tmp_path):
        pipeline.train_primitives(epochs=10, lr=0.01, seq_epochs=0)
        save_path = str(tmp_path / "prim_enc_keys.npz")
        pipeline.save_weights(save_path)
        data = np.load(save_path, allow_pickle=False)
        for key in ["prim_enc_W_encode", "prim_enc_b_encode",
                     "prim_enc_W_decode", "prim_enc_b_decode"]:
            assert key in data, f"Missing key: {key}"

    def test_load_weights_restores_primitive_encoder(self, pipeline, tmp_path):
        from ai.multimodal.training_pipeline import FullTrainingPipeline
        pipeline.train_primitives(epochs=10, lr=0.01, seq_epochs=0)
        save_path = str(tmp_path / "prim_enc_roundtrip.npz")
        pipeline.save_weights(save_path)
        data_before = np.load(save_path, allow_pickle=False)

        fresh = FullTrainingPipeline()
        loaded = fresh.load_weights(save_path)
        assert loaded
        assert fresh._primitive_encoder is not None
        assert fresh._primitive_encoder.is_trained
        assert np.allclose(
            fresh._primitive_encoder._W_encode, data_before["prim_enc_W_encode"])
        assert np.allclose(
            fresh._primitive_encoder._b_encode, data_before["prim_enc_b_encode"])
        assert np.allclose(
            fresh._primitive_encoder._W_decode, data_before["prim_enc_W_decode"])
        assert np.allclose(
            fresh._primitive_encoder._b_decode, data_before["prim_enc_b_decode"])

    def test_load_weights_compatible_without_prim_enc(self, pipeline, tmp_path):
        """Old weight files without primitive encoder should still load."""
        from ai.multimodal.training_pipeline import FullTrainingPipeline
        pipeline.train_sequence(batch_size=2, steps=3, lr=0.001)
        save_path = str(tmp_path / "no_prim_enc.npz")
        pipeline.save_weights(save_path)

        fresh = FullTrainingPipeline()
        loaded = fresh.load_weights(save_path)
        assert loaded
        assert fresh._primitive_encoder is None

    def test_image_generator_works_after_weight_roundtrip(self, pipeline, tmp_path):
        from ai.multimodal.generator.image_generator import ImageGenerator
        from ai.multimodal.training_pipeline import FullTrainingPipeline
        pipeline.train_primitives(epochs=20, lr=0.01, seq_epochs=15, seq_lr=0.001)
        save_path = str(tmp_path / "gen_roundtrip.npz")
        pipeline.save_weights(save_path)

        fresh = FullTrainingPipeline()
        fresh.load_weights(save_path)

        gen = ImageGenerator(
            sequence_generator=fresh._sequence_generator,
            primitive_encoder=fresh._primitive_encoder,
        )
        img = gen.generate_from_text("a red circle", canvas_size=(64, 64))
        assert img is not None
        assert img.size == (64, 64)
