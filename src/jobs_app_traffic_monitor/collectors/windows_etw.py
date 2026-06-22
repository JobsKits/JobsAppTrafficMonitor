from __future__ import annotations

from jobs_app_traffic_monitor.collectors.base import TrafficCollector
from jobs_app_traffic_monitor.models import AppTraffic


class WindowsEtwCollector(TrafficCollector):
    """Windows ETW 采集器占位；下一版接入 Microsoft-Windows-Kernel-Network。"""

    def start(self) -> None:
        raise NotImplementedError("Windows ETW 采集器将在下一版实现")

    def stop(self) -> None:
        return None

    def snapshot(self) -> list[AppTraffic]:
        return []
