from __future__ import annotations

from abc import ABC, abstractmethod

from jobs_app_traffic_monitor.models import AppTraffic


class TrafficCollector(ABC):
    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...

    @abstractmethod
    def snapshot(self) -> list[AppTraffic]: ...
