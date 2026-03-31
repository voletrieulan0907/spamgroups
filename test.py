import sys, os, random, time, json
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QGroupBox, QSpinBox, QFileDialog, QMessageBox, QDialog,
    QFrame, QStatusBar, QProgressBar, QCheckBox,
    QAbstractItemView, QMenu, QAction, QHeaderView,
    QListWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal, QEvent
from PyQt5.QtGui import QFont, QColor, QBrush

# Import Selenium worker từ module riêng
from browser_engine import (
    ChromeEmbedWorker, IS_WIN,
    cleanup_profile_cache,
    get_profile_size,
    list_profiles,
)

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


# ═══════════════════════════════════════════════════════════════════════════════
#  BROWSER TAB  — Chrome TỰ ĐỘNG khởi động khi tab này được tạo
# ═══════════════════════════════════════════════════════════════════════════════
class BrowserTab(QWidget):
    """
    Tab TRÌNH DUYỆT:
    - Chrome TỰ ĐỘNG được khởi động ngay khi FacebookWindow mở
    - Windows: nhúng Chrome thực vào Qt container qua WinAPI
    - Mỗi profile = thư mục riêng (cookie/session độc lập)
    - Dùng chromedriver-win64/chromedriver.exe
    """

    def __init__(self, profile_name: str, parent=None):
        super().__init__(parent)
        self.profile_name = profile_name
        self._worker      = None
        self._driver      = None
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Navbar bị ẩn — tạo dummy widgets để navigation methods không lỗi
        self._url_bar  = QLineEdit()
        self._btn_back = QPushButton()
        self._btn_fwd  = QPushButton()
        self._status_lbl = QLabel()

        if not IS_WIN:
            lay.addWidget(self._make_os_notice())
            return

        # Container Qt để nhúng Chrome vào
        self._container = QWidget(self)
        self._container.setAttribute(Qt.WA_NativeWindow, True)
        self._container.setStyleSheet("background:#000;")
        self._container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Install event filter để transfer focus khi click vào container
        self._container.installEventFilter(self)
        lay.addWidget(self._container, 1)

        # Overlay loading (hiện trong khi Chrome đang khởi động)
        self._overlay = QWidget(self._container)
        self._overlay.setStyleSheet("background:#11111b;")
        ov_lay = QVBoxLayout(self._overlay)
        ov_lay.setAlignment(Qt.AlignCenter)

        self._ov_icon = QLabel("🌐")
        self._ov_icon.setFont(QFont("Segoe UI", 40))
        self._ov_icon.setAlignment(Qt.AlignCenter)
        self._ov_icon.setStyleSheet("background:transparent;")

        self._ov_msg = QLabel("Đang khởi động Chrome...\nVui lòng chờ vài giây")
        self._ov_msg.setAlignment(Qt.AlignCenter)
        self._ov_msg.setStyleSheet("color:#a6adc8;font-size:15px;background:transparent;")

        self._ov_bar = QProgressBar()
        self._ov_bar.setRange(0, 0)
        self._ov_bar.setFixedSize(260, 8)
        self._ov_bar.setStyleSheet(
            "QProgressBar{background:#313244;border:none;border-radius:4px;}"
            "QProgressBar::chunk{background:#89b4fa;border-radius:4px;}")

        self._ov_profile = QLabel(f"Profile: {self.profile_name}")
        self._ov_profile.setAlignment(Qt.AlignCenter)
        self._ov_profile.setStyleSheet("color:#6c7086;font-size:11px;background:transparent;")

        ov_lay.addWidget(self._ov_icon)
        ov_lay.addSpacing(10)
        ov_lay.addWidget(self._ov_msg)
        ov_lay.addSpacing(14)
        ov_lay.addWidget(self._ov_bar, 0, Qt.AlignHCenter)
        ov_lay.addSpacing(8)
        ov_lay.addWidget(self._ov_profile)
        self._overlay.show()

    # ── Event filter để transfer focus khi click vào container ────────────────
    def eventFilter(self, obj, event):
        """Catch mouse press + focus events để transfer focus vào Chrome."""
        if obj == self._container:
            # Khi user click vào container hoặc keyboard event
            if event.type() in (QEvent.MouseButtonPress, QEvent.MouseMove, 
                               QEvent.FocusIn, QEvent.KeyPress):
                if self._worker and self._worker._chrome_hwnd:
                    self._worker.set_focus()
                    
        return super().eventFilter(obj, event)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_overlay") and self._overlay:
            self._overlay.setGeometry(self._container.rect())
        # Resize Chrome khi phần mềm resize
        if self._worker:
            sz = self._container.size()
            self._worker.resize_chrome(sz.width(), sz.height())

    def focusInEvent(self, e):
        """Khi BrowserTab nhận focus, transfer vào Chrome."""
        super().focusInEvent(e)
        if self._worker and self._worker._chrome_hwnd:
            QTimer.singleShot(50, self._worker.set_focus)

    # ── Navbar ────────────────────────────────────────────────────────────────
    def _make_navbar(self):
        nav = QWidget()
        nav.setStyleSheet("background:#181825;border-bottom:1px solid #313244;")
        nav.setFixedHeight(44)
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(8, 6, 8, 6)
        nl.setSpacing(5)

        self._btn_back = QPushButton("◀")
        self._btn_back.setFixedSize(32, 32)
        self._btn_back.setStyleSheet(BTN_NAV)
        self._btn_back.setEnabled(False)
        self._btn_back.setToolTip("Quay lại")
        self._btn_back.clicked.connect(self._go_back)

        self._btn_fwd = QPushButton("▶")
        self._btn_fwd.setFixedSize(32, 32)
        self._btn_fwd.setStyleSheet(BTN_NAV)
        self._btn_fwd.setEnabled(False)
        self._btn_fwd.setToolTip("Tiến tới")
        self._btn_fwd.clicked.connect(self._go_fwd)

        self._btn_ref = QPushButton("↺")
        self._btn_ref.setFixedSize(32, 32)
        self._btn_ref.setStyleSheet(BTN_NAV)
        self._btn_ref.setToolTip("Tải lại")
        self._btn_ref.clicked.connect(self._go_refresh)

        btn_home = QPushButton("🏠")
        btn_home.setFixedSize(32, 32)
        btn_home.setStyleSheet(BTN_NAV)
        btn_home.setToolTip("Facebook")
        btn_home.clicked.connect(lambda: self._navigate_to("https://www.facebook.com"))

        self._url_bar = QLineEdit()
        self._url_bar.setPlaceholderText("Nhập địa chỉ URL hoặc từ khóa...")
        self._url_bar.setFixedHeight(32)
        self._url_bar.setStyleSheet(
            "QLineEdit{background:#313244;border:1px solid #45475a;border-radius:16px;"
            "padding:2px 14px;font-size:13px;color:#cdd6f4;}"
            "QLineEdit:focus{border-color:#89b4fa;}")
        self._url_bar.returnPressed.connect(self._on_go)

        btn_go = QPushButton("→")
        btn_go.setFixedSize(32, 32)
        btn_go.setStyleSheet(BTN_NAV)
        btn_go.clicked.connect(self._on_go)

        # Trạng thái Chrome — thay nút "Khởi động" bằng status label
        self._status_lbl = QLabel("⏳  Đang khởi động...")
        self._status_lbl.setFixedHeight(32)
        self._status_lbl.setStyleSheet(
            "background:#313244;color:#fab387;border:1px solid #45475a;"
            "border-radius:4px;padding:0 12px;font-size:12px;font-weight:bold;")

        # Nút Scan Groups để quét groups từ Facebook
        btn_scan = QPushButton("🔍  Scan Groups")
        btn_scan.setFixedHeight(32)
        btn_scan.setStyleSheet(BTN_BLUE(12, 6))
        btn_scan.clicked.connect(self._scan_groups)
        btn_scan.setToolTip("Quét groups từ Facebook (phải login trước)")

        nl.addWidget(self._btn_back)
        nl.addWidget(self._btn_fwd)
        nl.addWidget(self._btn_ref)
        nl.addWidget(btn_home)
        nl.addWidget(self._url_bar, 1)
        nl.addWidget(btn_go)
        nl.addSpacing(8)
        nl.addWidget(btn_scan)
        nl.addWidget(self._status_lbl)
        return nav

    def _make_os_notice(self):
        w = QWidget()
        w.setStyleSheet("background:#11111b;")
        wl = QVBoxLayout(w)
        wl.setAlignment(Qt.AlignCenter)

        icon = QLabel("⚠️")
        icon.setFont(QFont("Segoe UI", 36))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background:transparent;")

        msg = QLabel(
            "<b style='font-size:16px;color:#f38ba8;'>Tính năng nhúng Chrome chỉ hỗ trợ Windows</b><br><br>"
            "<span style='color:#a6adc8;font-size:13px;'>"
            "Trên Linux/macOS, Chrome sẽ mở ra cửa sổ riêng.</span>"
        )
        msg.setTextFormat(Qt.RichText)
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("background:transparent;")
        msg.setWordWrap(True)

        btn = QPushButton("Mở Facebook trong Chrome")
        btn.setFixedSize(240, 40)
        btn.setStyleSheet(BTN_BLUE(13, 8))
        btn.clicked.connect(self._launch_chrome_external)

        wl.addWidget(icon)
        wl.addWidget(msg)
        wl.addSpacing(16)
        wl.addWidget(btn, 0, Qt.AlignHCenter)
        return w

    # ── Auto launch (gọi từ ngoài sau khi widget đã show) ────────────────────
    def auto_launch(self):
        """
        Gọi hàm này ngay sau khi FacebookWindow.show() để Chrome tự khởi động.
        Dùng QTimer để chờ widget render xong trước khi lấy HWND.
        """
        if not IS_WIN:
            self._launch_chrome_external()
            return
        QTimer.singleShot(600, self._launch_chrome_win)

    def _launch_chrome_win(self):
        if self._worker and self._worker.isRunning():
            return
        hwnd = int(self._container.winId())
        sz   = self._container.size()
        self._worker = ChromeEmbedWorker(
            self.profile_name, hwnd, sz.width(), sz.height())
        self._worker.ready.connect(self._on_chrome_ready)
        self._worker.error.connect(self._on_chrome_error)
        self._worker.start()

    # ── Chrome callbacks ──────────────────────────────────────────────────────
    def _on_chrome_ready(self, chrome_pid):
        """Chrome khởi động thành công → lấy driver từ worker."""
        # Lấy driver từ ChromeEmbedWorker
        self._driver = self._worker._driver if self._worker else None
        
        if hasattr(self, "_overlay") and self._overlay:
            self._overlay.hide()
        
        # Set focus vào Chrome
        if self._worker:
            QTimer.singleShot(300, self._worker.set_focus)
        
        # Hiển thị dung lượng profile
        profile_info = get_profile_size(self.profile_name)
        profile_mb = profile_info['size_mb']
        
        self._status_lbl.setText(
            f"✓ Chrome đang chạy (PID={chrome_pid})  ·  "
            f"Profile: {profile_mb}MB"
        )
        self._status_lbl.setStyleSheet(
            "background:#1c2e1c;color:#a6e3a1;border:1px solid #2e4a2e;"
            "border-radius:4px;padding:0 12px;font-size:12px;font-weight:bold;")

    def _on_chrome_error(self, msg):
        if hasattr(self, "_overlay") and self._overlay:
            self._overlay.hide()
        self._status_lbl.setText("⚠  Lỗi Chrome")
        self._status_lbl.setStyleSheet(
            "background:#2e1c1c;color:#f38ba8;border:1px solid #4a2e2e;"
            "border-radius:4px;padding:0 12px;font-size:12px;font-weight:bold;")

        # Hiển thị lỗi + nút thử lại trong container
        err_w = QWidget()
        err_w.setStyleSheet("background:#11111b;")
        err_lay = QVBoxLayout(err_w)
        err_lay.setAlignment(Qt.AlignCenter)

        icon = QLabel("⚠️")
        icon.setFont(QFont("Segoe UI", 32))
        icon.setAlignment(Qt.AlignCenter)
        icon.setStyleSheet("background:transparent;")

        lbl = QLabel(f"<b style='color:#f38ba8;'>Lỗi khởi động Chrome</b><br>"
                     f"<span style='color:#a6adc8;font-size:12px;'>{msg}</span>")
        lbl.setTextFormat(Qt.RichText)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("background:transparent;padding:10px;")

        btn_retry = QPushButton("🔄  Thử lại")
        btn_retry.setFixedSize(160, 36)
        btn_retry.setStyleSheet(BTN_BLUE(13, 8))
        btn_retry.clicked.connect(lambda: (err_w.hide(), self._launch_chrome_win()))

        err_lay.addWidget(icon)
        err_lay.addWidget(lbl)
        err_lay.addSpacing(8)
        err_lay.addWidget(btn_retry, 0, Qt.AlignHCenter)

        if hasattr(self, "_container"):
            parent_lay = self._container.layout() or QVBoxLayout(self._container)
            parent_lay.addWidget(err_w)

    def _launch_chrome_external(self):
        """Fallback Linux/Mac: mở Chrome ra cửa sổ riêng."""
        try:
            from browser_engine.chrome_worker import build_chrome_options, _get_chromedriver_path
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            opts = build_chrome_options(self.profile_name)
            self._driver = webdriver.Chrome(
                service=Service(_get_chromedriver_path()), options=opts)
            self._driver.get("https://www.facebook.com")
            self._status_lbl.setText("✓  Chrome đang chạy (ngoài)")
            self._status_lbl.setStyleSheet(
                "background:#1c2e1c;color:#a6e3a1;border:1px solid #2e4a2e;"
                "border-radius:4px;padding:0 12px;font-size:12px;font-weight:bold;")
        except Exception as e:
            QMessageBox.critical(None, "Lỗi", str(e))

    # ── Navigation ────────────────────────────────────────────────────────────
    def _on_go(self):
        url = self._url_bar.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            url = ("https://" + url) if ("." in url and " " not in url) \
                  else f"https://www.google.com/search?q={url}"
        self._navigate_to(url)

    def _navigate_to(self, url):
        """Navigate to URL - NOT AVAILABLE với Chrome trực tiếp."""
        self._url_bar.setText(url)
        # Chrome trực tiếp không có Selenium driver
        # Người dùng navigate manually qua UI Chrome
        pass

    def _go_back(self):
        """Quay lại - dùng Alt+Left hoặc button Chrome."""
        # Chrome trực tiếp không hỗ trợ programmatic back()
        pass

    def _go_fwd(self):
        """Tiến tới - dùng Alt+Right hoặc button Chrome."""
        # Chrome trực tiếp không hỗ trợ programmatic forward()
        pass

    def _go_refresh(self):
        """Tải lại - dùng F5 hoặc button Chrome."""
        # Chrome trực tiếp không hỗ trợ programmatic refresh()
        pass

    # ── Scan Groups từ Facebook ──────────────────────────────────────────────
    def _scan_groups(self):
        """Quét groups từ Facebook."""
        import sys
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        
        try:
            from action.scan_groups import GroupScanner
        except ImportError:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy module action/scan_groups.py")
            return
        
        # Show loading dialog
        dlg = QMessageBox(self)
        dlg.setWindowTitle("🔍  Đang quét groups...")
        dlg.setText("Vui lòng chờ, đang quét danh sách groups từ Facebook...")
        dlg.setStandardButtons(QMessageBox.NoButton)
        dlg.show()
        QApplication.processEvents()
        
        # Quét groups
        try:
            scanner = GroupScanner(self._driver, self.profile_name)
            result = scanner.scan_groups()
            dlg.close()
            
            if result['success']:
                QMessageBox.information(self, "✓  Quét thành công", result['message'])
            else:
                QMessageBox.warning(self, "⚠  Lỗi", result['message'])
        except Exception as e:
            dlg.close()
            import traceback
            print(traceback.format_exc(), flush=True)
            QMessageBox.critical(self, "Lỗi", f"Lỗi quét groups:\n{e}")

    def closeEvent(self, e):
        if self._worker:
            # Chrome trực tiếp - gọi quit_chrome thay vì quit_driver
            if hasattr(self._worker, 'quit_chrome'):
                self._worker.quit_chrome()
            elif hasattr(self._worker, 'quit_driver'):
                self._worker.quit_driver()
        super().closeEvent(e)


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
        else:
            self.st.setStyleSheet("color:#f38ba8;font-weight:bold;background:transparent;")
            self.st.setText("❌  Key không hợp lệ! Liên hệ Zalo 0961.006.186")


# ═══════════════════════════════════════════════════════════════════════════════
#  FACEBOOK WINDOW  — mở ra là Chrome tự động chạy luôn
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
        self._build()

    def show(self):
        super().show()
        # ── Sau khi cửa sổ show, tự động khởi động Chrome ──
        self._pg_browser.auto_launch()

    def closeEvent(self, e):
        self.window_closed.emit(self.profile_name)
        super().closeEvent(e)

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._make_header())
        root.addWidget(self._make_tabbar())

        self._pg_browser = BrowserTab(self.profile_name, self)
        self._pg_group   = self._build_group()
        self._pg_page    = self._build_page()
        self._pg_settings = self._build_settings()

        for p in [self._pg_browser, self._pg_group, self._pg_page, self._pg_settings]:
            root.addWidget(p)

        sb = QStatusBar()
        sb.setStyleSheet("background:#11111b;border-top:1px solid #313264;"
                         "font-size:12px;color:#6c7086;")
        self.setStatusBar(sb)
        self._sb = sb
        self._switch("browser")

    # ── Header ────────────────────────────────────────────────────────────────
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

    # ── Tab bar ───────────────────────────────────────────────────────────────
    def _make_tabbar(self):
        bar = QWidget()
        bar.setStyleSheet("background:#181825;border-bottom:1px solid #313244;")
        bar.setFixedHeight(44)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self._tb = {}
        for key, txt in [("browser", "  TRÌNH DUYỆT  "),
                          ("group",   "  ĐĂNG NHÓM  "),
                          ("page",    "  ĐĂNG PAGE  "),
                          ("settings", "  CÁCH CANH  ")
                        ]:
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
        self._pg_browser.setVisible(tab == "browser")
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
        fb = QPushButton("Lọc")
        fb.setFixedSize(52, 28)
        fb.setStyleSheet(BTN_GRAY)
        fr.addWidget(fi, 1)
        fr.addWidget(fb)
        lay.addLayout(fr)

        self._gt = QTableWidget()
        self._gt.setColumnCount(3)
        self._gt.setHorizontalHeaderLabels(["#", "ID Nhóm", "Tên Nhóm"])
        self._gt.horizontalHeader().setStretchLastSection(True)
        self._gt.setColumnWidth(0, 32)
        self._gt.setColumnWidth(1, 95)
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
        b1.clicked.connect(self._scan_groups_from_group)
        b2 = QPushButton("📂  LOAD DATA")
        b2.setFixedHeight(34)
        b2.setStyleSheet(BTN_GRAY)
        br.addWidget(b1)
        br.addWidget(b2)
        lay.addLayout(br)
        return p

    def _load_groups(self):
        groups = [
            ("2931648244", "Hội Mua Bán Nhà Đất, BĐS..."),
            ("9509418101", "CHỢ NHÀ ĐẤT TP.HCM"),
            ("1602912457", "Bất Động Sản TP.HCM - M..."),
            ("8734425373", "Hội Mua Bán Nhà Đất TP..."),
            ("1577544889", "NHÀ ĐẤT GIÁ RẺ TP.HCM"),
            ("3383194299", "Hội Mua Bán Nhà Đất TP..."),
            ("3099415852", "Nhà đất Sài Gòn"),
            ("1537704673", "Mua Bán Nhà Đất TP.HCM..."),
            ("1690048136", "Nhóm BĐS Đông Nam SG"),
            ("7978748189", "CHỢ MỸ XUÂN - PHÚ MỸ"),
        ]
        self._gt.setRowCount(len(groups))
        for i, (gid, gnm) in enumerate(groups):
            si = QTableWidgetItem(str(i + 1))
            si.setTextAlignment(Qt.AlignCenter)
            ii = QTableWidgetItem(gid)
            ni = QTableWidgetItem(gnm)
            if i == 4:
                for it in [si, ii, ni]:
                    it.setForeground(QBrush(QColor("#a6e3a1")))
            elif 5 <= i <= 8:
                for it in [si, ii, ni]:
                    it.setForeground(QBrush(QColor("#fab387")))
            self._gt.setItem(i, 0, si)
            self._gt.setItem(i, 1, ii)
            self._gt.setItem(i, 2, ni)
            self._gt.setRowHeight(i, 28)

    def _group_menu(self, pos):
        m = QMenu(self)
        for txt, fn in [("Chọn tất cả", self._gt.selectAll),
                        ("Bỏ chọn tất cả", self._gt.clearSelection)]:
            a = QAction(txt, self)
            a.triggered.connect(fn)
            m.addAction(a)
        m.exec_(self._gt.viewport().mapToGlobal(pos))

    def _make_group_center(self):
        p = QWidget()
        lay = QVBoxLayout(p)
        lay.setContentsMargins(10, 10, 10, 8)
        lay.setSpacing(8)

        gb_nd = QGroupBox("📝  Nội dung bài viết")
        gbl = QVBoxLayout(gb_nd)
        gbl.setContentsMargins(10, 8, 10, 10)
        self._content = QTextEdit()
        self._content.setPlaceholderText(
            "Nhập nội dung vào đây...\n\n"
            "Hỗ trợ Spin content:  {nội dung 1|nội dung 2|nội dung 3}\n"
            "Ví dụ: Bán nhà {quận 1|q1|Q.1}, giá {tốt|hợp lý|cạnh tranh}.")
        self._content.setMinimumHeight(140)
        self._content.setStyleSheet(
            "QTextEdit{background:#181825;border:1px solid #45475a;border-radius:6px;"
            "font-size:13px;color:#cdd6f4;padding:8px;}"
            "QTextEdit:focus{border-color:#89b4fa;}")
        gbl.addWidget(self._content)
        lay.addWidget(gb_nd)

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
        self._pnl_uptop = self._make_uptop_panel()
        lay.addWidget(self._pnl_main)
        lay.addWidget(self._pnl_uptop)
        self._pnl_uptop.setVisible(False)

        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        self._btn_start = QPushButton("▶  BẮT ĐẦU")
        self._btn_start.setFixedHeight(48)
        self._btn_start.setStyleSheet(BTN_GREEN(15, 10))
        self._btn_stop = QPushButton("■  DỪNG LẠI")
        self._btn_stop.setFixedHeight(48)
        self._btn_stop.setEnabled(False)
        self._btn_stop.setStyleSheet(BTN_RED(15, 10))
        self._btn_start.clicked.connect(self._start)
        self._btn_stop.clicked.connect(self._stop)
        ctrl.addWidget(self._btn_start)
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
        ba = QPushButton("⚙ Cấu hình AI")
        ba.setFixedHeight(28)
        ba.setStyleSheet(BTN_BLUE(12, 6))
        bc = QPushButton("📄 Chọn nội dung")
        bc.setFixedHeight(28)
        bc.setStyleSheet(BTN_GRAY)
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
        ACT = ("QPushButton{background:#89b4fa;color:#1e1e2e;border:none;"
               "border-radius:4px;font-size:12px;font-weight:bold;padding:4px 16px;}")
        OFF = ("QPushButton{background:#313244;color:#a6adc8;border:1px solid #45475a;"
               "border-radius:4px;font-size:12px;padding:4px 16px;}"
               "QPushButton:hover{background:#45475a;}")
        for k, b in self._sb_btns.items():
            b.setStyleSheet(ACT if k == tab else OFF)
        if hasattr(self, "_pnl_main"):
            self._pnl_main.setVisible(tab != "uptop")
            self._pnl_uptop.setVisible(tab == "uptop")

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

    def _scan_groups_from_group(self):
        """Quét groups từ Facebook (từ tab ĐĂNG NHÓM)."""
        import sys
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        
        try:
            from action.scan_groups import GroupScanner
        except ImportError:
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy module action/scan_groups.py")
            return
        
        try:
            scanner = GroupScanner(None, self.profile_name)
            result = scanner.scan_groups()
            
            if result['success']:
                self._sb.showMessage(f"✓ {result['message']}")
                self._load_groups()  # Reload lại danh sách groups
            else:
                self._sb.showMessage(f"⚠ {result['message']}")
        except Exception as e:
            import traceback
            print(traceback.format_exc(), flush=True)
            self._sb.showMessage(f"Lỗi quét groups: {e}")

    def _start(self):
        self._running      = True
        self._progress_val = 0
        self._btn_start.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._st_lbl.setText("⏳  Đang chạy...")
        self._timer.start(130)

    def _stop(self):
        self._running = False
        self._timer.stop()
        self._btn_start.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._st_lbl.setText("⏹  Đã dừng")

    def _tick(self):
        self._progress_val = min(self._progress_val + random.randint(1, 3), 100)
        self._pbar.setValue(self._progress_val)
        if self._progress_val >= 100:
            self._timer.stop()
            self._running = False
            self._btn_start.setEnabled(True)
            self._btn_stop.setEnabled(False)
            self._st_lbl.setText("✅  Hoàn thành!")
            ts = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            self._log.append(
                f'<span style="color:#a6e3a1;font-size:11px;">[{ts}]  ✔ HOÀN THÀNH</span>')
            r = self._suc.rowCount()
            self._suc.insertRow(r)
            for j, v in enumerate([ts[11:19], self.profile_name,
                                    "https://fb.com/groups/xxx/posts/yyy"]):
                self._suc.setItem(r, j, QTableWidgetItem(v))

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
    # TAB: CÁCH CANH (Settings/Profile Management)
    # ══════════════════════════════════════════════════════════════════════════
    def _build_settings(self):
        w = QWidget()
        w.setStyleSheet("background:#1e1e2e;")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        
        # ── Title ──
        title = QLabel("🔧  QUẢN LÝ PROFILE")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color:#89b4fa;background:transparent;")
        lay.addWidget(title)
        
        # ── Current Profile Info ──
        current_info = QLabel(f"Profile hiện tại: {self.profile_name}")
        current_info.setStyleSheet("color:#a6adc8;background:transparent;font-size:12px;")
        
        # Get current profile size
        profile_info = get_profile_size(self.profile_name)
        size_info = QLabel(f"Dung lượng: {profile_info['size_mb']} MB")
        size_info.setStyleSheet("color:#a6adc8;background:transparent;font-size:12px;")
        self._size_info_lbl = size_info  # Store reference for update
        
        lay.addWidget(current_info)
        lay.addWidget(size_info)
        lay.addSpacing(8)
        
        # ── Cleanup Button ──
        cleanup_btn = QPushButton("🧹  Xóa Cache & Temp (Cleanup)")
        cleanup_btn.setFixedHeight(36)
        cleanup_btn.setStyleSheet(
            "QPushButton{background:#e74c3c;color:white;border:none;"
            "border-radius:4px;font-weight:bold;font-size:12px;}"
            "QPushButton:hover{background:#c0392b;}"
            "QPushButton:pressed{background:#a93226;}")
        cleanup_btn.clicked.connect(self._do_cleanup_profile)
        lay.addWidget(cleanup_btn)
        
        lay.addSpacing(20)
        
        # ── All Profiles ──
        all_profiles_lbl = QLabel("📂  TẤT CẢ PROFILES")
        all_profiles_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        all_profiles_lbl.setStyleSheet("color:#a6e3a1;background:transparent;")
        lay.addWidget(all_profiles_lbl)
        
        # ── Profiles Table ──
        self._profiles_table = QTableWidget()
        self._profiles_table.setColumnCount(3)
        self._profiles_table.setHorizontalHeaderLabels(["Profile Name", "Size (MB)", "Action"])
        self._profiles_table.horizontalHeader().setStretchLastSection(False)
        self._profiles_table.setColumnWidth(0, 180)
        self._profiles_table.setColumnWidth(1, 100)
        self._profiles_table.setColumnWidth(2, 100)
        self._profiles_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._profiles_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._profiles_table.verticalHeader().setVisible(False)
        self._profiles_table.setShowGrid(False)
        self._profiles_table.setMaximumHeight(300)
        self._profiles_table.setStyleSheet(
            "QTableWidget{background:#181825;border:1px solid #45475a;border-radius:4px;}"
            "QTableWidget::item{padding:4px 6px;border:none;color:#cdd6f4;}"
            "QTableWidget::item:selected{background:#45475a;}"
            "QHeaderView::section{background:#313244;border:none;border-right:1px solid #45475a;"
            "border-bottom:1px solid #45475a;padding:5px 8px;font-weight:bold;color:#cdd6f4;}")
        lay.addWidget(self._profiles_table)
        
        # Refresh button
        refresh_btn = QPushButton("🔄  Làm mới danh sách")
        refresh_btn.setFixedHeight(28)
        refresh_btn.clicked.connect(self._refresh_profiles_list)
        lay.addWidget(refresh_btn)
        
        lay.addStretch()
        
        # ── Initial refresh ──
        self._refresh_profiles_list()
        
        return w
    
    def _refresh_profiles_list(self):
        """Cập nhật danh sách tất cả profiles trong bảng."""
        self._profiles_table.setRowCount(0)
        profiles = list_profiles()
        for i, profile_data in enumerate(profiles):
            self._profiles_table.insertRow(i)
            
            # Profile name
            name_item = QTableWidgetItem(profile_data['name'])
            name_item.setForeground(QColor("#cdd6f4"))
            self._profiles_table.setItem(i, 0, name_item)
            
            # Size
            size_item = QTableWidgetItem(f"{profile_data['size_mb']} MB")
            size_item.setForeground(QColor("#a6adc8"))
            size_item.setTextAlignment(Qt.AlignCenter)
            self._profiles_table.setItem(i, 1, size_item)
            
            # Cleanup button
            cleanup_btn = QPushButton("Cleanup")
            cleanup_btn.setFixedHeight(24)
            cleanup_btn.setStyleSheet(
                "QPushButton{background:#f39c12;color:white;border:none;"
                "border-radius:3px;font-size:10px;}"
                "QPushButton:hover{background:#d68910;}")
            profile_name = profile_data['name']
            cleanup_btn.clicked.connect(
                lambda _, pn=profile_name: self._cleanup_specific_profile(pn))
            self._profiles_table.setCellWidget(i, 2, cleanup_btn)
    
    def _do_cleanup_profile(self):
        """Cleanup profile hiện tại."""
        ret = QMessageBox.question(
            self,
            "Xác nhận Cleanup",
            f"Bạn có chắc chắn muốn xóa cache của profile '{self.profile_name}'?\n\n"
            f"Dữ liệu đăng nhập sẽ được giữ lại.",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.No:
            return
        
        result = cleanup_profile_cache(self.profile_name)
        freed_mb = result['freed_mb']
        after_mb = result['size_after'] // (1024*1024)
        
        QMessageBox.information(
            self,
            "✓  Cleanup hoàn thành",
            f"Đã giải phóng: {freed_mb} MB\n"
            f"Dung lượng còn lại: {after_mb} MB",
            QMessageBox.Ok
        )
        
        # Update lbl
        self._size_info_lbl.setText(f"Dung lượng: {after_mb} MB")
        self._refresh_profiles_list()
    
    def _cleanup_specific_profile(self, profile_name: str):
        """Cleanup specific profile từ table."""
        ret = QMessageBox.question(
            self,
            "Xác nhận Cleanup",
            f"Bạn có chắc chắn muốn xóa cache của profile '{profile_name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if ret == QMessageBox.No:
            return
        
        result = cleanup_profile_cache(profile_name)
        freed_mb = result['freed_mb']
        after_mb = result['size_after'] // (1024*1024)
        
        QMessageBox.information(
            self,
            "✓  Cleanup hoàn thành",
            f"Profile: {profile_name}\n"
            f"Đã giải phóng: {freed_mb} MB\n"
            f"Dung lượng còn lại: {after_mb} MB",
            QMessageBox.Ok
        )
        
        self._refresh_profiles_list()


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
        btn_cr = QPushButton("✚  TẠO PROFILE")
        btn_cr.setFixedHeight(36)
        btn_cr.setStyleSheet(BTN_GREEN(13, 7))
        btn_cr.clicked.connect(self._create)
        brow = QHBoxLayout()
        brow.setSpacing(6)
        for txt, fn in [("🗑 Xóa", self._delete),
                        ("↺ Làm mới", self._refresh),
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
        
        # Load profiles từ file
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
        self._save_profiles()  # Lưu vào file

    def _delete(self):
        r = self._tbl.currentRow()
        if r < 0:
            QMessageBox.information(self, "", "Vui lòng chọn Profile cần xóa!")
            return
        nm = self._tbl.item(r, 1).text() if self._tbl.item(r, 1) else ""
        if QMessageBox.question(self, "Xác nhận", f"Xóa Profile '{nm}'?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self._tbl.removeRow(r)
            self._save_profiles()  # Lưu vào file

    def _refresh(self):
        pass

    def _load_profiles(self):
        """Load danh sách profiles từ file data/profile.json"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            profile_file = os.path.join(base_dir, "data", "profile.json")
            
            if os.path.isfile(profile_file):
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                
                self._tbl.setRowCount(0)
                for profile in profiles:
                    r = self._tbl.rowCount()
                    self._tbl.insertRow(r)
                    
                    # Handle cả format cũ (list) và format mới (dict)
                    if isinstance(profile, dict):
                        # Format mới - dict object
                        row_data = [
                            profile.get("id", ""),
                            profile.get("profile", ""),
                            profile.get("status", ""),
                            profile.get("uid", ""),
                            profile.get("pass", ""),
                            profile.get("2fa", ""),
                            profile.get("email", ""),
                            profile.get("passmail", "")
                        ]
                    else:
                        # Format cũ - list
                        row_data = profile
                    
                    for j, v in enumerate(row_data):
                        it = QTableWidgetItem(str(v))
                        if j == 0:
                            it.setTextAlignment(Qt.AlignCenter)
                        self._tbl.setItem(r, j, it)
                    self._tbl.setRowHeight(r, 32)
        except Exception as e:
            print(f"[ProfileManager] Error loading profiles: {e}")

    def _save_profiles(self):
        """Lưu danh sách profiles vào file data/profile.json dưới dạng JSON object"""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            
            profile_file = os.path.join(data_dir, "profile.json")
            
            profiles = []
            for r in range(self._tbl.rowCount()):
                # Tạo dict object cho mỗi profile
                profile_obj = {
                    "id": self._tbl.item(r, 0).text() if self._tbl.item(r, 0) else "",
                    "profile": self._tbl.item(r, 1).text() if self._tbl.item(r, 1) else "",
                    "status": self._tbl.item(r, 2).text() if self._tbl.item(r, 2) else "",
                    "uid": self._tbl.item(r, 3).text() if self._tbl.item(r, 3) else "",
                    "pass": self._tbl.item(r, 4).text() if self._tbl.item(r, 4) else "",
                    "2fa": self._tbl.item(r, 5).text() if self._tbl.item(r, 5) else "",
                    "email": self._tbl.item(r, 6).text() if self._tbl.item(r, 6) else "",
                    "passmail": self._tbl.item(r, 7).text() if self._tbl.item(r, 7) else ""
                }
                profiles.append(profile_obj)
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, ensure_ascii=False, indent=2)
            
            print(f"[ProfileManager] Saved {len(profiles)} profiles to {profile_file}", flush=True)
        except Exception as e:
            print(f"[ProfileManager] Error saving profiles: {e}")

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
            # show() sẽ tự động gọi auto_launch() bên trong FacebookWindow
            w.show()

        it = self._tbl.item(r, 2)
        if it:
            it.setText("FB: Online")
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
            "   → Chrome TỰ ĐỘNG khởi động và nhúng vào tab TRÌNH DUYỆT\n"
            "   → Mỗi profile = dữ liệu riêng (cookie, session)\n"
            "4. Đăng nhập Facebook trong tab Trình Duyệt\n"
            "5. Chuyển sang ĐĂNG NHÓM / ĐĂNG PAGE\n\n"
            "📁 CẤU TRÚC:\n"
            "   tien_khoa/\n"
            "   ├── main.py\n"
            "   ├── chromedriver-win64/\n"
            "   │   └── chromedriver.exe\n"
            "   └── browser_engine/\n"
            "       ├── __init__.py\n"
            "       └── chrome_worker.py\n\n"
            "💡 Cài đặt:\n"
            "   pip install PyQt5 selenium\n\n"
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
    app = QApplication(sys.argv)
    app.setApplicationName("Tiến Khoa")
    app.setQuitOnLastWindowClosed(False)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps,    True)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()