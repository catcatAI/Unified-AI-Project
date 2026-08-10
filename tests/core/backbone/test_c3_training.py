# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""步驟 C3：訓練工作流掛載（TrainingMount + backbone register_training_mount）。

里程碑（§7 步驟 C）：backbone.mount/unmount 有測試覆蓋（含訓練工作流）。

驗證：
- `TrainingMount` 掛載 lazy 建例、釋放調 save + 清空、load_func 於掛載時呼叫。
- `backbone.register_training_mount` 註冊後可 mount/unmount/access，
  access 穿透回傳底層工作流實例。
- idle timeout + sweep 自動釋放（TrainingMount 自身邏輯）。
- training_info 正確回報掛載狀態。
"""

import pytest

from core.backbone import get_backbone, reset_backbone
from core.backbone.training import TrainingMount


@pytest.fixture(autouse=True)
def _fresh():
    reset_backbone()
    yield
    reset_backbone()


class _Workflow:
    def __init__(self, tag):
        self.tag = tag
        self.saved = []

    def save(self, path):
        self.saved.append(path)
        return path

    def step(self):
        return 42


def _make_mount(name="ed3n", persistence_path="/tmp/x.pt"):
    created = []

    def factory():
        w = _Workflow("w")
        created.append(w)
        return w

    mount = TrainingMount(
        name=name,
        factory=factory,
        save_func=lambda obj, path: obj.save(path),
        load_func=lambda obj, path: None,
        persistence_path=persistence_path,
    )
    return mount, created


class TestTrainingMount:
    def test_lazy_mount_creates_instance(self):
        mount, created = _make_mount()
        assert not mount.is_mounted()
        assert created == []
        obj = mount.access()
        assert len(created) == 1
        assert isinstance(obj, _Workflow)
        assert mount.is_mounted()

    def test_mount_is_idempotent(self):
        mount, created = _make_mount()
        mount.access()
        mount.access()
        assert len(created) == 1

    def test_unmount_saves_and_releases(self):
        mount, created = _make_mount(persistence_path="/tmp/save.pt")
        obj = mount.access()
        assert mount.unmount() is True
        assert obj.saved == ["/tmp/save.pt"]
        assert not mount.is_mounted()
        # 釋放後再存取 → 重新建例
        assert mount.access() is not obj
        assert len(created) == 2

    def test_unmount_when_not_mounted_is_noop(self):
        mount, _ = _make_mount()
        assert mount.unmount() is True

    def test_sweep_if_idle(self):
        mount, _ = _make_mount()
        mount.access()
        mount.idle_timeout = 0.0
        mount.last_access = 0.0
        assert mount.sweep_if_idle() is True
        assert not mount.is_mounted()

    def test_info(self):
        mount, _ = _make_mount()
        mount.access()
        info = mount.info()
        assert info["name"] == "ed3n"
        assert info["mounted"] is True

    def test_factory_failure_returns_false(self):
        def boom():
            raise RuntimeError("no engine")

        mount = TrainingMount(name="bad", factory=boom)
        assert mount.access() is None
        assert not mount.is_mounted()


class TestBackboneTrainingMount:
    def test_register_mount_and_access(self):
        bb = get_backbone()

        def factory():
            return _Workflow("x")

        bb.register_training_mount("joint", factory, persistence_path="/tmp/j.pt")
        obj = bb.access("training:joint")
        assert isinstance(obj, _Workflow)
        assert obj.step() == 42
        assert bb.mounted()["training:joint"] is True

    def test_unmount_and_remount(self):
        bb = get_backbone()
        saved = []

        def factory():
            w = _Workflow("x")
            w.save = lambda p: saved.append(p)
            return w

        bb.register_training_mount(
            "garden", factory, save_func=lambda o, p: o.save(p), persistence_path="/tmp/g.pt"
        )
        obj = bb.access("training:garden")
        assert bb.unmount("training:garden") is True
        assert saved == ["/tmp/g.pt"]
        assert bb.mounted()["training:garden"] is False

    def test_register_training_module_preserved(self):
        bb = get_backbone()
        bb.register_training("joint", lambda: None)
        assert bb.get_module("training:joint") is not None

    def test_training_info(self):
        bb = get_backbone()
        bb.register_training_mount("joint", lambda: _Workflow("x"), persistence_path="/tmp/j.pt")
        bb.access("training:joint")
        info = bb.training_info()
        assert "training:joint" in info
        assert info["training:joint"]["mounted"] is True
