from __future__ import annotations

import csv
import logging
import subprocess
import threading
import time
from dataclasses import dataclass

from jobs_app_traffic_monitor.app_resolver import MacOSAppResolver
from jobs_app_traffic_monitor.collectors.base import TrafficCollector
from jobs_app_traffic_monitor.models import AppTraffic, ProcessTraffic

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class _Counters:
    bytes_in: int
    bytes_out: int
    timestamp: float


def parse_nettop_row(line: str) -> tuple[str, int, int, int] | None:
    """解析 nettop CSV 行，返回进程名、PID、接收和发送字节。"""
    try:
        row = next(csv.reader([line]))
    except (csv.Error, StopIteration):
        return None
    if len(row) < 6 or row[0] == "time":
        return None

    process_field = row[1].strip()
    process_name, separator, pid_text = process_field.rpartition(".")
    if not separator or not process_name or not pid_text.isdigit():
        return None

    try:
        bytes_in = int(row[4] or 0)
        bytes_out = int(row[5] or 0)
    except ValueError:
        return None
    return process_name, int(pid_text), bytes_in, bytes_out


class MacOSNettopCollector(TrafficCollector):
    def __init__(self, stale_after: float = 5.0) -> None:
        self._stale_after = stale_after
        self._resolver = MacOSAppResolver()
        self._previous: dict[int, _Counters] = {}
        self._traffic: dict[int, ProcessTraffic] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="nettop-collector", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2)

    def snapshot(self) -> list[AppTraffic]:
        now = time.monotonic()
        with self._lock:
            stale_pids = [
                pid
                for pid, traffic in self._traffic.items()
                if now - traffic.updated_at > self._stale_after
            ]
            for pid in stale_pids:
                self._traffic.pop(pid, None)
                self._previous.pop(pid, None)
            processes = tuple(self._traffic.values())
        return self._aggregate_apps(processes)

    @staticmethod
    def _aggregate_apps(processes: tuple[ProcessTraffic, ...]) -> list[AppTraffic]:
        groups: dict[str, list[ProcessTraffic]] = {}
        for process in processes:
            key = process.app_path or f"pid:{process.pid}"
            groups.setdefault(key, []).append(process)

        apps = [
            AppTraffic(
                app_name=members[0].app_name,
                app_path=members[0].app_path,
                reveal_path=members[0].reveal_path,
                is_system=all(member.is_system for member in members),
                pids=tuple(sorted(member.pid for member in members)),
                bytes_in=sum(member.bytes_in for member in members),
                bytes_out=sum(member.bytes_out for member in members),
                sample_bytes_in=sum(member.sample_bytes_in for member in members),
                sample_bytes_out=sum(member.sample_bytes_out for member in members),
                download_rate=sum(member.download_rate for member in members),
                upload_rate=sum(member.upload_rate for member in members),
                updated_at=max(member.updated_at for member in members),
            )
            for members in groups.values()
        ]
        return sorted(apps, key=lambda item: item.total_bytes, reverse=True)

    def _run(self) -> None:
        command = ["nettop", "-P", "-L", "1", "-x"]
        while not self._stop_event.is_set():
            started_at = time.monotonic()
            try:
                result = subprocess.run(
                    command,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
            except FileNotFoundError:
                LOGGER.error("系统中未找到 nettop")
                return
            except subprocess.TimeoutExpired:
                LOGGER.warning("nettop 本次采样超时")
                continue

            if result.returncode != 0:
                LOGGER.error("nettop 采样失败：%s", result.stderr.strip() or result.returncode)
                self._stop_event.wait(1)
                continue

            for line in result.stdout.splitlines():
                parsed = parse_nettop_row(line)
                if parsed is not None:
                    self._consume(*parsed)

            remaining = max(1.0 - (time.monotonic() - started_at), 0.0)
            self._stop_event.wait(remaining)

    def _consume(self, process_name: str, pid: int, bytes_in: int, bytes_out: int) -> None:
        now = time.monotonic()
        identity = self._resolver.resolve(pid, process_name)

        with self._lock:
            previous = self._previous.get(pid)
            if previous is None or bytes_in < previous.bytes_in or bytes_out < previous.bytes_out:
                sample_in = 0
                sample_out = 0
                elapsed = 1.0
            else:
                sample_in = bytes_in - previous.bytes_in
                sample_out = bytes_out - previous.bytes_out
                elapsed = max(now - previous.timestamp, 0.001)

            self._previous[pid] = _Counters(bytes_in, bytes_out, now)
            self._traffic[pid] = ProcessTraffic(
                pid=pid,
                process_name=process_name,
                app_name=identity.name,
                app_path=identity.app_path,
                reveal_path=identity.reveal_path,
                is_system=identity.is_system,
                bytes_in=bytes_in,
                bytes_out=bytes_out,
                sample_bytes_in=sample_in,
                sample_bytes_out=sample_out,
                download_rate=sample_in / elapsed,
                upload_rate=sample_out / elapsed,
                updated_at=now,
            )
