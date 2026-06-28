from __future__ import annotations

from PySide6.QtCore import QEvent, QProcess, QTimer, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from jobs_app_traffic_monitor.collectors.base import TrafficCollector


def format_bytes(value: float, suffix: str = "") -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    amount = float(value)
    for unit in units:
        if abs(amount) < 1024 or unit == units[-1]:
            return f"{amount:.1f} {unit}{suffix}"
        amount /= 1024
    return f"{amount:.1f} TB{suffix}"


class MainWindow(QMainWindow):
    HEADERS = ("App", "PID", "下载速度", "上传速度", "本次下载", "本次上传", "累计流量")

    def __init__(self, collector: TrafficCollector) -> None:
        super().__init__()
        self._collector = collector
        self._dark_mode = False
        self.setWindowTitle("Jobs App Traffic Monitor")
        self.resize(1040, 680)

        title = QLabel("App 实时流量")
        title.setStyleSheet("font-size: 24px; font-weight: 700; margin: 8px 0;")
        self._theme_button = QPushButton("🌙 深色")
        self._theme_button.setToolTip("切换深色主题")
        self._theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_button.clicked.connect(self._toggle_theme)
        title_layout = QHBoxLayout()
        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(self._theme_button)

        subtitle = QLabel("仅统计字节数，不读取或分析数据内容")
        subtitle.setStyleSheet("color: #7a7a7a; margin-bottom: 8px;")

        self._table = QTableWidget(0, len(self.HEADERS))
        self._table.setHorizontalHeaderLabels(self.HEADERS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.verticalHeader().setVisible(False)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for column in range(1, len(self.HEADERS)):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self._empty_state = QLabel("正在采集网络流量，首次数据约 5 秒后显示……", self._table.viewport())
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setStyleSheet(
            "background: transparent; color: #6f6f6f; font-size: 16px;"
        )
        self._table.viewport().installEventFilter(self)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.addLayout(title_layout)
        layout.addWidget(subtitle)
        layout.addWidget(self._table)
        self.setCentralWidget(container)

        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self._refresh)
        self._collector.start()
        self._timer.start()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._resize_empty_state()

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if watched is self._table.viewport() and event.type() == QEvent.Type.Resize:
            self._resize_empty_state()
        return super().eventFilter(watched, event)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._timer.stop()
        self._collector.stop()
        super().closeEvent(event)

    def _refresh(self) -> None:
        traffic = self._collector.snapshot()
        self._empty_state.setVisible(not traffic)
        self._resize_empty_state()
        self._table.setRowCount(len(traffic))
        for row, item in enumerate(traffic):
            values = (
                item.app_name,
                ", ".join(str(pid) for pid in item.pids),
                format_bytes(item.download_rate, "/s"),
                format_bytes(item.upload_rate, "/s"),
                format_bytes(item.sample_bytes_in),
                format_bytes(item.sample_bytes_out),
                format_bytes(item.total_bytes),
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if column == 0:
                    cell.setData(Qt.ItemDataRole.UserRole, item.reveal_path)
                    if not item.is_system:
                        cell.setForeground(QColor("#d70015"))
                        cell.setToolTip("外源 App")
                if column > 0:
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if column == 2:
                    cell.setForeground(QColor("#1677ff"))
                elif column == 3:
                    cell.setForeground(QColor("#cf5b16"))
                self._table.setItem(row, column, cell)

    def _resize_empty_state(self) -> None:
        self._empty_state.setGeometry(self._table.viewport().rect())

    def _toggle_theme(self) -> None:
        self._dark_mode = not self._dark_mode
        if self._dark_mode:
            self.setStyleSheet(
                "QMainWindow, QWidget { background: #1f1f1f; color: #f2f2f2; }"
                "QTableWidget { background: #242424; alternate-background-color: #2c2c2c; "
                "gridline-color: #555; }"
                "QHeaderView::section { background: #333; color: #f2f2f2; padding: 6px; "
                "border: 1px solid #555; }"
                "QPushButton { background: #3a3a3a; color: #f2f2f2; border: 1px solid #666; "
                "border-radius: 6px; padding: 6px 12px; }"
                "QPushButton:hover { background: #4a4a4a; }"
            )
            self._empty_state.setStyleSheet(
                "background: transparent; color: #b8b8b8; font-size: 16px;"
            )
            self._theme_button.setText("☀️ 浅色")
            self._theme_button.setToolTip("切换浅色主题")
            return

        self.setStyleSheet("")
        self._empty_state.setStyleSheet(
            "background: transparent; color: #6f6f6f; font-size: 16px;"
        )
        self._theme_button.setText("🌙 深色")
        self._theme_button.setToolTip("切换深色主题")

    def _show_context_menu(self, position) -> None:
        clicked_cell = self._table.itemAt(position)
        if clicked_cell is None:
            return

        row = clicked_cell.row()
        self._table.selectRow(row)
        app_cell = self._table.item(row, 0)
        reveal_path = app_cell.data(Qt.ItemDataRole.UserRole) if app_cell else None

        menu = QMenu(self)
        action = menu.addAction("在 Finder 中显示")
        action.setEnabled(bool(reveal_path))
        if reveal_path:
            action.triggered.connect(lambda: self._reveal_in_finder(reveal_path))
        menu.exec(self._table.viewport().mapToGlobal(position))

    @staticmethod
    def _reveal_in_finder(path: str) -> None:
        QProcess.startDetached("/usr/bin/open", ["-R", path])
