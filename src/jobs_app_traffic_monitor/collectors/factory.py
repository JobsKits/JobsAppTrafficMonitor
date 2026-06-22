from __future__ import annotations

import platform

from jobs_app_traffic_monitor.collectors.base import TrafficCollector


def create_collector() -> TrafficCollector:
    system = platform.system()
    if system == "Darwin":
        from jobs_app_traffic_monitor.collectors.macos_nettop import MacOSNettopCollector

        return MacOSNettopCollector()
    if system == "Windows":
        from jobs_app_traffic_monitor.collectors.windows_etw import WindowsEtwCollector

        return WindowsEtwCollector()
    raise RuntimeError(f"暂不支持当前系统：{system}")

