from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProcessTraffic:
    pid: int
    process_name: str
    app_name: str
    app_path: str | None
    reveal_path: str | None
    is_system: bool
    bytes_in: int
    bytes_out: int
    sample_bytes_in: int
    sample_bytes_out: int
    download_rate: float
    upload_rate: float
    updated_at: float

    @property
    def total_bytes(self) -> int:
        return self.bytes_in + self.bytes_out


@dataclass(frozen=True, slots=True)
class AppTraffic:
    app_name: str
    app_path: str | None
    reveal_path: str | None
    is_system: bool
    pids: tuple[int, ...]
    bytes_in: int
    bytes_out: int
    sample_bytes_in: int
    sample_bytes_out: int
    download_rate: float
    upload_rate: float
    updated_at: float

    @property
    def total_bytes(self) -> int:
        return self.bytes_in + self.bytes_out
