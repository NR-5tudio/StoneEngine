
import os
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QApplication, QFileDialog, QFrame,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QPixmap
import Core.Helper as helper


CSS_PATH = os.path.join("UserSettings", "Style.css")

_DEFAULTS = {
    "bg-window":           "#060D1A",
    "bg-panel":            "#080F1E",
    "bg-input":            "#050B16",
    "bg-btn-primary":      "#0D2040",
    "bg-btn-primary-h":    "#162E54",
    "bg-btn-primary-p":    "#0A1A30",
    "bg-btn-secondary":    "#050B16",
    "bg-btn-secondary-h":  "#0A1628",
    "bg-browse":           "#0A1628",
    "bg-browse-h":         "#0F2040",
    "border-panel":        "#1A3A5C",
    "border-subtle":       "#1A3A5C",
    "border-accent":       "#2A7FD4",
    "border-accent-h":     "#4A9FFF",
    "border-cancel":       "#0E2035",
    "border-cancel-h":     "#1A3A5C",
    "border-rule":         "#1A3A5C",
    "corner-color":        "#2A7FD4",
    "corner-size":         "14",
    "corner-width":        "2",
    "text-title":          "#E0EEFF",
    "text-normal":         "#A8C8E8",
    "text-bright":         "#D0E8FF",
    "text-accent":         "#2A7FD4",
    "text-accent-h":       "#5AAFFF",
    "text-dim":            "#2A5A8A",
    "text-dim-h":          "#5A9FCC",
    "text-muted":          "#1E3A58",
    "text-muted-h":        "#2A5A8A",
    "text-version":        "#0E2035",
    "text-status":         "#1E4060",
    "text-placeholder":    "#1E3A58",
    "btn-primary-label":   "#7BBFED",
    "btn-primary-label-h": "#C0DEFF",
    "danger":              "#CC4444",
    "selection-bg":        "#1A4A7A",
    "font-mono":           "Courier New, Courier, monospace",
    "font-size-title":     "34",
    "font-size-sub":       "10",
    "font-size-label":     "13",
    "font-size-input":     "12",
    "font-size-btn":       "15",
    "font-size-small":     "10",
    "font-size-tiny":      "9",
    "spacing-panel-h":     "32",
    "spacing-panel-v":     "32",
    "spacing-panel-b":     "24",
    "panel-width":         "380",
    "height-input":        "36",
    "height-btn-main":     "38",
    "height-btn-cancel":   "32",
}

def _load_theme(path: str = CSS_PATH) -> dict:
    """
    Parse CSS custom properties from :root {} in the given file.
    Returns a dict of { 'var-name': 'value' } (-- prefix stripped).
    Missing keys fall back to _DEFAULTS so the engine always starts.
    """
    theme = dict(_DEFAULTS)

    if not os.path.isfile(path):
        print(f"[StyleLoader] '{path}' not found — using built-in defaults.")
        return theme

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except OSError as exc:
        print(f"[StyleLoader] Cannot read '{path}': {exc} — using built-in defaults.")
        return theme

    # Remove block comments
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)

    # Find :root { ... }
    match = re.search(r":root\s*\{([^}]*)\}", raw, re.DOTALL)
    if not match:
        print(f"[StyleLoader] No :root block in '{path}' — using built-in defaults.")
        return theme

    for line in match.group(1).splitlines():
        line = line.strip().rstrip(";")
        if not line.startswith("--") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        theme[key.strip().lstrip("-")] = val.strip()

    return theme

def _make_styles(t: dict) -> dict:
    """Build all QSS strings from theme tokens."""
    f = t["font-mono"]

    return {
        "field": f"""
            QLineEdit {{
                background: {t['bg-input']};
                border: 1px solid {t['border-subtle']};
                color: {t['text-normal']};
                font-family: {f};
                font-size: {t['font-size-input']}px;
                padding: 7px 10px;
                selection-background-color: {t['selection-bg']};
            }}
            QLineEdit:focus {{
                border: 1px solid {t['border-accent']};
                color: {t['text-bright']};
            }}
            QLineEdit::placeholder {{
                color: {t['text-placeholder']};
            }}
        """,

        "primary": f"""
            QPushButton {{
                background: {t['bg-btn-primary']};
                border: 1px solid {t['border-accent']};
                color: {t['btn-primary-label']};
                font-family: {f};
                font-size: {t['font-size-btn']}px;
                letter-spacing: 2px;
                padding: 9px 0px;
            }}
            QPushButton:hover {{
                background: {t['bg-btn-primary-h']};
                border-color: {t['border-accent-h']};
                color: {t['btn-primary-label-h']};
            }}
            QPushButton:pressed {{
                background: {t['bg-btn-primary-p']};
            }}
        """,

        "secondary": f"""
            QPushButton {{
                background: {t['bg-btn-secondary']};
                border: 1px solid {t['border-subtle']};
                color: {t['text-dim']};
                font-family: {f};
                font-size: {t['font-size-btn']}px;
                letter-spacing: 2px;
                padding: 9px 0px;
            }}
            QPushButton:hover {{
                background: {t['bg-btn-secondary-h']};
                border-color: {t['border-accent']};
                color: {t['text-dim-h']};
            }}
        """,

        "browse": f"""
            QPushButton {{
                background: {t['bg-browse']};
                border: 1px solid {t['border-subtle']};
                border-left: none;
                color: {t['text-accent']};
                font-family: {f};
                font-size: {t['font-size-small']}px;
                letter-spacing: 1px;
                padding: 0px 14px;
                min-width: 60px;
            }}
            QPushButton:hover {{
                background: {t['bg-browse-h']};
                border-color: {t['border-accent']};
                border-left: none;
                color: {t['text-accent-h']};
            }}
        """,

        "cancel": f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {t['border-cancel']};
                color: {t['text-muted']};
                font-family: {f};
                font-size: {t['font-size-small']}px;
                letter-spacing: 2px;
                padding: 7px 0px;
            }}
            QPushButton:hover {{
                border-color: {t['border-cancel-h']};
                color: {t['text-muted-h']};
            }}
        """,

        "status_ok": (
            f"color:{t['text-status']}; font-family:{f}; "
            f"font-size:{t['font-size-small']}px; letter-spacing:2px;"
        ),

        "status_err": (
            f"color:{t['danger']}; font-family:{f}; "
            f"font-size:{t['font-size-small']}px; letter-spacing:2px;"
        ),
    }

class _CyberPanel(QWidget):
    """Opaque panel that paints corner brackets using theme tokens."""

    def __init__(self, theme: dict, parent=None):
        super().__init__(parent)
        self._t = theme

    def paintEvent(self, _event):
        t = self._t
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        w, h = self.width(), self.height()

        p.fillRect(0, 0, w, h, QColor(t["bg-panel"]))
        p.setPen(QPen(QColor(t["border-panel"]), 1))
        p.drawRect(0, 0, w - 1, h - 1)

        s  = int(t["corner-size"])
        lw = int(t["corner-width"])
        p.setPen(QPen(QColor(t["corner-color"]), lw))
        # top-left
        p.drawLine(0, s, 0, 0);      p.drawLine(0, 0, s, 0)
        # top-right
        p.drawLine(w - s, 0, w, 0);  p.drawLine(w, 0, w, s)
        # bottom-left
        p.drawLine(0, h - s, 0, h);  p.drawLine(0, h, s, h)
        # bottom-right
        p.drawLine(w - s, h, w, h);  p.drawLine(w, h, w, h - s)


def _rule(t: dict) -> QFrame:
    """1 px horizontal divider line."""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFixedHeight(1)
    line.setStyleSheet(f"background:{t['border-rule']}; border:none;")
    return line


class WelcomeWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.folder_path = ""

        self._theme  = _load_theme()
        self._styles = _make_styles(self._theme)

        self._build_ui()

    # UI
    def _build_ui(self):
        t = self._theme
        s = self._styles
        fn = t["font-mono"]

        # Icon
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.icon = QPixmap("Core/Icons/Icon.png")
        self.scaled_icon = self.icon.scaled(
            200, 200,                  # target size
            Qt.KeepAspectRatio,        # key part
            Qt.SmoothTransformation    # better quality
        )
        self.image_label.setPixmap(self.scaled_icon)

        self.setStyleSheet(f"WelcomeWindow {{ background: {t['bg-window']}; }}")

        # Centre the panel inside the widget
        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        self._panel = _CyberPanel(t)
        self._panel.setFixedWidth(int(t["panel-width"]))
        outer.addWidget(self._panel, alignment=Qt.AlignCenter)

        inner = QVBoxLayout(self._panel)
        inner.setContentsMargins(
            int(t["spacing-panel-h"]),
            int(t["spacing-panel-v"]),
            int(t["spacing-panel-h"]),
            int(t["spacing-panel-b"]),
        )
        inner.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────────────
        lbl_stone = QLabel("STONE")
        lbl_stone.setAlignment(Qt.AlignCenter)
        lbl_stone.setStyleSheet(
            f"color:{t['text-title']}; font-family:{fn}; "
            f"font-size:{t['font-size-title']}px; font-weight:bold; letter-spacing:8px;"
        )
        inner.addWidget(self.image_label)

        lbl_engine = QLabel("ENGINE")
        lbl_engine.setAlignment(Qt.AlignCenter)
        lbl_engine.setStyleSheet(
            f"color:{t['text-accent']}; font-family:{fn}; "
            f"font-size:{t['font-size-sub']}px; letter-spacing:5px; margin-bottom:4px;"
        )
        inner.addWidget(lbl_engine)

        inner.addSpacing(16)
        inner.addWidget(_rule(t))
        inner.addSpacing(16)

        # ── Section label ─────────────────────────────────────────────────────
        lbl_section = QLabel("// NEW PROJECT")
        lbl_section.setStyleSheet(
            f"color:{t['text-dim']}; font-family:{fn}; "
            f"font-size:{t['font-size-label']}px; letter-spacing:3px;"
        )
        inner.addWidget(lbl_section)
        inner.addSpacing(8)

        # ── Project name ──────────────────────────────────────────────────────
        self.pname = QLineEdit()
        self.pname.setPlaceholderText("project_name")
        self.pname.setStyleSheet(s["field"])
        self.pname.setFixedHeight(int(t["height-input"]))
        inner.addWidget(self.pname)
        inner.addSpacing(6)

        # ── Path row ──────────────────────────────────────────────────────────
        path_row = QHBoxLayout()
        path_row.setSpacing(0)

        self.ppath = QLineEdit()
        self.ppath.setPlaceholderText("project_path/")
        self.ppath.setStyleSheet(s["field"])
        self.ppath.setFixedHeight(int(t["height-input"]))

        btn_browse = QPushButton("BROWSE")
        btn_browse.setFixedHeight(int(t["height-input"]))
        btn_browse.setStyleSheet(s["browse"])
        btn_browse.clicked.connect(self.set_path)

        path_row.addWidget(self.ppath)
        path_row.addWidget(btn_browse)
        inner.addLayout(path_row)

        inner.addSpacing(16)
        inner.addWidget(_rule(t))
        inner.addSpacing(16)

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_create = QPushButton("CREATE")
        btn_create.setFixedHeight(int(t["height-btn-main"]))
        btn_create.setStyleSheet(s["primary"])
        btn_create.clicked.connect(self.enter_editor)

        btn_load = QPushButton("LOAD")
        btn_load.setFixedHeight(int(t["height-btn-main"]))
        btn_load.setStyleSheet(s["secondary"])
        btn_load.clicked.connect(self.enter_editor)

        btn_row.addWidget(btn_create)
        btn_row.addWidget(btn_load)
        inner.addLayout(btn_row)

        inner.addSpacing(8)

        btn_cancel = QPushButton("CANCEL")
        btn_cancel.setFixedHeight(int(t["height-btn-cancel"]))
        btn_cancel.setStyleSheet(s["cancel"])
        btn_cancel.clicked.connect(QApplication.quit)
        inner.addWidget(btn_cancel)

        inner.addSpacing(14)

        # ── Status line ───────────────────────────────────────────────────────
        self.ermsg = QLabel("// READY")
        self.ermsg.setAlignment(Qt.AlignCenter)
        self.ermsg.setStyleSheet(s["status_ok"])
        inner.addWidget(self.ermsg)

        inner.addSpacing(6)

        lbl_ver = QLabel("v0.2")
        lbl_ver.setAlignment(Qt.AlignCenter)
        lbl_ver.setStyleSheet(
            f"color:{t['text-version']}; font-family:{fn}; "
            f"font-size:{t['font-size-tiny']}px; letter-spacing:2px;"
        )
        inner.addWidget(lbl_ver)

    # ── Logic ──────────────────────────────────────────────────────────────────

    def enter_editor(self):
        if self.pname.text() == "":
            self._err("// ERR: enter a project name")
            return
        if helper.has_invalid_chars(self.pname.text()):
            self._err("// ERR: A-Z, 0-9, underscore, space only")
            return
        if self.ppath.text() == "":
            self._err("// ERR: select a project folder")
            return
        if not os.path.exists(self.ppath.text()):
            self._err("// ERR: folder not found")
            return

        ProjectPath = helper.create_project(self.pname.text(), self.ppath.text())
        self.hide()
        self.parent().show_editor(ProjectPath)
        self.parent().browser.set_root(ProjectPath)

    def _err(self, msg: str):
        self.ermsg.setStyleSheet(self._styles["status_err"])
        self.ermsg.setText(msg)
        QTimer.singleShot(3000, self._reset_status)

    def _reset_status(self):
        self.ermsg.setStyleSheet(self._styles["status_ok"])
        self.ermsg.setText("// READY")

    def set_path(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder", "")
        if folder:
            self.folder_path = folder
            self.ppath.setText(folder)