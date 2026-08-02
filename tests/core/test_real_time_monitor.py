"""core.real_time_monitor 即時監控模組測試"""

from apps.backend.src.core.real_time_monitor import (
    ActivityState,
    MonitorType,
    MouseData,
    RealTimeMonitor,
)


class TestMonitorType:
    def test_has_all_monitor_types(self):
        names = [m.name for m in MonitorType]
        assert names == [
            "MOUSE",
            "FILE_SYSTEM",
            "TIME",
            "SYSTEM_STATE",
            "USER_ACTIVITY",
            "AUDIO_STATE",
        ]

    def test_values_have_chinese_and_english(self):
        assert MonitorType.MOUSE.value[1] == "Global mouse position"
        assert MonitorType.FILE_SYSTEM.value[0] == "文件系统"


class TestActivityState:
    def test_has_user_states(self):
        assert ActivityState.IDLE.name == "IDLE"
        assert ActivityState.TYPING.name == "TYPING"
        assert ActivityState.UNKNOWN.name == "UNKNOWN"


class TestMouseData:
    def test_velocity_property(self):
        md = MouseData(x=10, y=0, velocity_x=3.0, velocity_y=4.0)
        assert md.velocity == 5.0

    def test_has_screen_defaults(self):
        md = MouseData(x=1, y=2)
        assert md.screen_width > 0
        assert md.screen_height > 0


class TestRealTimeMonitor:
    def test_constructible(self):
        rtm = RealTimeMonitor()
        assert rtm.mouse_monitor is not None
        assert rtm.file_monitor is not None
        assert rtm.time_monitor is not None
        assert rtm.system_monitor is not None
        assert rtm.activity_monitor is not None

    def test_get_monitor(self):
        rtm = RealTimeMonitor()
        assert rtm.get_monitor("mouse") == rtm.mouse_monitor
        assert rtm.get_monitor("file_system") == rtm.file_monitor
        assert rtm.get_monitor("nonexistent") is None
