import sys, os, random, time, json, traceback
from datetime import datetime

from browser_engine.chrome_driver import ChromiumDriver
from action.scan_groups import GroupScanner
from action.comment import CommentGroups

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QSpinBox, QFileDialog, QMessageBox, QDialog,
    QFrame, QStatusBar, QProgressBar, QCheckBox,
    QAbstractItemView, QMenu, QAction, QHeaderView,
    QListWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor, QBrush

# ═══════════════════════════════════════════════════════════════════════════════
#  DARK STYLESHEET
# ═══════════════════════════════════════════════════════════════════════════════
DARK = """
QMainWindow, QDialog {
    background: #1e1e2e;
}
QWidget {
    background: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', Arial;
    font-size: 13px;
}
QLineEdit {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 5px 10px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
}
QLineEdit:focus { border-color: #89b4fa; }
QLineEdit:read-only { background: #2a2a3c; color: #a6adc8; }
QTextEdit {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 6px;
    color: #cdd6f4;
}
QTextEdit:focus { border-color: #89b4fa; }
QPushButton {
    background: #45475a;
    color: #cdd6f4;
    border: 1px solid #585b70;
    border-radius: 4px;
    padding: 6px 16px;
    font-size: 13px;
}
QPushButton:hover { background: #585b70; }
QPushButton:pressed { background: #313244; }
QPushButton:disabled { background: #313244; color: #6c7086; border-color: #45475a; }
QTableWidget {
    background: #181825;
    border: 1px solid #45475a;
    border-radius: 4px;
    gridline-color: #313244;
    selection-background-color: #45475a;
    selection-color: #cdd6f4;
    alternate-background-color: #1e1e2e;
}
QTableWidget::item { padding: 4px 6px; border: none; }
QTableWidget::item:selected { background: #45475a; }
QHeaderView::section {
    background: #313244;
    border: none;
    border-right: 1px solid #45475a;
    border-bottom: 1px solid #45475a;
    padding: 5px 8px;
    font-weight: bold;
    font-size: 12px;
    color: #89b4fa;
}
QHeaderView { background: #313244; }
QCheckBox { spacing: 6px; color: #cdd6f4; }
QCheckBox::indicator {
    width: 15px; height: 15px;
    border: 1px solid #585b70;
    border-radius: 3px;
    background: #313244;
}
QCheckBox::indicator:checked {
    background: #89b4fa;
    border-color: #89b4fa;
}
QSpinBox {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    padding: 3px 5px;
    color: #cdd6f4;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #45475a; border: none; width: 16px;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover { background: #585b70; }
QProgressBar {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 4px;
    text-align: right;
    padding-right: 6px;
    font-size: 11px;
    color: #a6adc8;
    min-height: 20px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #89b4fa, stop:1 #74c7ec);
    border-radius: 4px;
}
QStatusBar {
    background: #181825;
    border-top: 1px solid #45475a;
    font-size: 12px;
    color: #a6adc8;
}
QStatusBar QLabel { background: transparent; }
QGroupBox {
    border: 1px solid #45475a;
    border-radius: 6px;
    margin-top: 12px;
    background: #24273a;
    font-weight: bold;
    font-size: 13px;
    color: #89b4fa;
    padding-top: 4px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    background: #24273a;
    color: #89b4fa;
}
QScrollBar:vertical {
    background: #181825; width: 8px; border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a; border-radius: 4px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #181825; height: 8px; border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #45475a; border-radius: 4px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QMenu {
    background: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item { padding: 6px 20px; border-radius: 4px; color: #cdd6f4; }
QMenu::item:selected { background: #45475a; color: #89b4fa; }
QListWidget {
    background: #181825;
    border: 1px solid #45475a;
    border-radius: 4px;
    font-size: 12px;
}
QListWidget::item { padding: 3px 6px; }
QListWidget::item:selected { background: #45475a; color: #89b4fa; }
QMenuBar {
    background: #11111b;
    color: #cdd6f4;
}
"""

# ── Button style helpers ──────────────────────────────────────────────────────
def _btn(bg, bg_h, fg="#ffffff", fs=13, pad=8, bold=True, radius=4):
    b = "font-weight:bold;" if bold else ""
    return (f"QPushButton{{background:{bg};color:{fg};border:none;border-radius:{radius}px;"
            f"{b}font-size:{fs}px;padding:{pad}px;}}"
            f"QPushButton:hover{{background:{bg_h};}}"
            f"QPushButton:disabled{{background:#313244;color:#6c7086;}}")

BTN_GREEN = lambda fs=13, p=8: _btn("#40a02b", "#4caf30", fs=fs, pad=p)
BTN_RED   = lambda fs=13, p=8: _btn("#d20f39", "#e81144", fs=fs, pad=p)
BTN_BLUE  = lambda fs=13, p=6: _btn("#1e66f5", "#3b82f6", fs=fs, pad=p)
BTN_GRAY  = ("QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
             "border-radius:4px;font-size:13px;padding:5px 12px;}"
             "QPushButton:hover{background:#45475a;}")
BTN_NAV   = ("QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
             "border-radius:4px;font-size:14px;padding:2px 8px;"
             "min-width:30px;min-height:30px;}"
             "QPushButton:hover{background:#45475a;color:#89b4fa;}"
             "QPushButton:disabled{color:#45475a;background:#1e1e2e;border-color:#313244;}")

driver = None
# ═══════════════════════════════════════════════════════════════════════════════
#  LICENSE DIALOG
# ═══════════════════════════════════════════════════════════════════════════════
class LicenseDialog(QDialog):
    activated = pyqtSignal()

    def __init__(self, machine_id, parent=None):
        super().__init__(parent)
        self.machine_id = machine_id
        self.setWindowTitle("License - Kích hoạt phần mềm")
        self.setFixedSize(500, 290)
        self.setStyleSheet(DARK)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        lay.setContentsMargins(22, 22, 22, 22)

        t = QLabel("🔑  Kích hoạt bản quyền")
        t.setFont(QFont("Segoe UI", 14, QFont.Bold))
        t.setStyleSheet("color:#89b4fa;background:transparent;")
        lay.addWidget(t)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background:#45475a;max-height:1px;")
        lay.addWidget(sep)

        id_box = QGroupBox("Mã kích hoạt máy  —  copy & gửi qua Zalo 0961.006.186")
        id_lay = QHBoxLayout(id_box)
        id_lay.setContentsMargins(8, 8, 8, 8)
        self.mid = QLineEdit(self.machine_id)
        self.mid.setReadOnly(True)
        self.mid.setStyleSheet(
            "QLineEdit{background:#11111b;color:#a6e3a1;font-weight:bold;"
            "font-family:'Courier New';font-size:15px;letter-spacing:3px;"
            "border:1px solid #45475a;border-radius:4px;padding:6px 10px;}")
        btn_c = QPushButton("Copy")
        btn_c.setStyleSheet(BTN_GRAY)
        btn_c.setFixedWidth(70)
        btn_c.clicked.connect(lambda: QApplication.clipboard().setText(self.machine_id))
        id_lay.addWidget(self.mid)
        id_lay.addWidget(btn_c)
        lay.addWidget(id_box)

        key_box = QGroupBox("Nhập Key kích hoạt")
        key_lay = QVBoxLayout(key_box)
        key_lay.setContentsMargins(8, 8, 8, 8)
        self.key = QLineEdit()
        self.key.setPlaceholderText("Nhập Key tại đây...")
        self.key.setFont(QFont("Courier New", 13))
        key_lay.addWidget(self.key)
        lay.addWidget(key_box)

        self.st = QLabel("")
        self.st.setAlignment(Qt.AlignCenter)
        self.st.setStyleSheet("background:transparent;")
        lay.addWidget(self.st)

        row = QHBoxLayout()
        bc = QPushButton("Đóng")
        bc.setStyleSheet(BTN_GRAY)
        bc.clicked.connect(self.reject)
        bk = QPushButton("KÍCH HOẠT")
        bk.setStyleSheet(BTN_GREEN(14, 10))
        bk.setFixedHeight(38)
        bk.clicked.connect(self._activate)
        row.addWidget(bc)
        row.addWidget(bk)
        lay.addLayout(row)

    def _activate(self):
        k = self.key.text().strip().upper()
        if len(k.replace("-", "")) >= 8:
            self.st.setStyleSheet("color:#a6e3a1;font-weight:bold;background:transparent;")
            self.st.setText("✅  Kích hoạt thành công! Hạn: Vĩnh Viễn")
            self.activated.emit()
            QTimer.singleShot(1500, self.accept)


# ═══════════════════════════════════════════════════════════════════════════════
#  CHROMIUM WORKER
# ═══════════════════════════════════════════════════════════════════════════════
class ChromiumWorker(QThread):
    ready = pyqtSignal(object)

    def __init__(self, profile_name: str, parent=None):
        super().__init__(parent)
        self.profile_name = profile_name

    def run(self):
        try:
            print(f"[INFO] Mở Chrome cho profile: {self.profile_name}", flush=True)
            d = ChromiumDriver.get_driver(
                self.profile_name,
                start_url="https://www.facebook.com",
                no_images=True
            )
            self.ready.emit(d)
        except Exception as e:
            print(f"[ERROR] Lỗi mở Chrome: {e}", flush=True)
            self.ready.emit(None)


class GroupScannerWorker(QThread):
    result = pyqtSignal(dict)

    def __init__(self, driver, profile_name, parent=None):
        super().__init__(parent)
        self.driver = driver
        self.profile_name = profile_name

    def run(self):
        try:
            scanner = GroupScanner(self.driver, self.profile_name)
            res = scanner.scan_groups()
            self.result.emit(res)
        except Exception as e:
            print(f"[ERROR] Lỗi quét nhóm: {e}", flush=True)
            self.result.emit({
                'success': False,
                'message': f'Lỗi quét nhóm: {str(e)}',
                'groups': [],
            })


# ═══════════════════════════════════════════════════════════════════════════════
#  POST GROUPS WORKER  — FIX: truyền log_callback, success_callback, fail_callback
# ═══════════════════════════════════════════════════════════════════════════════
class PostGroupsWorker(QThread):
    log_signal     = pyqtSignal(str)
    success_signal = pyqtSignal(str, str, str)   # ts, group_name, post_url
    fail_signal    = pyqtSignal(str, str, str)    # ts, group_name, error

    def __init__(self, driver, data, parent=None):
        super().__init__(parent)
        self.driver = driver
        self.data   = data

    def run(self):
        try:
            from action.post_groups import PostGroups
            poster = PostGroups(
                self.driver,
                self.data,
                log_callback=self.log_signal.emit,
                success_callback=self.success_signal.emit,
                fail_callback=self.fail_signal.emit,
            )
            poster.main_post()
        except Exception as e:
            print(f"[ERROR] Lỗi đăng nhóm: {e}", flush=True)
            self.log_signal.emit(f'❌ Lỗi: {str(e)}')


# ═══════════════════════════════════════════════════════════════════════════════
#  COMMENT GROUPS WORKER  
# ═══════════════════════════════════════════════════════════════════════════════
class CommentGroupsWorker(QThread):
    log_signal     = pyqtSignal(str)
    success_signal = pyqtSignal(str, str, str)   # ts, post_url, group_name
    fail_signal    = pyqtSignal(str, str, str)    # ts, post_url, error

    def __init__(self, driver, data, parent=None):
        super().__init__(parent)
        self.driver = driver
        self.data   = data

    def run(self):
        try:
            from action.comment import CommentGroups
            cmter = CommentGroups(
                self.driver,
                self.data,
                log_callback=self.log_signal.emit,
                success_callback=self.success_signal.emit,
                fail_callback=self.fail_signal.emit,
            )
            cmter.execute()
        except Exception as e:
            print(f"[ERROR] Lỗi comment nhóm: {e}", flush=True)
            self.log_signal.emit(f'❌ Lỗi: {str(e)}')


# ═══════════════════════════════════════════════════════════════════════════════
#  FACEBOOK WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class FacebookWindow(QMainWindow):
    window_closed = pyqtSignal(str)

    def __init__(self, profile_name: str):
        super().__init__()
        self.profile_name  = profile_name
        self.setWindowTitle(f"Tiến Khoa  ·  {profile_name}")
        self.resize(1400, 860)
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(DARK)
        self._running      = False
        self._progress_val = 0
        self._timer        = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._driver  = None
        self._worker  = None
        self._post_worker = None
        self._cmt_worker = None
        self._opening = False
        self._current_tab = "post"  # Track current active tab
        self._total_groups = 0
        self._done_groups  = 0

        self._build()
        QTimer.singleShot(500, self._open_chrome)

    def closeEvent(self, e):
        if self._timer.isActive():
            self._timer.stop()
        if self._driver is not None:
            ChromiumDriver.close_driver(self._driver)
            self._driver = None
        if self._worker is not None:
            if self._worker.isRunning():
                self._worker.quit()
                self._worker.wait(3000)
            self._worker = None
        if self._post_worker is not None:
            if self._post_worker.isRunning():
                self._post_worker.quit()
                self._post_worker.wait(3000)
            self._post_worker = None
        if self._cmt_worker is not None:
            if self._cmt_worker.isRunning():
                self._cmt_worker.quit()
                self._cmt_worker.wait(3000)
            self._cmt_worker = None
        self._opening = False
        self.window_closed.emit(self.profile_name)
        super().closeEvent(e)

    def _open_chrome(self):
        if self._driver is not None or self._opening:
            return
        self._opening = True
        self._worker  = ChromiumWorker(self.profile_name)
        self._worker.ready.connect(self._on_chrome_ready)
        self._worker.start()

    def _on_chrome_ready(self, driver):
        self._opening = False
        if driver is not None:
            self._driver = driver
            print(f"[SUCCESS] ✅ Chrome đã mở cho {self.profile_name}", flush=True)
        else:
            self._driver = None
            print(f"[ERROR] ❌ Không mở được Chrome cho {self.profile_name}", flush=True)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_tabbar())

        self._pg_group    = self._build_group()
        self._pg_page     = self._build_page()
        self._pg_settings = self._build_settings()

        for p in [self._pg_group, self._pg_page, self._pg_settings]:
            root.addWidget(p)

        sb = QStatusBar()
        sb.setStyleSheet("background:#11111b;border-top:1px solid #313264;"
                         "font-size:12px;color:#6c7086;")
        self.setStatusBar(sb)
        self._sb = sb
        self._switch("group")

    def _make_header(self):
        h = QWidget()
        h.setStyleSheet("background:#11111b;border-bottom:1px solid #313244;")
        h.setFixedHeight(46)
        lay = QHBoxLayout(h)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        fb_badge = QLabel("  fb  ")
        fb_badge.setFixedHeight(28)
        fb_badge.setAlignment(Qt.AlignCenter)
        fb_badge.setStyleSheet(
            "background:#1877f2;color:white;font-weight:bold;"
            "font-size:13px;border-radius:6px;padding:0 8px;")

        lbl = QLabel(f"Tiến Khoa   ·   {self.profile_name}")
        lbl.setStyleSheet(
            "color:#cdd6f4;font-weight:bold;font-size:14px;background:transparent;")

        def pill(txt, bg):
            b = QPushButton(txt)
            b.setStyleSheet(
                f"QPushButton{{background:{bg};color:white;border:none;"
                f"border-radius:10px;padding:4px 14px;font-size:12px;font-weight:bold;}}"
                f"QPushButton:hover{{opacity:0.85;}}")
            b.setFixedHeight(26)
            return b

        lay.addWidget(fb_badge)
        lay.addWidget(lbl)
        lay.addSpacing(12)
        lay.addWidget(pill("Nội dung", "#40a02b"))
        lay.addWidget(pill("Cấu hình AI", "#1e66f5"))
        lay.addStretch()
        return h

    def _make_tabbar(self):
        bar = QWidget()
        bar.setStyleSheet("background:#181825;border-bottom:1px solid #313244;")
        bar.setFixedHeight(44)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._tb = {}
        for key, txt in [("group",    "  ĐĂNG NHÓM  "),
                          ("page",     "  ĐĂNG PAGE  "),
                          ("settings", "  CÁCH CANH  ")]:
            b = QPushButton(txt)
            b.setFixedHeight(44)
            b.setMinimumWidth(148)
            b.clicked.connect(lambda _, k=key: self._switch(k))
            self._tb[key] = b
            lay.addWidget(b)
        lay.addStretch()
        return bar

    def _switch(self, tab):
        self._cur_tab = tab
        self._pg_group.setVisible(tab == "group")
        self._pg_page.setVisible(tab == "page")
        self._pg_settings.setVisible(tab == "settings")

        ACT = ("QPushButton{background:#1e1e2e;color:#89b4fa;border:none;"
               "border-bottom:2px solid #89b4fa;font-weight:bold;font-size:13px;"
               "padding:0 20px;min-width:148px;height:44px;}")
        OFF = ("QPushButton{background:#181825;color:#6c7086;border:none;"
               "border-bottom:2px solid transparent;font-weight:bold;font-size:13px;"
               "padding:0 20px;min-width:148px;height:44px;}"
               "QPushButton:hover{background:#1e1e2e;color:#a6adc8;}")
        for k, b in self._tb.items():
            b.setStyleSheet(ACT if k == tab else OFF)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: ĐĂNG NHÓM
    # ══════════════════════════════════════════════════════════════════════════
    def _build_group(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._make_group_left())
        lay.addWidget(self._make_group_center(), 1)
        lay.addWidget(self._make_group_right())
        return w

    def _make_group_left(self):
        p = QWidget()
        p.setStyleSheet("background:#181825;border-right:1px solid #313244;")
        p.setFixedWidth(316)
        lay = QVBoxLayout(p)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        fr = QHBoxLayout()
        fi = QLineEdit()
        fi.setPlaceholderText("🔍  Tìm nhóm...")
        fi.setFixedHeight(28)
        fi.setStyleSheet(
            "QLineEdit{background:#313244;border:1px solid #45475a;"
            "border-radius:4px;padding:2px 10px;font-size:12px;color:#cdd6f4;}"
            "QLineEdit:focus{border-color:#89b4fa;}")
        fb_btn = QPushButton("Lọc")
        fb_btn.setFixedSize(52, 28)
        fb_btn.setStyleSheet(BTN_GRAY)
        fr.addWidget(fi, 1)
        fr.addWidget(fb_btn)
        lay.addLayout(fr)

        self._gt = QTableWidget()
        self._gt.setColumnCount(4)
        self._gt.setHorizontalHeaderLabels(["✓", "#", "ID Nhóm", "Tên Nhóm"])
        self._gt.horizontalHeader().setStretchLastSection(True)
        self._gt.setColumnWidth(0, 30)
        self._gt.setColumnWidth(1, 32)
        self._gt.setColumnWidth(2, 90)
        self._gt.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._gt.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._gt.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._gt.setAlternatingRowColors(True)
        self._gt.verticalHeader().setVisible(False)
        self._gt.setShowGrid(False)
        self._gt.setContextMenuPolicy(Qt.CustomContextMenu)
        self._gt.customContextMenuRequested.connect(self._group_menu)
        self._gt.setStyleSheet(
            "QTableWidget{border:1px solid #45475a;border-radius:4px;font-size:12px;"
            "background:#181825;alternate-background-color:#1e1e2e;}"
            "QTableWidget::item{padding:5px 6px;border:none;}"
            "QTableWidget::item:selected{background:#45475a;color:#89b4fa;}"
            "QHeaderView::section{background:#313244;font-size:11px;color:#89b4fa;"
            "border:none;border-bottom:1px solid #45475a;padding:5px 6px;}")
        self._load_groups()
        lay.addWidget(self._gt, 1)

        br = QHBoxLayout()
        br.setSpacing(6)
        b1 = QPushButton("⬇  LẤY DS NHÓM")
        b1.setFixedHeight(34)
        b1.setStyleSheet(BTN_GREEN(12, 6))
        b1.clicked.connect(self._scan_groups)
        b2 = QPushButton("📂  LOAD DATA")
        b2.setFixedHeight(34)
        b2.setStyleSheet(BTN_GRAY)
        br.addWidget(b1)
        br.addWidget(b2)
        lay.addLayout(br)
        return p

    def _scan_groups(self):
        if self._driver is None:
            self._log_msg('<span style="color:#f38ba8;font-size:11px;">'
                          '[WARN] Chrome chưa mở hoặc chưa sẵn sàng.</span>')
            return
        if hasattr(self, '_scan_worker') and self._scan_worker is not None:
            if self._scan_worker.isRunning():
                self._log_msg('<span style="color:#fab387;font-size:11px;">'
                              '[WARN] Đang quét, vui lòng chờ...</span>')
                return

        self._log_msg('<span style="color:#89b4fa;font-size:11px;">'
                      '[INFO] Đang lấy danh sách nhóm...</span>')

        self._scan_worker = GroupScannerWorker(self._driver, self.profile_name)
        self._scan_worker.result.connect(self._on_scan_groups_done)
        self._scan_worker.finished.connect(self._on_scan_worker_finished)
        self._scan_worker.start()

    def _on_scan_groups_done(self, res: dict):
        ts = datetime.now().strftime("%H:%M:%S")
        if not res.get('success'):
            msg = res.get('message', 'Lỗi không xác định')
            self._log_msg(f'<span style="color:#f38ba8;font-size:11px;">'
                          f'[{ts}] ✖ {msg}</span>')
            return

        groups = res.get('groups', [])
        self._log_msg(f'<span style="color:#a6e3a1;font-size:11px;">'
                      f'[{ts}] ✔ {res.get("message", "")} ({len(groups)} nhóm)</span>')

        profile_file = os.path.join('data', 'profile.json')
        try:
            os.makedirs('data', exist_ok=True)
            profiles = []
            if os.path.isfile(profile_file):
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            found = False
            for p in profiles:
                if p.get('profile') == self.profile_name:
                    p['groups'] = groups
                    found = True
                    break
            if not found:
                profiles.append({'profile': self.profile_name, 'groups': groups})
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, ensure_ascii=False, indent=4)
            print(f"[SUCCESS] Lưu {len(groups)} groups cho {self.profile_name}", flush=True)
        except Exception as e:
            print(f"[ERROR] Lỗi lưu groups: {e}", flush=True)

        self._gt.setRowCount(0)
        for i, g in enumerate(groups):
            self._gt.insertRow(i)
            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox { margin-left: 8px; }")
            self._gt.setCellWidget(i, 0, chk)
            si = QTableWidgetItem(str(i + 1))
            si.setTextAlignment(Qt.AlignCenter)
            self._gt.setItem(i, 1, si)
            self._gt.setItem(i, 2, QTableWidgetItem(g.get('url', '')))
            self._gt.setItem(i, 3, QTableWidgetItem(g.get('name', '')))
            self._gt.setRowHeight(i, 28)

    def _on_scan_worker_finished(self):
        if hasattr(self, '_scan_worker') and self._scan_worker is not None:
            self._scan_worker.deleteLater()
            self._scan_worker = None

    # ── Log helpers ───────────────────────────────────────────────────────────
    def _log_msg(self, html: str):
        """Ghi log HTML vào nhật ký."""
        self._log.append(html)

    def _on_post_log(self, msg: str):
        """Callback nhận log từ PostGroupsWorker."""
        ts = datetime.now().strftime("%H:%M:%S")
        if '✔' in msg or '✅' in msg or 'SUCCESS' in msg:
            color = '#a6e3a1'
        elif '❌' in msg or '✖' in msg or 'ERROR' in msg:
            color = '#f38ba8'
        elif '⏳' in msg or '⏱' in msg or 'Chờ' in msg or 'chờ' in msg:
            color = '#f9e2af'
        else:
            color = '#cdd6f4'
        self._log.append(
            f'<span style="color:{color};font-size:11px;">[{ts}] {msg}</span>')

    def _on_post_success(self, ts: str, group_name: str, post_url: str):
        """Thêm vào bảng kết quả thành công."""
        r = self._suc.rowCount()
        self._suc.insertRow(r)
        for j, v in enumerate([ts, group_name, post_url]):
            self._suc.setItem(r, j, QTableWidgetItem(v))
        self._suc.scrollToBottom()

    def _on_post_fail(self, ts: str, group_name: str, error: str):
        """Thêm vào bảng kết quả lỗi."""
        r = self._err.rowCount()
        self._err.insertRow(r)
        for j, v in enumerate([ts, group_name, error]):
            self._err.setItem(r, j, QTableWidgetItem(v))
        self._err.scrollToBottom()

    # ── Comment handlers ───────────────────────────────────────────────────────
    def _on_cmt_log(self, msg: str):
        """Callback nhận log từ CommentGroupsWorker."""
        ts = datetime.now().strftime("%H:%M:%S")
        if '✔' in msg or '✅' in msg or 'SUCCESS' in msg:
            color = '#a6e3a1'
        elif '❌' in msg or '✖' in msg or 'ERROR' in msg:
            color = '#f38ba8'
        elif '⏳' in msg or '⏱' in msg or 'Chờ' in msg or 'chờ' in msg:
            color = '#f9e2af'
        else:
            color = '#cdd6f4'
        self._log.append(
            f'<span style="color:{color};font-size:11px;">[{ts}] {msg}</span>')

    def _on_cmt_success(self, ts: str, post_url: str, group_name: str):
        """Thêm vào bảng kết quả thành công comment."""
        r = self._suc.rowCount()
        self._suc.insertRow(r)
        for j, v in enumerate([ts, group_name, post_url]):
            self._suc.setItem(r, j, QTableWidgetItem(v))
        self._suc.scrollToBottom()
        self._done_groups += 1
        self._update_progress()

    def _on_cmt_fail(self, ts: str, post_url: str, error: str):
        """Thêm vào bảng kết quả lỗi comment."""
        r = self._err.rowCount()
        self._err.insertRow(r)
        for j, v in enumerate([ts, post_url, error]):
            self._err.setItem(r, j, QTableWidgetItem(v))
        self._err.scrollToBottom()
        self._done_groups += 1
        self._update_progress()

    def _on_cmt_finished(self):
        self._running = False
        self._timer.stop()
        self._pbar.setValue(100)
        self._set_btn_enabled(True)
        self._st_lbl.setText("✔ Hoàn thành")
        if hasattr(self, '_cmt_worker') and self._cmt_worker is not None:
            self._cmt_worker.deleteLater()
            self._cmt_worker = None


    def _load_groups(self):
        groups = []
        profile_file = os.path.join('data', 'profile.json')
        if os.path.isfile(profile_file):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                for p in profiles:
                    if p.get('profile') == self.profile_name:
                        groups = p.get('groups', [])
                        break
            except Exception as e:
                print(f"[ERROR] Lỗi load groups: {e}", flush=True)

        self._gt.setRowCount(len(groups))
        for i, g in enumerate(groups):
            chk = QCheckBox()
            chk.setStyleSheet("QCheckBox { margin-left: 8px; }")
            self._gt.setCellWidget(i, 0, chk)
            si = QTableWidgetItem(str(i + 1))
            si.setTextAlignment(Qt.AlignCenter)
            self._gt.setItem(i, 1, si)
            if isinstance(g, dict):
                gurl = g.get('url', '')
                gnm  = g.get('name', '')
            else:
                gurl = g[0] if len(g) > 0 else ''
                gnm  = g[1] if len(g) > 1 else ''
            self._gt.setItem(i, 2, QTableWidgetItem(gurl))
            self._gt.setItem(i, 3, QTableWidgetItem(gnm))
            self._gt.setRowHeight(i, 28)

    def _group_menu(self, pos):
        m = QMenu(self)
        a1 = QAction("✓ Chọn tất cả", self)
        a1.triggered.connect(self._check_all_groups)
        m.addAction(a1)
        a2 = QAction("✗ Bỏ chọn tất cả", self)
        a2.triggered.connect(self._uncheck_all_groups)
        m.addAction(a2)
        m.addSeparator()
        a3 = QAction("⚫ Chọn những nhóm bôi đen", self)
        a3.triggered.connect(self._check_colored_groups)
        m.addAction(a3)
        m.exec_(self._gt.viewport().mapToGlobal(pos))

    def _check_all_groups(self):
        for i in range(self._gt.rowCount()):
            chk = self._gt.cellWidget(i, 0)
            if isinstance(chk, QCheckBox):
                chk.setChecked(True)

    def _uncheck_all_groups(self):
        for i in range(self._gt.rowCount()):
            chk = self._gt.cellWidget(i, 0)
            if isinstance(chk, QCheckBox):
                chk.setChecked(False)

    def _check_colored_groups(self):
        for i in range(self._gt.rowCount()):
            item = self._gt.item(i, 1)
            if item and item.isSelected():
                chk = self._gt.cellWidget(i, 0)
                if isinstance(chk, QCheckBox):
                    chk.setChecked(True)

    def _make_group_center(self):
        p = QWidget()
        lay = QVBoxLayout(p)
        lay.setContentsMargins(10, 10, 10, 8)
        lay.setSpacing(8)

        self._gb_nd = QGroupBox("📝  Nội dung bài viết")
        gbl = QVBoxLayout(self._gb_nd)
        gbl.setContentsMargins(10, 8, 10, 10)

        # ── Hướng dẫn spin content ────────────────────────────────
        spin_hint = QLabel(
            "💡 Spin bằng dấu  |  (pipe)  ·  Mỗi đoạn cách nhau bằng  |  sẽ random 1 đoạn\n"
            "Ví dụ:  Nội dung 1 | Nội dung 2 | Nội dung 3   →  tự động chọn ngẫu nhiên 1 đoạn")
        spin_hint.setStyleSheet(
            "color:#6c7086;font-size:11px;font-style:italic;background:transparent;")
        spin_hint.setWordWrap(True)
        gbl.addWidget(spin_hint)

        self._content = QTextEdit()
        self._content.setPlaceholderText(
            "Nhập nội dung vào đây...\n\n"
            "Spin bằng | :  Nội dung A | Nội dung B | Nội dung C\n"
            "Hoặc spin từng từ bằng {}: Bán nhà {quận 1|q1|Q.1}, giá {tốt|hợp lý}")
        self._content.setMinimumHeight(140)
        self._content.setStyleSheet(
            "QTextEdit{background:#181825;border:1px solid #45475a;border-radius:6px;"
            "font-size:13px;color:#cdd6f4;padding:8px;}"
            "QTextEdit:focus{border-color:#89b4fa;}")
        gbl.addWidget(self._content)
        lay.addWidget(self._gb_nd)

        gb_av = QGroupBox("🖼  Danh sách ảnh / Video")
        gb_av.setFixedHeight(112)
        avl = QHBoxLayout(gb_av)
        avl.setContentsMargins(10, 6, 10, 10)
        self._media = QListWidget()
        self._media.setStyleSheet(
            "QListWidget{background:#181825;border:1px solid #45475a;border-radius:4px;"
            "font-size:12px;color:#cdd6f4;}"
            "QListWidget::item:selected{background:#45475a;color:#89b4fa;}")
        avr = QVBoxLayout()
        avr.setSpacing(4)
        for txt in ["+ Thêm", "✕ Xóa", "⊘ Clear"]:
            b = QPushButton(txt)
            b.setFixedSize(90, 26)
            b.setStyleSheet(BTN_GRAY)
            if "Thêm" in txt:
                b.clicked.connect(self._add_media)
            elif "Xóa" in txt:
                b.clicked.connect(self._rm_media)
            elif "Clear" in txt:
                b.clicked.connect(self._media.clear)
            avr.addWidget(b)
        avr.addStretch()
        avl.addWidget(self._media, 1)
        avl.addLayout(avr)
        lay.addWidget(gb_av)

        sub_bar = QWidget()
        sub_bar.setStyleSheet(
            "background:#181825;border:1px solid #45475a;border-radius:6px;")
        sub_bar.setFixedHeight(42)
        sl = QHBoxLayout(sub_bar)
        sl.setContentsMargins(4, 4, 4, 4)
        sl.setSpacing(4)
        self._sb_btns = {}
        for k, txt in [("post", "ĐĂNG BÀI"), ("comment", "COMMENT"), ("uptop", "UP TOP")]:
            b = QPushButton(txt)
            b.setFixedHeight(32)
            b.clicked.connect(lambda _, k=k: self._sub_switch(k))
            self._sb_btns[k] = b
            sl.addWidget(b)
        sl.addStretch()
        lay.addWidget(sub_bar)
        self._sub_switch("post")

        self._pnl_main  = self._make_settings_panel()
        self._pnl_comment = self._make_comment_panel()
        self._pnl_uptop = self._make_uptop_panel()
        lay.addWidget(self._pnl_main)
        lay.addWidget(self._pnl_comment)
        lay.addWidget(self._pnl_uptop)
        self._pnl_comment.setVisible(False)
        self._pnl_uptop.setVisible(False)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        
        # 3 nút bắt đầu khác nhau cho 3 tab
        self._btn_start_post = QPushButton("▶  BẮT ĐẦU ĐĂNG BÀI")
        self._btn_start_post.setFixedHeight(48)
        self._btn_start_post.setStyleSheet(BTN_GREEN(15, 10))
        self._btn_start_post.clicked.connect(lambda: self._start_action("post"))
        
        self._btn_start_comment = QPushButton("▶  BẮT ĐẦU COMMENT")
        self._btn_start_comment.setFixedHeight(48)
        self._btn_start_comment.setStyleSheet(BTN_GREEN(15, 10))
        self._btn_start_comment.clicked.connect(lambda: self._start_action("comment"))
        self._btn_start_comment.setVisible(False)
        
        self._btn_start_uptop = QPushButton("▶  BẮT ĐẦU UP TOP")
        self._btn_start_uptop.setFixedHeight(48)
        self._btn_start_uptop.setStyleSheet(BTN_GREEN(15, 10))
        self._btn_start_uptop.clicked.connect(lambda: self._start_action("uptop"))
        self._btn_start_uptop.setVisible(False)
        
        self._btn_stop = QPushButton("■  DỪNG LẠI")
        self._btn_stop.setFixedHeight(48)
        self._btn_stop.setEnabled(False)
        self._btn_stop.setStyleSheet(BTN_RED(15, 10))
        self._btn_stop.clicked.connect(self._stop)
        
        ctrl.addWidget(self._btn_start_post)
        ctrl.addWidget(self._btn_start_comment)
        ctrl.addWidget(self._btn_start_uptop)
        ctrl.addWidget(self._btn_stop)
        lay.addLayout(ctrl)

        prog = QHBoxLayout()
        self._st_lbl = QLabel("Sẵn sàng")
        self._st_lbl.setStyleSheet("color:#6c7086;font-size:12px;background:transparent;")
        self._pbar = QProgressBar()
        self._pbar.setValue(0)
        self._pbar.setFormat("%p%")
        self._pbar.setFixedHeight(18)
        prog.addWidget(self._st_lbl)
        prog.addWidget(self._pbar, 1)
        lay.addLayout(prog)
        return p

    def _make_settings_panel(self):
        gb = QGroupBox("⚙  Cấu hình đăng bài")
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(12, 8, 12, 10)
        lay.setSpacing(8)

        r1 = QHBoxLayout()
        self._chk_ai = QCheckBox("Dùng AI viết lại bài")
        self._chk_ai.setChecked(True)
        self._chk_ai.setEnabled(False)
        self._chk_ai.setVisible(False)
        ba = QPushButton("⚙ Cấu hình AI")
        ba.setFixedHeight(28)
        ba.setStyleSheet(BTN_BLUE(12, 6))
        ba.setEnabled(False)
        ba.setVisible(False)
        bc = QPushButton("📄 Chọn nội dung")
        bc.setFixedHeight(28)
        bc.setStyleSheet(BTN_GRAY)
        bc.setEnabled(False)
        bc.setVisible(False)
        r1.addWidget(self._chk_ai)
        r1.addStretch()
        r1.addWidget(ba)
        r1.addWidget(bc)
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        self._chk_rand = QCheckBox("Ngẫu nhiên số ảnh/video:")
        self._spin_med = QSpinBox()
        self._spin_med.setRange(1, 20)
        self._spin_med.setValue(1)
        self._spin_med.setFixedSize(58, 26)
        r2.addWidget(self._chk_rand)
        r2.addWidget(self._spin_med)
        r2.addStretch()
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        dl = QLabel("⏱  Thời gian chờ:")
        dl.setStyleSheet("background:transparent;color:#a6adc8;")
        self._sp_d1 = QSpinBox()
        self._sp_d1.setRange(5, 3600)
        self._sp_d1.setValue(60)
        self._sp_d1.setFixedSize(68, 26)
        sep = QLabel("~")
        sep.setStyleSheet("background:transparent;color:#6c7086;")
        self._sp_d2 = QSpinBox()
        self._sp_d2.setRange(5, 3600)
        self._sp_d2.setValue(120)
        self._sp_d2.setFixedSize(68, 26)
        un = QLabel("giây / nhóm")
        un.setStyleSheet("background:transparent;color:#6c7086;font-size:12px;")
        r3.addWidget(dl)
        r3.addWidget(self._sp_d1)
        r3.addWidget(sep)
        r3.addWidget(self._sp_d2)
        r3.addWidget(un)
        r3.addStretch()
        lay.addLayout(r3)
        return gb

    def _make_uptop_panel(self):
        gb = QGroupBox("🔝  Cấu hình Up Top")
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(12, 8, 12, 10)
        lay.setSpacing(6)

        guide = QLabel("📌  Dán link bài đã đăng (mỗi link 1 dòng).")
        guide.setStyleSheet(
            "color:#6c7086;font-size:11px;font-style:italic;background:transparent;")
        guide.setWordWrap(True)
        lay.addWidget(guide)

        lay.addWidget(self._lbl("Link bài cần up top:"))
        self._uptop_links = QTextEdit()
        self._uptop_links.setPlaceholderText("https://www.facebook.com/groups/.../posts/...")
        self._uptop_links.setFixedHeight(70)
        self._uptop_links.setStyleSheet(
            "QTextEdit{background:#181825;border:1px solid #45475a;border-radius:4px;"
            "font-size:12px;font-family:'Courier New';color:#cdd6f4;padding:5px;}"
            "QTextEdit:focus{border-color:#89b4fa;}")
        lay.addWidget(self._uptop_links)

        lay.addWidget(self._lbl("Nội dung comment up top (mỗi dòng 1 nội dung):"))
        self._uptop_cmts = QTextEdit()
        self._uptop_cmts.setPlaceholderText("chấm\ncheck inbox\nquan tâm\n...")
        self._uptop_cmts.setFixedHeight(60)
        self._uptop_cmts.setStyleSheet(self._uptop_links.styleSheet())
        lay.addWidget(self._uptop_cmts)

        r = QHBoxLayout()
        dl = QLabel("⏱  Thời gian chờ:")
        dl.setStyleSheet("background:transparent;color:#a6adc8;")
        self._sp_ut1 = QSpinBox()
        self._sp_ut1.setRange(5, 3600)
        self._sp_ut1.setValue(60)
        self._sp_ut1.setFixedSize(68, 26)
        sep = QLabel("~")
        sep.setStyleSheet("background:transparent;color:#6c7086;")
        self._sp_ut2 = QSpinBox()
        self._sp_ut2.setRange(5, 3600)
        self._sp_ut2.setValue(120)
        self._sp_ut2.setFixedSize(68, 26)
        un = QLabel("giây / link")
        un.setStyleSheet("background:transparent;color:#6c7086;font-size:12px;")
        r.addWidget(dl)
        r.addWidget(self._sp_ut1)
        r.addWidget(sep)
        r.addWidget(self._sp_ut2)
        r.addWidget(un)
        r.addStretch()
        lay.addLayout(r)
        return gb

    def _make_comment_panel(self):
        gb = QGroupBox("💬  Cấu hình Comment")
        lay = QVBoxLayout(gb)
        lay.setContentsMargins(12, 8, 12, 10)
        lay.setSpacing(6)

        r1 = QHBoxLayout()
        ql = QLabel("Số lượng bài viết:")
        ql.setStyleSheet("background:transparent;color:#a6adc8;")
        self._cmt_count = QSpinBox()
        self._cmt_count.setRange(1, 100)
        self._cmt_count.setValue(3)
        self._cmt_count.setFixedSize(70, 26)
        r1.addWidget(ql)
        r1.addWidget(self._cmt_count)
        r1.addStretch()
        lay.addLayout(r1)

        r2 = QHBoxLayout()
        self._cmt_chk_rand = QCheckBox("Ngẫu nhiên số ảnh/video:")
        self._cmt_spin_med = QSpinBox()
        self._cmt_spin_med.setRange(1, 20)
        self._cmt_spin_med.setValue(1)
        self._cmt_spin_med.setFixedSize(58, 26)
        r2.addWidget(self._cmt_chk_rand)
        r2.addWidget(self._cmt_spin_med)
        r2.addStretch()
        lay.addLayout(r2)

        r3 = QHBoxLayout()
        dl = QLabel("⏱  Thời gian chờ:")
        dl.setStyleSheet("background:transparent;color:#a6adc8;")
        self._cmt_sp_d1 = QSpinBox()
        self._cmt_sp_d1.setRange(5, 3600)
        self._cmt_sp_d1.setValue(60)
        self._cmt_sp_d1.setFixedSize(68, 26)
        sep = QLabel("~")
        sep.setStyleSheet("background:transparent;color:#6c7086;")
        self._cmt_sp_d2 = QSpinBox()
        self._cmt_sp_d2.setRange(5, 3600)
        self._cmt_sp_d2.setValue(120)
        self._cmt_sp_d2.setFixedSize(68, 26)
        un = QLabel("giây / nhóm")
        un.setStyleSheet("background:transparent;color:#6c7086;font-size:12px;")
        r3.addWidget(dl)
        r3.addWidget(self._cmt_sp_d1)
        r3.addWidget(sep)
        r3.addWidget(self._cmt_sp_d2)
        r3.addWidget(un)
        r3.addStretch()
        lay.addLayout(r3)
        return gb

    def _make_group_right(self):
        p = QWidget()
        p.setStyleSheet("background:#181825;border-left:1px solid #313244;")
        p.setFixedWidth(358)
        lay = QVBoxLayout(p)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        h1 = QLabel("✔  KẾT QUẢ THÀNH CÔNG")
        h1.setFixedHeight(30)
        h1.setStyleSheet("background:#1c2e1c;color:#a6e3a1;font-weight:bold;font-size:12px;"
                         "padding:0 10px;border-bottom:1px solid #2e4a2e;")
        lay.addWidget(h1)
        self._suc = self._make_result_table(
            ["Time", "Nhóm", "Link Bài Viết"], [68, 80], "#1c2e1c", "#a6e3a1")
        self._suc.setContextMenuPolicy(Qt.CustomContextMenu)
        self._suc.customContextMenuRequested.connect(
            lambda p: self._res_menu(p, self._suc))
        lay.addWidget(self._suc, 2)

        h2 = QLabel("✖  KẾT QUẢ LỖI")
        h2.setFixedHeight(30)
        h2.setStyleSheet("background:#2e1c1c;color:#f38ba8;font-weight:bold;font-size:12px;"
                         "padding:0 10px;border-top:1px solid #4a2e2e;border-bottom:1px solid #4a2e2e;")
        lay.addWidget(h2)
        self._err = self._make_result_table(
            ["Time", "Nhóm", "Lỗi"], [68, 80], "#2e1c1c", "#f38ba8")
        lay.addWidget(self._err, 1)

        lh = QWidget()
        lh.setFixedHeight(30)
        lh.setStyleSheet("background:#1a1a2e;border-top:1px solid #313264;"
                         "border-bottom:1px solid #313264;")
        lhl = QHBoxLayout(lh)
        lhl.setContentsMargins(10, 0, 10, 0)
        ll = QLabel("📋  NHẬT KÝ GROUP")
        ll.setStyleSheet("color:#89b4fa;font-weight:bold;font-size:12px;background:transparent;")
        bc = QPushButton("Xóa")
        bc.setFixedHeight(22)
        bc.setStyleSheet("QPushButton{background:#313244;color:#a6adc8;border:1px solid #45475a;"
                         "border-radius:3px;font-size:11px;padding:0 8px;}"
                         "QPushButton:hover{background:#45475a;}")
        lhl.addWidget(ll)
        lhl.addStretch()
        lhl.addWidget(bc)
        lay.addWidget(lh)

        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setStyleSheet(
            "QTextEdit{font-size:11px;background:#11111b;border:none;"
            "font-family:'Consolas','Courier New';color:#a6adc8;padding:4px;}")
        bc.clicked.connect(self._log.clear)
        lay.addWidget(self._log, 2)
        return p

    def _make_result_table(self, headers, col_widths, bg, hdr_color):
        t = QTableWidget()
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setStretchLastSection(True)
        for i, w in enumerate(col_widths):
            t.setColumnWidth(i, w)
        t.verticalHeader().setVisible(False)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.setShowGrid(False)
        t.setStyleSheet(
            f"QTableWidget{{font-size:11px;background:{bg};border:none;color:#cdd6f4;}}"
            f"QTableWidget::item{{padding:4px 6px;border:none;}}"
            f"QHeaderView::section{{background:#313244;font-size:11px;color:{hdr_color};"
            f"border:none;border-bottom:1px solid #45475a;padding:4px 6px;}}")
        return t

    def _sub_switch(self, tab):
        self._current_tab = tab  # Save current tab
        ACT = ("QPushButton{background:#89b4fa;color:#1e1e2e;border:none;"
               "border-radius:4px;font-size:12px;font-weight:bold;padding:4px 16px;}")
        OFF = ("QPushButton{background:#313244;color:#a6adc8;border:1px solid #45475a;"
               "border-radius:4px;font-size:12px;padding:4px 16px;}"
               "QPushButton:hover{background:#45475a;}")
        for k, b in self._sb_btns.items():
            b.setStyleSheet(ACT if k == tab else OFF)
        if hasattr(self, "_pnl_main"):
            self._pnl_main.setVisible(tab == "post")
            self._pnl_comment.setVisible(tab == "comment")
            self._pnl_uptop.setVisible(tab == "uptop")
            # Đổi tên nội dung bài viết
            if tab == "post":
                self._gb_nd.setTitle("📝  Nội dung bài viết")
            elif tab == "comment":
                self._gb_nd.setTitle("📝  Nội dung comment")
        
        # Hiển thị nút BẮT ĐẦU tương ứng
        if hasattr(self, "_btn_start_post"):
            self._btn_start_post.setVisible(tab == "post")
            self._btn_start_comment.setVisible(tab == "comment")
            self._btn_start_uptop.setVisible(tab == "uptop")

    def _res_menu(self, pos, tbl):
        m = QMenu(self)
        a = QAction("📋  Copy link bài viết", self)
        a.triggered.connect(lambda: self._copy_links(tbl))
        m.addAction(a)
        m.exec_(tbl.viewport().mapToGlobal(pos))

    def _copy_links(self, tbl):
        links = [tbl.item(r, 2).text() for r in range(tbl.rowCount()) if tbl.item(r, 2)]
        if links:
            QApplication.clipboard().setText("\n".join(links))

    def _add_media(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh/Video", "",
            "Media (*.jpg *.jpeg *.png *.gif *.bmp *.mp4 *.avi *.mov);;All Files (*)")
        for f in files:
            self._media.addItem(f)

    def _rm_media(self):
        for item in self._media.selectedItems():
            self._media.takeItem(self._media.row(item))

    def _start_action(self, action_type):
        """Bắt đầu thực thi dựa trên loại action (post/comment/uptop)"""
        if self._driver is None:
            self._log_msg('<span style="color:#f38ba8;font-size:11px;">'
                          '[ERROR] Chrome chưa mở hoặc chưa sẵn sàng.</span>')
            return

        # ── Lọc các groups được checkbox ─────────────────────────
        selected_groups = []
        for i in range(self._gt.rowCount()):
            chk = self._gt.cellWidget(i, 0)
            if isinstance(chk, QCheckBox) and chk.isChecked():
                url_item  = self._gt.item(i, 2)
                name_item = self._gt.item(i, 3)
                gurl = url_item.text()  if url_item  else ''
                gnm  = name_item.text() if name_item else ''
                if gurl:
                    selected_groups.append({'url': gurl, 'name': gnm})

        if not selected_groups:
            self._log_msg('<span style="color:#f38ba8;font-size:11px;">'
                          '[WARN] Chưa chọn nhóm nào (hãy tick checkbox ✓).</span>')
            return

        # ── Nội dung ──────────────────────────────────────────────
        content = self._content.toPlainText().strip()
        if not content:
            self._log_msg('<span style="color:#f38ba8;font-size:11px;">'
                          '[WARN] Chưa nhập nội dung.</span>')
            return

        # ── Danh sách ảnh / video ─────────────────────────────────
        media_list = []
        for i in range(self._media.count()):
            item = self._media.item(i)
            if item:
                file_path = item.text()
                file_name = os.path.basename(file_path)
                media_list.append({
                    'path': file_path,
                    'name': file_name
                })

        # ── Xử lý theo loại action ────────────────────────────────
        if action_type == "comment":
            use_random_media  = self._cmt_chk_rand.isChecked()
            random_media_count = self._cmt_spin_med.value() if use_random_media else 1
            delay_min = self._cmt_sp_d1.value()
            delay_max = self._cmt_sp_d2.value()
            cmt_count = self._cmt_count.value()

            data = {
                'profile':      self.profile_name,
                'groups':       selected_groups,
                'content':      content,
                'media':        media_list,
                'random_media': use_random_media,
                'media_count':  random_media_count,
                'cmt_count':    cmt_count,
                'delay_min':    delay_min,
                'delay_max':    delay_max,
            }

            ts = datetime.now().strftime("%H:%M:%S")
            self._log_msg(
                f'<span style="color:#89b4fa;font-size:11px;">'
                f'[{ts}] 💬 Bắt đầu comment {cmt_count} bài/nhóm | '
                f'{len(selected_groups)} nhóm | '
                f'Delay: {delay_min}~{delay_max}s</span>')

            # ── Khởi động worker ──────────────────────────────────────
            self._running      = True
            self._progress_val = 0
            self._total_groups = len(selected_groups)
            self._done_groups  = 0
            self._set_btn_enabled(False)
            self._st_lbl.setText(f"⏳  Đang chạy... 0/{self._total_groups}")
            self._pbar.setValue(0)
            self._pbar.setFormat(f"0 / {self._total_groups}")

            self._cmt_worker = CommentGroupsWorker(self._driver, data)
            self._cmt_worker.log_signal.connect(self._on_cmt_log)
            self._cmt_worker.success_signal.connect(self._on_cmt_success)
            self._cmt_worker.fail_signal.connect(self._on_cmt_fail)
            self._cmt_worker.finished.connect(self._on_cmt_finished)
            self._cmt_worker.start()

        elif action_type == "post":
            use_random_media  = self._chk_rand.isChecked()
            random_media_count = self._spin_med.value() if use_random_media else 1
            delay_min = self._sp_d1.value()
            delay_max = self._sp_d2.value()

            data = {
                'profile':      self.profile_name,
                'groups':       selected_groups,
                'content':      content,
                'media':        media_list,
                'random_media': use_random_media,
                'media_count':  random_media_count,
                'delay_min':    delay_min,
                'delay_max':    delay_max,
            }

            ts = datetime.now().strftime("%H:%M:%S")
            self._log_msg(
                f'<span style="color:#89b4fa;font-size:11px;">'
                f'[{ts}] 🚀 Bắt đầu đăng {len(selected_groups)} nhóm | '
                f'Delay: {delay_min}~{delay_max}s | '
                f'Media: {"random " + str(random_media_count) if use_random_media else "tuần tự"}</span>')

            print(f"[INFO] Start posting: {json.dumps(data, ensure_ascii=False)}", flush=True)

            # ── Khởi động worker ──────────────────────────────────────
            self._running      = True
            self._progress_val = 0
            self._total_groups = len(selected_groups)
            self._done_groups  = 0
            self._set_btn_enabled(False)
            self._st_lbl.setText(f"⏳  Đang chạy... 0/{self._total_groups}")
            self._pbar.setValue(0)
            self._pbar.setFormat(f"0 / {self._total_groups}")

            self._post_worker = PostGroupsWorker(self._driver, data)
            self._post_worker.log_signal.connect(self._on_post_log)
            self._post_worker.success_signal.connect(self._on_post_success)
            self._post_worker.fail_signal.connect(self._on_post_fail)
            self._post_worker.finished.connect(self._on_post_finished)
            self._post_worker.start()

        elif action_type == "uptop":
            self._log_msg('<span style="color:#fab387;font-size:11px;">'
                          '[INFO] UP TOP chưa được code...</span>')

    def _set_btn_enabled(self, enabled):
        """Enable/disable nút start tương ứng với tab hiện tại"""
        if hasattr(self, "_btn_start_post"):
            if self._current_tab == "post":
                self._btn_start_post.setEnabled(enabled)
            elif self._current_tab == "comment":
                self._btn_start_comment.setEnabled(enabled)
            elif self._current_tab == "uptop":
                self._btn_start_uptop.setEnabled(enabled)
        self._btn_stop.setEnabled(not enabled)

    def _on_post_success(self, ts: str, group_name: str, post_url: str):
        r = self._suc.rowCount()
        self._suc.insertRow(r)
        for j, v in enumerate([ts, group_name, post_url]):
            self._suc.setItem(r, j, QTableWidgetItem(v))
        self._suc.scrollToBottom()
        self._done_groups += 1
        self._update_progress()

    def _on_post_fail(self, ts: str, group_name: str, error: str):
        r = self._err.rowCount()
        self._err.insertRow(r)
        for j, v in enumerate([ts, group_name, error]):
            self._err.setItem(r, j, QTableWidgetItem(v))
        self._err.scrollToBottom()
        self._done_groups += 1
        self._update_progress()

    def _update_progress(self):
        """Cập nhật progress bar theo số nhóm đã xử lý."""
        if not hasattr(self, '_total_groups') or self._total_groups == 0:
            return
        pct = int(self._done_groups / self._total_groups * 100)
        self._pbar.setValue(pct)
        self._pbar.setFormat(f"{self._done_groups} / {self._total_groups}")
        self._st_lbl.setText(f"⏳  Đang chạy... {self._done_groups}/{self._total_groups}")

    def _on_post_finished(self):
        self._running = False
        self._timer.stop()
        self._pbar.setValue(100)
        if hasattr(self, '_total_groups'):
            self._pbar.setFormat(f"{self._total_groups} / {self._total_groups}")
        self._set_btn_enabled(True)
        ts = datetime.now().strftime("%H:%M:%S")
        suc = self._suc.rowCount()
        err = self._err.rowCount()
        self._st_lbl.setText(f"✔ Hoàn thành  ✅{suc}  ❌{err}")
        self._log_msg(
            f'<span style="color:#a6e3a1;font-size:11px;">'
            f'[{ts}] ✅ HOÀN THÀNH — Thành công: {suc} | Lỗi: {err}</span>')
        if hasattr(self, '_post_worker') and self._post_worker is not None:
            self._post_worker.deleteLater()
            self._post_worker = None

    def _stop(self):
        self._running = False
        self._timer.stop()
        self._set_btn_enabled(True)
        self._st_lbl.setText("⏹  Đã dừng")

    def _tick(self):
        """Tick timer — không còn dùng để fake progress, chỉ giữ lại phòng trường hợp cần."""
        pass

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: ĐĂNG PAGE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_page(self):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._make_page_left())
        lay.addWidget(self._make_page_center(), 1)
        lay.addWidget(self._make_page_right())
        return w

    def _make_page_left(self):
        p = QWidget()
        p.setStyleSheet("background:#181825;border-right:1px solid #313244;")
        p.setFixedWidth(316)
        lay = QVBoxLayout(p)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        fi = QLineEdit()
        fi.setPlaceholderText("🔍  Tìm page...")
        fi.setFixedHeight(28)
        fi.setStyleSheet(
            "QLineEdit{background:#313244;border:1px solid #45475a;"
            "border-radius:4px;padding:2px 10px;font-size:12px;color:#cdd6f4;}"
            "QLineEdit:focus{border-color:#89b4fa;}")
        lay.addWidget(fi)

        self._pt = QTableWidget()
        self._pt.setColumnCount(3)
        self._pt.setHorizontalHeaderLabels(["#", "ID Page", "Tên Page"])
        self._pt.horizontalHeader().setStretchLastSection(True)
        self._pt.setColumnWidth(0, 32)
        self._pt.setColumnWidth(1, 95)
        self._pt.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._pt.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._pt.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._pt.setAlternatingRowColors(True)
        self._pt.verticalHeader().setVisible(False)
        self._pt.setShowGrid(False)
        self._pt.setContextMenuPolicy(Qt.CustomContextMenu)
        self._pt.customContextMenuRequested.connect(
            lambda pos: self._simple_menu(pos, self._pt))
        self._pt.setStyleSheet(self._gt.styleSheet())
        lay.addWidget(self._pt, 1)

        br = QHBoxLayout()
        br.setSpacing(6)
        b1 = QPushButton("⬇  LẤY DS PAGE")
        b1.setFixedHeight(34)
        b1.setStyleSheet(BTN_GREEN(12, 6))
        b1.clicked.connect(self._load_pages)
        b2 = QPushButton("📂  LOAD DATA")
        b2.setFixedHeight(34)
        b2.setStyleSheet(BTN_GRAY)
        br.addWidget(b1)
        br.addWidget(b2)
        lay.addLayout(br)
        return p

    def _load_pages(self):
        pages = [
            ("101834829", "Tiến Khoa Official"),
            ("209384756", "BĐS Sài Gòn 24h"),
            ("345678901", "Nhà Đất TP.HCM"),
            ("456789012", "Bất Động Sản Việt"),
            ("567890123", "Mua Bán Nhà Đất"),
        ]
        self._pt.setRowCount(len(pages))
        for i, (pid, pnm) in enumerate(pages):
            si = QTableWidgetItem(str(i + 1))
            si.setTextAlignment(Qt.AlignCenter)
            self._pt.setItem(i, 0, si)
            self._pt.setItem(i, 1, QTableWidgetItem(pid))
            self._pt.setItem(i, 2, QTableWidgetItem(pnm))
            self._pt.setRowHeight(i, 28)

    def _simple_menu(self, pos, tbl):
        m = QMenu(self)
        for txt, fn in [("Chọn tất cả", tbl.selectAll),
                        ("Bỏ chọn tất cả", tbl.clearSelection)]:
            a = QAction(txt, self)
            a.triggered.connect(fn)
            m.addAction(a)
        m.exec_(tbl.viewport().mapToGlobal(pos))

    def _make_page_center(self):
        p = QWidget()
        lay = QVBoxLayout(p)
        lay.setContentsMargins(10, 10, 10, 8)
        lay.setSpacing(8)

        gb_nd = QGroupBox("📝  Nội dung bài viết")
        gbl = QVBoxLayout(gb_nd)
        gbl.setContentsMargins(10, 8, 10, 10)
        self._page_content = QTextEdit()
        self._page_content.setPlaceholderText(
            "Nhập nội dung... Hỗ trợ Spin {nội dung 1|nội dung 2}")
        self._page_content.setMinimumHeight(140)
        self._page_content.setStyleSheet(
            "QTextEdit{background:#181825;border:1px solid #45475a;border-radius:6px;"
            "font-size:13px;color:#cdd6f4;padding:8px;}"
            "QTextEdit:focus{border-color:#89b4fa;}")
        gbl.addWidget(self._page_content)
        lay.addWidget(gb_nd)

        gb_av = QGroupBox("🖼  Danh sách ảnh / Video")
        gb_av.setFixedHeight(112)
        avl = QHBoxLayout(gb_av)
        avl.setContentsMargins(10, 6, 10, 10)
        self._page_media = QListWidget()
        avr = QVBoxLayout()
        avr.setSpacing(4)
        for txt in ["+ Thêm", "✕ Xóa", "⊘ Clear"]:
            b = QPushButton(txt)
            b.setFixedSize(90, 26)
            b.setStyleSheet(BTN_GRAY)
            avr.addWidget(b)
        avr.addStretch()
        avl.addWidget(self._page_media, 1)
        avl.addLayout(avr)
        lay.addWidget(gb_av)

        gb_cfg = QGroupBox("⚙  Cấu hình đăng page")
        psl = QVBoxLayout(gb_cfg)
        psl.setContentsMargins(12, 8, 12, 10)
        psl.setSpacing(8)

        r1 = QHBoxLayout()
        chk = QCheckBox("Dùng AI viết lại bài")
        chk.setChecked(True)
        ba = QPushButton("⚙ Cấu hình AI")
        ba.setFixedHeight(28)
        ba.setStyleSheet(BTN_BLUE(12, 6))
        bc2 = QPushButton("📄 Chọn nội dung")
        bc2.setFixedHeight(28)
        bc2.setStyleSheet(BTN_GRAY)
        r1.addWidget(chk)
        r1.addStretch()
        r1.addWidget(ba)
        r1.addWidget(bc2)
        psl.addLayout(r1)

        r2 = QHBoxLayout()
        chk2 = QCheckBox("Ngẫu nhiên số ảnh/video:")
        sp2 = QSpinBox()
        sp2.setRange(1, 20)
        sp2.setValue(1)
        sp2.setFixedSize(58, 26)
        r2.addWidget(chk2)
        r2.addWidget(sp2)
        r2.addStretch()
        psl.addLayout(r2)

        r3 = QHBoxLayout()
        dl = QLabel("⏱  Thời gian chờ:")
        dl.setStyleSheet("background:transparent;color:#a6adc8;")
        sp3a = QSpinBox()
        sp3a.setRange(5, 3600)
        sp3a.setValue(60)
        sp3a.setFixedSize(68, 26)
        ss = QLabel("~")
        ss.setStyleSheet("background:transparent;color:#6c7086;")
        sp3b = QSpinBox()
        sp3b.setRange(5, 3600)
        sp3b.setValue(120)
        sp3b.setFixedSize(68, 26)
        un = QLabel("giây / page")
        un.setStyleSheet("background:transparent;color:#6c7086;font-size:12px;")
        r3.addWidget(dl)
        r3.addWidget(sp3a)
        r3.addWidget(ss)
        r3.addWidget(sp3b)
        r3.addWidget(un)
        r3.addStretch()
        psl.addLayout(r3)
        lay.addWidget(gb_cfg)
        lay.addStretch()

        cr = QHBoxLayout()
        cr.setSpacing(8)
        self._pg_start = QPushButton("▶  BẮT ĐẦU")
        self._pg_start.setFixedHeight(48)
        self._pg_start.setStyleSheet(BTN_GREEN(15, 10))
        self._pg_stop = QPushButton("■  DỪNG LẠI")
        self._pg_stop.setFixedHeight(48)
        self._pg_stop.setEnabled(False)
        self._pg_stop.setStyleSheet(BTN_RED(15, 10))
        cr.addWidget(self._pg_start)
        cr.addWidget(self._pg_stop)
        lay.addLayout(cr)

        pr = QHBoxLayout()
        self._pg_st_lbl = QLabel("Sẵn sàng")
        self._pg_st_lbl.setStyleSheet("color:#6c7086;font-size:12px;background:transparent;")
        self._pg_pbar = QProgressBar()
        self._pg_pbar.setValue(0)
        self._pg_pbar.setFormat("%p%")
        self._pg_pbar.setFixedHeight(18)
        pr.addWidget(self._pg_st_lbl)
        pr.addWidget(self._pg_pbar, 1)
        lay.addLayout(pr)
        return p

    def _make_page_right(self):
        p = QWidget()
        p.setStyleSheet("background:#181825;border-left:1px solid #313244;")
        p.setFixedWidth(358)
        lay = QVBoxLayout(p)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        h1 = QLabel("✔  KẾT QUẢ THÀNH CÔNG")
        h1.setFixedHeight(30)
        h1.setStyleSheet("background:#1c2e1c;color:#a6e3a1;font-weight:bold;font-size:12px;"
                         "padding:0 10px;border-bottom:1px solid #2e4a2e;")
        lay.addWidget(h1)
        self._pg_suc = self._make_result_table(
            ["Time", "Page", "Link"], [68, 80], "#1c2e1c", "#a6e3a1")
        lay.addWidget(self._pg_suc, 2)

        h2 = QLabel("✖  KẾT QUẢ LỖI")
        h2.setFixedHeight(30)
        h2.setStyleSheet("background:#2e1c1c;color:#f38ba8;font-weight:bold;font-size:12px;"
                         "padding:0 10px;border-top:1px solid #4a2e2e;border-bottom:1px solid #4a2e2e;")
        lay.addWidget(h2)
        self._pg_err = self._make_result_table(
            ["Time", "Page", "Lỗi"], [68, 80], "#2e1c1c", "#f38ba8")
        lay.addWidget(self._pg_err, 1)

        lh = QWidget()
        lh.setFixedHeight(30)
        lh.setStyleSheet("background:#1a1a2e;border-top:1px solid #313264;"
                         "border-bottom:1px solid #313264;")
        lhl = QHBoxLayout(lh)
        lhl.setContentsMargins(10, 0, 10, 0)
        ll = QLabel("📋  NHẬT KÝ PAGE")
        ll.setStyleSheet("color:#89b4fa;font-weight:bold;font-size:12px;background:transparent;")
        bc = QPushButton("Xóa")
        bc.setFixedHeight(22)
        bc.setStyleSheet("QPushButton{background:#313244;color:#a6adc8;border:1px solid #45475a;"
                         "border-radius:3px;font-size:11px;padding:0 8px;}"
                         "QPushButton:hover{background:#45475a;}")
        lhl.addWidget(ll)
        lhl.addStretch()
        lhl.addWidget(bc)
        lay.addWidget(lh)

        self._pg_log = QTextEdit()
        self._pg_log.setReadOnly(True)
        self._pg_log.setStyleSheet(
            "QTextEdit{font-size:11px;background:#11111b;border:none;"
            "font-family:'Consolas','Courier New';color:#a6adc8;padding:4px;}")
        bc.clicked.connect(self._pg_log.clear)
        lay.addWidget(self._pg_log, 2)
        return p

    @staticmethod
    def _lbl(txt):
        l = QLabel(txt)
        l.setStyleSheet(
            "background:transparent;font-weight:bold;font-size:12px;color:#a6adc8;")
        return l

    # ══════════════════════════════════════════════════════════════════════════
    # TAB: CÁCH CANH
    # ══════════════════════════════════════════════════════════════════════════
    def _build_settings(self):
        w = QWidget()
        w.setStyleSheet("background:#1e1e2e;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        title = QLabel("🔧  QUẢN LÝ PROFILE")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color:#89b4fa;background:transparent;")
        lay.addWidget(title)

        info = QLabel(f"Profile hiện tại: {self.profile_name}")
        info.setStyleSheet("color:#a6adc8;background:transparent;font-size:12px;")
        lay.addWidget(info)
        lay.addStretch()
        return w


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tiến Khoa  ·  Marketing Tự động")
        self.resize(1120, 700)
        self.setMinimumSize(820, 520)
        self.setStyleSheet(DARK)
        self._windows: dict[str, FacebookWindow] = {}
        self._machine_id = self._mk_id()
        self._activated  = False
        self._build()

    def _mk_id(self):
        import hashlib, uuid
        h = hashlib.md5(str(uuid.getnode()).encode()).hexdigest().upper()
        return f"{h[:4]}-{h[4:8]}-{h[8:12]}-{h[12:16]}"

    def _build(self):
        mb = self.menuBar()
        mb.setStyleSheet(
            "QMenuBar{background:#11111b;color:#cdd6f4;font-size:15px;"
            "font-weight:bold;min-height:44px;padding:0 14px;border-bottom:1px solid #313244;}"
            "QMenuBar::item{background:transparent;color:#cdd6f4;padding:10px 0;}"
            "QMenuBar::item:disabled{color:#89b4fa;}")
        act = QAction("◈  Tiến Khoa", self)
        act.setEnabled(False)
        mb.addAction(act)

        corner = QWidget()
        corner.setStyleSheet("background:#11111b;")
        cl = QHBoxLayout(corner)
        cl.setContentsMargins(0, 0, 12, 0)
        cl.setSpacing(2)
        for txt, slot in [("📖 Hướng dẫn", self._help),
                           ("🔑 License",   self._license),
                           ("🔄 Update",    self._update)]:
            b = QPushButton(txt)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:#a6adc8;border:none;"
                "padding:8px 12px;font-size:12px;border-radius:4px;}"
                "QPushButton:hover{background:#313244;color:#cdd6f4;}")
            b.clicked.connect(slot)
            cl.addWidget(b)
        mb.setCornerWidget(corner, Qt.TopRightCorner)

        cw = QWidget()
        self.setCentralWidget(cw)
        root = QHBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._make_left())
        root.addWidget(self._make_right(), 1)

        sb = QStatusBar()
        sb.setStyleSheet("QStatusBar{background:#11111b;border-top:1px solid #313244;"
                         "font-size:12px;color:#6c7086;}"
                         "QStatusBar QLabel{background:transparent;}")
        self.setStatusBar(sb)
        self._sr = QLabel(
            "Hạn sử dụng: Chưa kích hoạt   ·   Version 13.3.26   ·   Zalo 0961.006.186")
        self._sr.setStyleSheet(
            "color:#6c7086;font-size:12px;padding-right:12px;background:transparent;")
        sb.addPermanentWidget(self._sr)
        sb.showMessage(
            "  Sẵn sàng   ·   Gói 6 tháng: 600.000đ   ·   12 tháng: 1.000.000đ   ·   Vĩnh Viễn: 3.000.000đ")

    def _make_left(self):
        p = QWidget()
        p.setStyleSheet("background:#181825;border-right:1px solid #313244;")
        p.setFixedWidth(292)
        lay = QVBoxLayout(p)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(12)

        ab = QGroupBox("➕  Thêm Profile Mới")
        al = QVBoxLayout(ab)
        al.setContentsMargins(12, 10, 12, 12)
        al.setSpacing(8)
        lbl = QLabel("Tên Profile:")
        lbl.setStyleSheet("background:transparent;color:#a6adc8;font-size:12px;")
        self._name_in = QLineEdit()
        self._name_in.setPlaceholderText("VD: FB Sales 01")
        self._name_in.setFixedHeight(30)
        self._name_in.returnPressed.connect(self._create)
        btn_cr = QPushButton("✚  TẠO PROFILE")
        btn_cr.setFixedHeight(36)
        btn_cr.setStyleSheet(BTN_GREEN(13, 7))
        btn_cr.clicked.connect(self._create)
        brow = QHBoxLayout()
        brow.setSpacing(6)
        for txt, fn in [("🗑 Xóa", self._delete),
                        ("↺ Làm mới", self._load_profiles),
                        ("✕ Đóng", self.close)]:
            b = QPushButton(txt)
            b.setFixedHeight(28)
            b.setStyleSheet(BTN_GRAY)
            b.clicked.connect(fn)
            brow.addWidget(b)
        al.addWidget(lbl)
        al.addWidget(self._name_in)
        al.addWidget(btn_cr)
        al.addLayout(brow)
        lay.addWidget(ab)

        cb = QGroupBox("🎛  Bảng Điều Khiển")
        cl2 = QVBoxLayout(cb)
        cl2.setContentsMargins(12, 10, 12, 12)
        cl2.setSpacing(10)
        self._chk_mute = QCheckBox("Tắt âm thanh trình duyệt")
        self._chk_mute.setChecked(True)

        self._btn_fb = QPushButton("🌐  MỞ TÍNH NĂNG FACEBOOK")
        self._btn_fb.setFixedHeight(46)
        self._btn_fb.setStyleSheet(BTN_BLUE(13, 10))
        self._btn_fb.clicked.connect(self._open_fb)

        note = QLabel(
            "✦ Chọn 1 tài khoản → bấm nút\n  (Double-click tên cũng mở được)\n"
            "✦ Chrome tự khởi động khi mở cửa sổ")
        note.setStyleSheet(
            "color:#6c7086;font-size:11px;font-style:italic;background:transparent;")
        note.setWordWrap(True)

        self._btn_zalo = QPushButton("💬  MỞ TÍNH NĂNG ZALO")
        self._btn_zalo.setFixedHeight(46)
        self._btn_zalo.setStyleSheet(BTN_GREEN(13, 10))
        self._btn_zalo.clicked.connect(self._open_zalo)

        cl2.addWidget(self._chk_mute)
        cl2.addWidget(self._btn_fb)
        cl2.addWidget(note)
        cl2.addWidget(self._btn_zalo)
        lay.addWidget(cb)

        sb2 = QGroupBox("⊞  Sắp xếp cửa sổ")
        sl = QVBoxLayout(sb2)
        sl.setContentsMargins(12, 10, 12, 12)
        sl.setSpacing(8)
        row1 = QHBoxLayout()
        lbl2 = QLabel("Số cột:")
        lbl2.setStyleSheet("background:transparent;color:#a6adc8;font-size:12px;")
        self._spin_cols = QSpinBox()
        self._spin_cols.setRange(1, 6)
        self._spin_cols.setValue(2)
        self._spin_cols.setFixedSize(54, 28)
        row1.addWidget(lbl2)
        row1.addWidget(self._spin_cols)
        row1.addStretch()
        sl.addLayout(row1)
        btn_tile = QPushButton("⊞  SẮP XẾP CỬA SỔ")
        btn_tile.setFixedHeight(34)
        btn_tile.setStyleSheet(BTN_GRAY)
        btn_tile.clicked.connect(self._tile_windows)
        sl.addWidget(btn_tile)
        lay.addWidget(sb2)
        lay.addStretch()
        return p

    def _make_right(self):
        p = QWidget()
        p.setStyleSheet("background:#1e1e2e;")
        lay = QVBoxLayout(p)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        tl = QLabel("Danh sách tài khoản (Profiles)")
        tl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        tl.setStyleSheet("color:#cdd6f4;background:transparent;")
        lay.addWidget(tl)

        self._tbl = QTableWidget()
        self._tbl.setColumnCount(8)
        self._tbl.setHorizontalHeaderLabels(
            ["#", "Profile", "Trạng thái", "UID", "Pass", "2FA", "Email", "PassMail"])
        self._tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        for col, w in [(0, 40), (3, 92), (4, 80), (5, 60), (6, 90), (7, 82)]:
            self._tbl.setColumnWidth(col, w)
        self._tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._tbl.setSelectionMode(QAbstractItemView.SingleSelection)
        self._tbl.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setShowGrid(False)
        self._tbl.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tbl.customContextMenuRequested.connect(self._tbl_menu)
        self._tbl.doubleClicked.connect(self._open_fb)
        self._tbl.setStyleSheet(
            "QTableWidget{border:1px solid #45475a;border-radius:6px;background:#181825;"
            "alternate-background-color:#1e1e2e;}"
            "QTableWidget::item{padding:5px 6px;border:none;}"
            "QTableWidget::item:selected{background:#45475a;color:#89b4fa;}"
            "QHeaderView::section{background:#313244;color:#89b4fa;font-weight:bold;"
            "border:none;border-bottom:1px solid #45475a;padding:6px 8px;font-size:12px;}")
        lay.addWidget(self._tbl)
        self._load_profiles()
        return p

    def _tbl_menu(self, pos):
        m = QMenu(self)
        for txt, fn in [("🌐 Mở tính năng Facebook", self._open_fb),
                        ("💬 Mở tính năng Zalo",     self._open_zalo),
                        ("🗑 Xóa Profile",            self._delete)]:
            a = QAction(txt, self)
            a.triggered.connect(fn)
            m.addAction(a)
        m.exec_(self._tbl.viewport().mapToGlobal(pos))

    def _create(self):
        name = self._name_in.text().strip()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên Profile!")
            return
        for r in range(self._tbl.rowCount()):
            it = self._tbl.item(r, 1)
            if it and it.text() == name:
                QMessageBox.warning(self, "Lỗi", f"Profile '{name}' đã tồn tại!")
                return
        r = self._tbl.rowCount()
        self._tbl.insertRow(r)
        for j, v in enumerate([str(r + 1), name, "disconnect", "", "", "", "", ""]):
            it = QTableWidgetItem(v)
            if j == 0:
                it.setTextAlignment(Qt.AlignCenter)
            self._tbl.setItem(r, j, it)
        self._tbl.setRowHeight(r, 32)
        self._name_in.clear()
        self._tbl.selectRow(r)
        self._save_profiles()

    def _delete(self):
        r = self._tbl.currentRow()
        if r < 0:
            QMessageBox.information(self, "", "Vui lòng chọn Profile cần xóa!")
            return
        nm = self._tbl.item(r, 1).text() if self._tbl.item(r, 1) else ""
        if QMessageBox.question(self, "Xác nhận", f"Xóa Profile '{nm}'?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._tbl.removeRow(r)
            self._save_profiles()

    def _profile_file(self) -> str:
        base = os.path.dirname(os.path.abspath(__file__))
        data = os.path.join(base, "data")
        os.makedirs(data, exist_ok=True)
        return os.path.join(data, "profile.json")

    def _load_profiles(self):
        path = self._profile_file()
        if not os.path.isfile(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                profiles = json.load(f)
            self._tbl.setRowCount(0)
            for profile in profiles:
                r = self._tbl.rowCount()
                self._tbl.insertRow(r)
                if isinstance(profile, dict):
                    row_data = [
                        profile.get("id", ""),
                        profile.get("profile", ""),
                        profile.get("status", ""),
                        profile.get("uid", ""),
                        profile.get("pass", ""),
                        profile.get("2fa", ""),
                        profile.get("email", ""),
                        profile.get("passmail", ""),
                    ]
                else:
                    row_data = profile
                for j, v in enumerate(row_data):
                    it = QTableWidgetItem(str(v))
                    if j == 0:
                        it.setTextAlignment(Qt.AlignCenter)
                    self._tbl.setItem(r, j, it)
                self._tbl.setRowHeight(r, 32)
        except Exception as e:
            print(f"[Profile] Load lỗi: {e}")

    def _save_profiles(self):
        path = self._profile_file()
        try:
            profiles = []
            for r in range(self._tbl.rowCount()):
                def cell(col, _r=r):
                    it = self._tbl.item(_r, col)
                    return it.text() if it else ""
                profiles.append({
                    "id":       cell(0),
                    "profile":  cell(1),
                    "status":   cell(2),
                    "uid":      cell(3),
                    "pass":     cell(4),
                    "2fa":      cell(5),
                    "email":    cell(6),
                    "passmail": cell(7),
                })
            with open(path, "w", encoding="utf-8") as f:
                json.dump(profiles, f, ensure_ascii=False, indent=2)
            print(f"[Profile] Đã lưu {len(profiles)} profiles", flush=True)
        except Exception as e:
            print(f"[Profile] Save lỗi: {e}")

    def _open_fb(self):
        r = self._tbl.currentRow()
        if r < 0:
            QMessageBox.information(
                self, "",
                "Vui lòng chọn 1 tài khoản!\n(hoặc double-click vào tên profile)")
            return
        nm_it = self._tbl.item(r, 1)
        name  = nm_it.text() if nm_it else f"Profile {r + 1}"

        if name in self._windows and self._windows[name].isVisible():
            w = self._windows[name]
            if w.isMinimized():
                w.showNormal()
            w.raise_()
            w.activateWindow()
        else:
            w = FacebookWindow(name)
            w.window_closed.connect(lambda nm: self._windows.pop(nm, None))
            self._windows[name] = w
            offset = len(self._windows) * 28
            scr = QApplication.primaryScreen().availableGeometry()
            w.move(min(scr.left() + 80 + offset, scr.right() - 820),
                   min(scr.top()  + 40 + offset, scr.bottom() - 620))
            w.show()

        it = self._tbl.item(r, 2)
        if it:
            it.setText("Chưa login")
            it.setForeground(QBrush(QColor("#a6e3a1")))

    def _open_zalo(self):
        r = self._tbl.currentRow()
        if r < 0:
            QMessageBox.information(self, "", "Vui lòng chọn 1 tài khoản!")
            return
        nm = self._tbl.item(r, 1).text() if self._tbl.item(r, 1) else "Profile"
        QMessageBox.information(self, "Zalo Tiến Khoa",
            f"Đang mở Zalo cho: {nm}\n\n"
            "• Nhắn tin & kết bạn theo danh sách SĐT\n"
            "• Nhắn tin đến bạn bè và nhóm Zalo")

    def _tile_windows(self):
        wins = [w for w in self._windows.values() if w.isVisible()]
        if not wins:
            QMessageBox.information(self, "", "Chưa có cửa sổ Facebook nào đang mở!")
            return
        cols = max(1, self._spin_cols.value())
        rows = (len(wins) + cols - 1) // cols
        scr  = QApplication.primaryScreen().availableGeometry()
        cw   = scr.width() // cols
        ch   = scr.height() // rows
        for idx, win in enumerate(wins):
            col = idx % cols
            row = idx // cols
            win.showNormal()
            win.setGeometry(QRect(
                scr.left() + col * cw,
                scr.top()  + row * ch,
                cw - 4, ch - 4))
            win.raise_()

    def _help(self):
        QMessageBox.information(self, "Hướng dẫn Tiến Khoa",
            "📖 HƯỚNG DẪN:\n\n"
            "1. Nhập tên profile → TẠO PROFILE\n"
            "2. Chọn profile trong bảng\n"
            "3. Bấm MỞ TÍNH NĂNG FACEBOOK\n"
            "4. Đăng nhập Facebook trong tab Trình Duyệt\n"
            "5. Chuyển sang ĐĂNG NHÓM / ĐĂNG PAGE\n\n"
            "📞 HOTLINE: 0961.006.186 (Zalo)")

    def _license(self):
        d = LicenseDialog(self._machine_id, self)
        d.activated.connect(self._on_activated)
        d.exec_()

    def _on_activated(self):
        self._activated = True
        self._sr.setText(
            "✅  Hạn sử dụng: Vĩnh Viễn   ·   Version 13.3.26   ·   Zalo 0961.006.186")
        self._sr.setStyleSheet(
            "color:#a6e3a1;font-weight:bold;font-size:12px;"
            "padding-right:12px;background:transparent;")

    def _update(self):
        QMessageBox.information(self, "Cập nhật", "✅ Phiên bản mới nhất!\n\nVersion 13.3.26")


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("Tiến Khoa")
    app.setQuitOnLastWindowClosed(False)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()