import pytest

def test_example() -> None:
    assert 1 == 1

if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])