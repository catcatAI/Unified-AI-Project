"""HAM 工具函数测试"""

import numpy as np

from apps.backend.src.ai.memory.ham_utils import (
    calculate_cosine_similarity,
    generate_embedding,
    get_current_utc_timestamp,
    is_valid_uuid,
)


class TestCalculateCosineSimilarity:
    def test_identical_vectors(self):
        vec = np.array([1.0, 0.0, 0.0])
        assert calculate_cosine_similarity(vec, vec) == 1.0

    def test_orthogonal_vectors(self):
        v1 = np.array([1.0, 0.0])
        v2 = np.array([0.0, 1.0])
        assert abs(calculate_cosine_similarity(v1, v2)) < 1e-9

    def test_zero_vector_returns_zero(self):
        zero = np.zeros(3)
        vec = np.ones(3)
        assert calculate_cosine_similarity(zero, vec) == 0.0

    def test_non_1d_raises(self):
        matrix = np.ones((2, 2))
        vec = np.ones(2)
        try:
            calculate_cosine_similarity(matrix, vec)
        except ValueError:
            pass
        else:
            raise AssertionError("non-1D input should raise ValueError")


class TestGenerateEmbedding:
    def test_returns_384_dim_float32(self):
        vec = generate_embedding("hello world")
        assert vec.shape == (384,)
        assert vec.dtype == np.float32

    def test_normalized(self):
        vec = generate_embedding("some text here")
        norm = np.linalg.norm(vec)
        assert abs(norm - 1.0) < 1e-5

    def test_empty_and_short_texts(self):
        assert np.array_equal(generate_embedding(""), np.zeros(384))
        assert np.array_equal(generate_embedding("a"), np.zeros(384))

    def test_similar_texts_have_high_similarity(self):
        v1 = generate_embedding("the quick brown fox")
        v2 = generate_embedding("the quick brown fox jumps")
        assert calculate_cosine_similarity(v1, v2) > 0.3


class TestGetCurrentUtcTimestamp:
    def test_returns_positive_float(self):
        ts = get_current_utc_timestamp()
        assert isinstance(ts, float)
        assert ts > 1_000_000_000


class TestIsValidUUID:
    def test_valid_uuid(self):
        assert is_valid_uuid("123e4567-e89b-12d3-a456-426614174000", version=1) is True

    def test_invalid_uuid(self):
        assert is_valid_uuid("not-a-uuid") is False

    def test_version_mismatch(self):
        # v1 UUID passed with version=4 should be invalid
        assert is_valid_uuid("123e4567-e89b-12d3-a456-426614174000", version=4) is False

    def test_v4_uuid(self):
        import uuid

        assert is_valid_uuid(str(uuid.uuid4())) is True
