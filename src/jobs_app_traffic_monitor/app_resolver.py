from __future__ import annotations

import plistlib
import subprocess
from dataclasses import dataclass
from pathlib import Path
from threading import Lock


@dataclass(frozen=True, slots=True)
class AppIdentity:
    name: str
    app_path: str | None
    reveal_path: str | None
    is_system: bool


class MacOSAppResolver:
    """把 PID 对应的可执行文件归并到所属 .app。"""

    def __init__(self) -> None:
        self._cache: dict[int, AppIdentity] = {}
        self._lock = Lock()

    def resolve(self, pid: int, process_name: str) -> AppIdentity:
        with self._lock:
            cached = self._cache.get(pid)
        if cached is not None:
            return cached

        identity = self._resolve_uncached(pid, process_name)
        with self._lock:
            self._cache[pid] = identity
        return identity

    @staticmethod
    def _resolve_uncached(pid: int, process_name: str) -> AppIdentity:
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "comm="],
                check=False,
                capture_output=True,
                text=True,
                timeout=1,
            )
        except (OSError, subprocess.SubprocessError):
            return AppIdentity(process_name, None, None, False)

        executable = result.stdout.strip()
        if not executable:
            return AppIdentity(process_name, None, None, False)

        marker = ".app/"
        marker_index = executable.find(marker)
        if marker_index < 0:
            return AppIdentity(
                process_name,
                None,
                executable,
                MacOSAppResolver._is_system_path(executable),
            )

        app_path = Path(executable[: marker_index + len(".app")])
        app_name = MacOSAppResolver._bundle_name(app_path) or app_path.stem
        app_path_text = str(app_path)
        return AppIdentity(
            app_name,
            app_path_text,
            app_path_text,
            MacOSAppResolver._is_system_path(app_path_text),
        )

    @staticmethod
    def _is_system_path(path: str) -> bool:
        normalized = str(Path(path))
        system_roots = (
            "/System/",
            "/usr/",
            "/bin/",
            "/sbin/",
            "/Library/Apple/",
        )
        return normalized == "/System" or normalized.startswith(system_roots)

    @staticmethod
    def _bundle_name(app_path: Path) -> str | None:
        info_plist = app_path / "Contents" / "Info.plist"
        try:
            with info_plist.open("rb") as file:
                info = plistlib.load(file)
        except (OSError, plistlib.InvalidFileException):
            return None

        for key in ("CFBundleDisplayName", "CFBundleName"):
            value = info.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
