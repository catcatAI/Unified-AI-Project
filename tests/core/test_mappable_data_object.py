"""C4 — MappableDataObject unit tests"""

from core.shared.types.mappable_data_object import MappableDataObject


class TestMappableDataObject:

    def test_init_with_data(self):
        obj = MappableDataObject({"hello": "world"})
        assert obj.data == {"hello": "world"}
        assert obj.metadata == {}
        assert obj.compressed_data is None

    def test_init_with_metadata(self):
        obj = MappableDataObject("raw", {"source": "test"})
        assert obj.metadata == {"source": "test"}

    def test_compress_and_decompress_roundtrip(self):
        data = {"key": "value", "nested": [1, 2, 3]}
        obj = MappableDataObject(data)
        obj.compress()
        assert obj.compressed_data is not None
        result = obj.decompress()
        assert result == data

    def test_compress_none_data_does_nothing(self):
        obj = MappableDataObject(None)
        obj.compress()
        assert obj.compressed_data is None

    def test_decompress_without_compress_returns_none(self):
        obj = MappableDataObject("data")
        assert obj.decompress() is None

    def test_add_layer(self):
        obj = MappableDataObject("base")
        obj.add_layer("embedding", [0.1, 0.2, 0.3])
        assert obj.layers["embedding"] == [0.1, 0.2, 0.3]

    def test_get_layer_exists(self):
        obj = MappableDataObject("base")
        obj.add_layer("meta", {"version": 1})
        assert obj.get_layer("meta") == {"version": 1}

    def test_get_layer_missing(self):
        obj = MappableDataObject("base")
        assert obj.get_layer("nonexistent") is None

    def test_remove_layer(self):
        obj = MappableDataObject("base")
        obj.add_layer("temp", "value")
        obj.remove_layer("temp")
        assert obj.get_layer("temp") is None

    def test_remove_layer_nonexistent_does_nothing(self):
        obj = MappableDataObject("base")
        obj.remove_layer("nothing")  # no crash

    def test_to_dict_contains_all_fields(self):
        obj = MappableDataObject("data", {"version": 1})
        obj.add_layer("summary", "ok")
        d = obj.to_dict()
        assert d["data"] == "data"
        assert d["metadata"] == {"version": 1}
        assert d["layers"] == {"summary": "ok"}
        assert d["compressed"] is False

    def test_to_dict_shows_compressed_true(self):
        obj = MappableDataObject([1, 2, 3])
        obj.compress()
        d = obj.to_dict()
        assert d["compressed"] is True

    def test_from_dict_roundtrip(self):
        obj = MappableDataObject("original", {"tag": "test"})
        obj.add_layer("notes", "hello")
        d = obj.to_dict()
        restored = MappableDataObject.from_dict(d)
        assert restored.data == "original"
        assert restored.metadata == {"tag": "test"}
        assert restored.layers == {"notes": "hello"}

    def test_from_dict_with_compressed_data(self):
        obj = MappableDataObject("compressible")
        obj.compress()
        d = obj.to_dict()
        d["compressed_data"] = obj.compressed_data
        restored = MappableDataObject.from_dict(d)
        assert restored.compressed_data == obj.compressed_data
