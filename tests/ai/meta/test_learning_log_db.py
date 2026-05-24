import sys
import pytest
import os

_MODULE_MOCKS = {}
for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


@pytest.fixture
def db(tmp_path):
    from apps.backend.src.ai.meta.learning_log_db import LearningLogDB
    db_path = str(tmp_path / "test_learning_log.db")
    db_instance = LearningLogDB(db_path)
    yield db_instance
    if os.path.exists(db_path):
        os.remove(db_path)


class TestLearningLogDBInit:
    def test_db_file_created(self, tmp_path):
        from apps.backend.src.ai.meta.learning_log_db import LearningLogDB
        db_path = str(tmp_path / "created.db")
        db = LearningLogDB(db_path)
        assert os.path.exists(db_path)
        db.delete_db_file()

    def test_init_invalid_path_raises(self, tmp_path):
        from apps.backend.src.ai.meta.learning_log_db import LearningLogDB
        invalid_path = str(tmp_path / "nonexistent" / "subdir" / "test.db")
        with pytest.raises(Exception):
            LearningLogDB(invalid_path)


class TestLearningLogDBAddEntry:
    def test_add_log_entry_returns_int(self, db):
        entry_id = db.add_log_entry({
            "strategy_id": "strat_a",
            "current_effectiveness": 0.85,
            "message": "test entry",
        })
        assert isinstance(entry_id, int)
        assert entry_id >= 1

    def test_add_log_entry_multiple_entries(self, db):
        id1 = db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.5, "message": "first"})
        id2 = db.add_log_entry({"strategy_id": "s2", "current_effectiveness": 0.6, "message": "second"})
        assert id2 == id1 + 1

    def test_add_log_entry_default_strategy(self, db):
        entry_id = db.add_log_entry({"current_effectiveness": 0.5})
        entries = db.get_all_log_entries()
        assert entries[0]["strategy_id"] == "unknown_strategy"

    def test_add_log_entry_default_timestamp(self, db):
        entry_id = db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.5})
        entries = db.get_all_log_entries()
        assert entries[0]["timestamp"] is not None

    def test_add_log_entry_null_effectiveness(self, db):
        entry_id = db.add_log_entry({"strategy_id": "s1", "message": "no effectiveness"})
        entries = db.get_all_log_entries()
        assert entries[0]["current_effectiveness"] is None

    def test_add_log_entry_null_message(self, db):
        entry_id = db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.5})
        entries = db.get_all_log_entries()
        assert entries[0]["message"] is None


class TestLearningLogDBGetEntries:
    def test_get_all_log_entries_empty(self, db):
        entries = db.get_all_log_entries()
        assert entries == []

    def test_get_all_log_entries_all(self, db):
        db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.8, "message": "a"})
        db.add_log_entry({"strategy_id": "s2", "current_effectiveness": 0.9, "message": "b"})
        entries = db.get_all_log_entries()
        assert len(entries) == 2

    def test_get_all_log_entries_filter_by_strategy(self, db):
        db.add_log_entry({"strategy_id": "filter_me", "current_effectiveness": 0.7, "message": "x"})
        db.add_log_entry({"strategy_id": "other", "current_effectiveness": 0.8, "message": "y"})
        entries = db.get_all_log_entries(strategy_id="filter_me")
        assert len(entries) == 1
        assert entries[0]["strategy_id"] == "filter_me"

    def test_get_all_log_entries_filter_no_match(self, db):
        db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.7, "message": "x"})
        entries = db.get_all_log_entries(strategy_id="nonexistent")
        assert entries == []

    def test_get_all_log_entries_returns_dict_with_all_keys(self, db):
        db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.75, "message": "test msg"})
        entries = db.get_all_log_entries()
        entry = entries[0]
        assert set(entry.keys()) == {"id", "timestamp", "strategy_id", "current_effectiveness", "message"}
        assert entry["strategy_id"] == "s1"
        assert entry["current_effectiveness"] == 0.75
        assert entry["message"] == "test msg"

    def test_get_all_log_entries_ordered_by_timestamp_desc(self, db):
        db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.5, "message": "old"})
        db.add_log_entry({"strategy_id": "s1", "current_effectiveness": 0.9, "message": "new"})
        entries = db.get_all_log_entries(strategy_id="s1")
        assert entries[0]["current_effectiveness"] == 0.9


class TestLearningLogDBDelete:
    def test_delete_db_file_removes_file(self, tmp_path):
        from apps.backend.src.ai.meta.learning_log_db import LearningLogDB
        db_path = str(tmp_path / "delete_me.db")
        db = LearningLogDB(db_path)
        assert os.path.exists(db_path)
        db.delete_db_file()
        assert not os.path.exists(db_path)

    def test_delete_db_file_nonexistent(self, db):
        db.delete_db_file()
        assert not os.path.exists(db.db_path)
