from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

from jobs_app_traffic_monitor.collectors import create_collector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="按 App 实时统计上下行流量")
    parser.add_argument("--headless", action="store_true", help="在终端显示实时流量")
    parser.add_argument("--limit", type=int, default=10, help="终端模式显示的 App 数量")
    return parser


def run_headless(limit: int) -> int:
    collector = create_collector()
    collector.start()
    try:
        while True:
            time.sleep(1)
            items = collector.snapshot()[: max(limit, 1)]
            print("\033[2J\033[H", end="")
            print(f"{'App':<32} {'PID':>7} {'下载':>14} {'上传':>14} {'累计':>14}")
            for item in items:
                print(
                    f"{item.app_name[:32]:<32} {item.pids[0]:>7} "
                    f"{item.download_rate / 1024:>10.1f} KB/s "
                    f"{item.upload_rate / 1024:>10.1f} KB/s "
                    f"{item.total_bytes / 1024 / 1024:>10.1f} MB"
                )
    except KeyboardInterrupt:
        return 0
    finally:
        collector.stop()


def run_gui() -> int:
    if getattr(sys, "frozen", False):
        qt_platforms_dir = Path(sys._MEIPASS) / "platforms"  # type: ignore[attr-defined]
        os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(qt_platforms_dir))

    try:
        from PySide6.QtWidgets import QApplication

        from jobs_app_traffic_monitor.ui.main_window import MainWindow
    except ImportError:
        print("缺少 PySide6，请先执行：python -m pip install -e .", file=sys.stderr)
        return 2

    app = QApplication(sys.argv)
    window = MainWindow(create_collector())
    window.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    if args.headless:
        return run_headless(args.limit)
    return run_gui()
