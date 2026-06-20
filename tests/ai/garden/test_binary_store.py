# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [C] [L0]
# =============================================================================
"""
Tests for GARDEN BinaryStore (mmap-based weight matrix).
"""

import os
import tempfile

import pytest

from ai.garden.binary_store import (
    HEADER_SIZE,
    MAGIC,
    VERSION,
    BinaryStore,
)

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class TestBinaryStoreInit:
    """Tests for BinaryStore construction and creation."""

    def test_create_small(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test.bin")
            store = BinaryStore.create(path, V=10, fill_value=0.0)
            assert store.V == 10
            assert store.header["magic"] == MAGIC
            assert store.header["version"] == VERSION
            store.close()

    def test_create_with_fill(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_fill.bin")
            store = BinaryStore.create(path, V=5, fill_value=0.5)
            # Check a value
            assert store[0, 0] == 0.5
            assert store[4, 4] == 0.5
            store.close()

    def test_create_file_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_size.bin")
            V = 100
            store = BinaryStore.create(path, V=V, fill_value=0.0)
            store.close()
            expected = HEADER_SIZE + V * V * 4
            actual = os.path.getsize(path)
            assert actual == expected

    def test_open_existing_r(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_open.bin")
            store = BinaryStore.create(path, V=20, fill_value=0.3)
            store.close()
            store2 = BinaryStore(path, mode="r")
            assert store2.V == 20
            assert store2[0, 0] == 0.3
            store2.close()

    def test_open_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            BinaryStore("/nonexistent/path.bin", mode="r")


class TestBinaryStoreReadWrite:
    """Tests for reading and writing matrix values."""

    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_rw.bin")
            store = BinaryStore.create(path, V=10, fill_value=0.0)
            store[0, 1] = 0.75
            store[5, 5] = 1.0
            store[9, 0] = 0.5
            assert store[0, 1] == 0.75
            assert store[5, 5] == 1.0
            assert store[9, 0] == 0.5
            store.close()

    def test_slice_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_slice.bin")
            store = BinaryStore.create(path, V=5, fill_value=0.0)
            for i in range(5):
                store[i, i] = float(i) / 4.0
            # Read row 0
            row = store[0, :]
            assert len(row) == 5
            assert row[0] == 0.0
            # Read column
            col = store[:, 0]
            assert len(col) == 5
            store.close()

    def test_write_then_flush_and_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_flush.bin")
            store = BinaryStore.create(path, V=10, fill_value=0.0)
            store[3, 7] = 0.99
            store.flush()
            store.close()
            store2 = BinaryStore(path, mode="r")
            assert store2[3, 7] == 0.99
            store2.close()

    def test_fill(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_fill_all.bin")
            store = BinaryStore.create(path, V=8, fill_value=0.0)
            store.fill(0.42)
            assert store[0, 0] == 0.42
            assert store[7, 7] == 0.42
            assert store[3, 5] == 0.42
            store.close()


class TestBinaryStoreHelpers:
    """Tests for helper methods."""

    def test_coherency_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_check.bin")
            store = BinaryStore.create(path, V=50, fill_value=0.0)
            store[0, 1] = 0.5
            store[1, 0] = 0.5
            check = store.coherency_check()
            assert check["status"] == "ok"
            assert check["V"] == 50
            assert check["nonzero"] >= 2
            assert check["density"] > 0
            store.close()

    def test_estimate_optimal_V(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_est.bin")
            store = BinaryStore.create(path, V=100, fill_value=0.0)
            V_est = store.estimate_optimal_V(target_mb=800)
            # sqrt(800*1024*1024/4) ≈ sqrt(209715200) ≈ 14482
            assert 14000 < V_est < 15000
            store.close()

    def test_to_dense_numpy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_dense.bin")
            store = BinaryStore.create(path, V=5, fill_value=0.0)
            store[1, 2] = 0.5
            arr = store.to_dense_numpy()
            assert arr.shape == (5, 5)
            assert arr[1, 2] == 0.5
            store.close()

    @pytest.mark.slow
    def test_large_matrix(self):
        """Test a moderately large matrix (1000x1000 = 4MB)."""
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_large.bin")
            store = BinaryStore.create(path, V=1000, fill_value=0.0)
            store[500, 500] = 1.0
            store[999, 0] = 0.5
            assert store[500, 500] == 1.0
            assert store[999, 0] == 0.5
            store.close()


class TestBinaryStoreImportExport:
    """Tests for PyTorch import/export."""

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")
    def test_import_from_torch(self):
        import torch
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_import.bin")
            store = BinaryStore.create(path, V=10, fill_value=0.0)
            tensor = torch.zeros(10, 10)
            tensor[0, 1] = 0.8
            tensor[1, 0] = 0.8
            tensor[3, 4] = 0.6
            store.import_from_torch(tensor)
            assert store[0, 1] == 0.8
            assert store[3, 4] == 0.6
            store.close()

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not available")
    def test_export_to_torch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_export.bin")
            store = BinaryStore.create(path, V=5, fill_value=0.0)
            store[2, 3] = 0.7
            tensor = store.export_to_torch()
            assert tensor.shape == (5, 5)
            assert tensor[2, 3] == 0.7
            store.close()
