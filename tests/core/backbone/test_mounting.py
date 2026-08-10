# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""掛載/釋放機制測試（§4.2 / §4.3 — mount/unmount + idle timeout + lazy mount）。"""

import time

from core.backbone.mountable import MountableWrapper, MountManager


class _FakeResource:
    """實作 Mountable 協定的假資源。"""

    def __init__(self):
        self.mounted = False
        self.mount_calls = 0
        self.unmount_calls = 0

    def mount(self):
        self.mounted = True
        self.mount_calls += 1
        return True

    def unmount(self):
        self.mounted = False
        self.unmount_calls += 1
        return True

    def is_mounted(self):
        return self.mounted

    def persistence_path(self):
        return "/fake/path.bin"


class TestMountableWrapper:
    def test_mount_unmount(self):
        r = _FakeResource()
        w = MountableWrapper(r, idle_timeout=100)
        assert w.mount() is True
        assert w.is_mounted()
        assert w.unmount() is True
        assert not w.is_mounted()

    def test_lazy_mount_on_access(self):
        r = _FakeResource()
        w = MountableWrapper(r, idle_timeout=100)
        resource = w.access()
        assert resource is r
        assert r.mount_calls == 1
        assert w.access_count == 1

    def test_idle_timeout_auto_unmount(self):
        r = _FakeResource()
        w = MountableWrapper(r, idle_timeout=0.05)
        w.mount()
        assert w.is_mounted()
        time.sleep(0.1)
        assert w.is_idle()
        assert w.sweep_if_idle() is True
        assert not w.is_mounted()

    def test_not_idle_while_mounted_fresh(self):
        r = _FakeResource()
        w = MountableWrapper(r, idle_timeout=100)
        w.mount()
        assert not w.is_idle()

    def test_unmount_idempotent(self):
        r = _FakeResource()
        w = MountableWrapper(r, idle_timeout=100)
        assert w.unmount() is True
        assert w.unmount() is True


class TestMountManager:
    def test_register_mount_mounted_map(self):
        mgr = MountManager()
        mgr.register("vision", _FakeResource())
        assert mgr.mount("vision") is True
        assert mgr.mounted() == {"vision": True}

    def test_access_lazy_mount(self):
        mgr = MountManager()
        r = _FakeResource()
        mgr.register("audio", r)
        resource = mgr.access("audio")
        assert resource is r
        assert r.mount_calls == 1

    def test_unmount_releases(self):
        mgr = MountManager()
        r = _FakeResource()
        mgr.register("vision", r)
        mgr.mount("vision")
        assert mgr.unmount("vision") is True
        assert r.unmount_calls == 1
        assert mgr.is_mounted("vision") is False

    def test_sweep_idle_resources(self):
        mgr = MountManager()
        r = _FakeResource()
        mgr.register("vision", r, idle_timeout=0.05)
        mgr.mount("vision")
        time.sleep(0.1)
        released = mgr.sweep()
        assert released == 1
        assert not mgr.is_mounted("vision")

    def test_sweep_keeps_active(self):
        mgr = MountManager()
        r = _FakeResource()
        mgr.register("vision", r, idle_timeout=100)
        mgr.mount("vision")
        assert mgr.sweep() == 0
        assert mgr.is_mounted("vision")

    def test_unknown_key_ops(self):
        mgr = MountManager()
        assert mgr.mount("nope") is False
        assert mgr.unmount("nope") is False
        assert mgr.access("nope") is None
        assert mgr.persistence_path("nope") == ""

    def test_unregister(self):
        mgr = MountManager()
        mgr.register("vision", _FakeResource())
        assert mgr.unregister("vision") is True
        assert not mgr.has("vision")


class TestBackboneMountIntegration:
    def test_backbone_register_mount(self):
        from core.backbone import get_backbone, reset_backbone

        reset_backbone()
        bb = get_backbone()
        r = _FakeResource()
        bb.register_mountable("vision", r, idle_timeout=100)
        assert bb.mount("vision") is True
        assert bb.mounted()["vision"] is True
        assert bb.access("vision") is r
        assert bb.unmount("vision") is True
        assert bb.mounted()["vision"] is False
