import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from jobs_app_traffic_monitor.models import AppTraffic
from jobs_app_traffic_monitor.ui.main_window import MainWindow


class _CollectorStub:
    def __init__(self) -> None:
        self.items: list[AppTraffic] = []

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def snapshot(self) -> list[AppTraffic]:
        return self.items


class MainWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.collector = _CollectorStub()
        self.window = MainWindow(self.collector)

    def tearDown(self) -> None:
        self.window.close()

    def test_shows_sampling_hint_until_data_arrives(self) -> None:
        self.window._refresh()
        self.assertFalse(self.window._empty_state.isHidden())

        self.collector.items = [
            AppTraffic("Example", None, None, False, (1,), 10, 5, 10, 5, 10, 5, 1)
        ]
        self.window._refresh()

        self.assertTrue(self.window._empty_state.isHidden())
        self.assertEqual(self.window._table.rowCount(), 1)

    def test_switches_between_dark_and_light_themes(self) -> None:
        self.window._toggle_theme()
        self.assertTrue(self.window._dark_mode)
        self.assertEqual(self.window._theme_button.text(), "☀️ 浅色")

        self.window._toggle_theme()
        self.assertFalse(self.window._dark_mode)
        self.assertEqual(self.window._theme_button.text(), "🌙 深色")


if __name__ == "__main__":
    unittest.main()
