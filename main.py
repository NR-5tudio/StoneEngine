import sys
import re
import os

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt

import Core.Editor as E
import EasyJson as json
import Core.StyleLoader as style
import subprocess


CSS_PATH = os.path.join("UserSettings", "Style.css")

_DEFAULTS = {
    # welcome backgrounds
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
    # borders
    "border-panel":        "#1A3A5C",
    "border-subtle":       "#1A3A5C",
    "border-accent":       "#2A7FD4",
    "border-accent-h":     "#4A9FFF",
    "border-cancel":       "#0E2035",
    "border-cancel-h":     "#1A3A5C",
    "border-rule":         "#1A3A5C",
    # corner brackets
    "corner-color":        "#2A7FD4",
    "corner-size":         "14",
    "corner-width":        "2",
    # welcome text
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
    # button labels
    "btn-primary-label":   "#7BBFED",
    "btn-primary-label-h": "#C0DEFF",
    # danger / selection
    "danger":              "#CC4444",
    "selection-bg":        "#1A4A7A",
    # editor-wide
    "editor-bg":           "#07111F",
    "editor-surface":      "#0C1A2E",
    "editor-border":       "#162840",
    "editor-text":         "#B8D0E8",
    "editor-text-dim":     "#4A6A8A",
    "editor-accent":       "#1A4A7A",
    "editor-accent-text":  "#C0DEFF",
    "editor-scrollbar":    "#1A3A5C",
    "editor-scrollbar-h":  "#2A7FD4",
    "editor-tab-active":   "#0D2040",
    "editor-tab-text":     "#7BBFED",
    "editor-menu-bg":      "#080F1E",
    "editor-menu-text":    "#A8C8E8",
    "editor-menu-sel":     "#1A3A5C",
    # typography
    "font-mono":           "Courier New, Courier, monospace",
    "font-ui":             "Segoe UI, Arial, sans-serif",
    "font-size-title":     "34",
    "font-size-sub":       "10",
    "font-size-label":     "9",
    "font-size-input":     "12",
    "font-size-btn":       "11",
    "font-size-small":     "10",
    "font-size-tiny":      "9",
    "font-size-ui":        "12",
    # spacing / heights
    "spacing-panel-h":     "32",
    "spacing-panel-v":     "32",
    "spacing-panel-b":     "24",
    "panel-width":         "380",
    "height-input":        "36",
    "height-btn-main":     "38",
    "height-btn-cancel":   "32",
}


def _load_theme(path: str = CSS_PATH) -> dict:
    """Parse :root { --var: value; } from Style.css. Falls back to _DEFAULTS."""
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

    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
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


def _build_global_qss(t: dict) -> str:
    """
    Convert theme tokens into a single QSS string applied to the QApplication.
    Covers: QMainWindow, QWidget, QMenuBar, QMenu, QToolBar, QDockWidget,
            QTreeView, QListView, QTableView, QHeaderView, QScrollBar,
            QTabWidget, QTabBar, QSplitter, QStatusBar, QLabel,
            QPushButton, QLineEdit, QTextEdit, QPlainTextEdit.
    """
    f  = t["font-ui"]
    fs = t["font-size-ui"]

    return f"""

    /* ── Base ──────────────────────────────────────────────────────────────── */
    QWidget {{
        background-color: {t['editor-bg']};
        color: {t['editor-text']};
        font-family: {f};
        font-size: {fs}px;
        border: none;
        outline: none;
    }}

    QMainWindow {{
        background-color: {t['editor-bg']};
    }}

    /* ── Menu bar ───────────────────────────────────────────────────────────── */
    QMenuBar {{
        background-color: {t['editor-menu-bg']};
        color: {t['editor-menu-text']};
        border-bottom: 1px solid {t['editor-border']};
        padding: 2px 4px;
    }}
    QMenuBar::item {{
        background: transparent;
        padding: 4px 10px;
    }}
    QMenuBar::item:selected {{
        background: {t['editor-menu-sel']};
        color: {t['editor-text']};
    }}

    QMenu {{
        background-color: {t['editor-menu-bg']};
        color: {t['editor-menu-text']};
        border: 1px solid {t['editor-border']};
        padding: 4px 0px;
    }}
    QMenu::item {{
        padding: 5px 24px 5px 12px;
    }}
    QMenu::item:selected {{
        background: {t['editor-menu-sel']};
        color: {t['editor-text']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {t['editor-border']};
        margin: 3px 8px;
    }}

    /* ── Toolbar ─────────────────────────────────────────────────────────────── */
    QToolBar {{
        background-color: {t['editor-surface']};
        border-bottom: 1px solid {t['editor-border']};
        spacing: 4px;
        padding: 2px 4px;
    }}
    QToolBar::separator {{
        width: 1px;
        background: {t['editor-border']};
        margin: 4px 2px;
    }}
    QToolButton {{
        background: transparent;
        color: {t['editor-text']};
        border: 1px solid transparent;
        padding: 3px 6px;
    }}
    QToolButton:hover {{
        background: {t['editor-accent']};
        border-color: {t['editor-scrollbar']};
        color: {t['editor-accent-text']};
    }}
    QToolButton:pressed {{
        background: {t['editor-menu-sel']};
    }}

    /* ── Dock widgets ────────────────────────────────────────────────────────── */
    QDockWidget {{
        color: {t['editor-text']};
        titlebar-close-icon: none;
        titlebar-normal-icon: none;
    }}
    QDockWidget::title {{
        background: {t['editor-surface']};
        border-bottom: 1px solid {t['editor-border']};
        padding: 4px 8px;
        text-align: left;
        font-size: {fs}px;
        color: {t['editor-text-dim']};
        letter-spacing: 1px;
    }}
    QDockWidget::close-button,
    QDockWidget::float-button {{
        background: transparent;
        border: none;
        padding: 0px;
    }}

    /* ── Splitter ────────────────────────────────────────────────────────────── */
    QSplitter::handle {{
        background: {t['editor-border']};
    }}
    QSplitter::handle:horizontal {{ width: 1px; }}
    QSplitter::handle:vertical   {{ height: 1px; }}

    /* ── Tree / List / Table views ───────────────────────────────────────────── */
    QTreeView, QListView, QTableView {{
        background-color: {t['editor-bg']};
        alternate-background-color: {t['editor-surface']};
        color: {t['editor-text']};
        border: 1px solid {t['editor-border']};
        selection-background-color: {t['editor-accent']};
        selection-color: {t['editor-accent-text']};
        gridline-color: {t['editor-border']};
        outline: none;
    }}
    QTreeView::item, QListView::item, QTableView::item {{
        padding: 3px 6px;
    }}
    QTreeView::item:hover, QListView::item:hover {{
        background: {t['editor-menu-sel']};
    }}
    QTreeView::item:selected, QListView::item:selected {{
        background: {t['editor-accent']};
        color: {t['editor-accent-text']};
    }}
    QTreeView::branch {{
        background: {t['editor-bg']};
    }}
    QTreeView::branch:has-children:closed {{
        border-image: none;
    }}

    QHeaderView::section {{
        background: {t['editor-surface']};
        color: {t['editor-text-dim']};
        border: none;
        border-right: 1px solid {t['editor-border']};
        border-bottom: 1px solid {t['editor-border']};
        padding: 4px 8px;
    }}

    /* ── Scrollbars ──────────────────────────────────────────────────────────── */
    QScrollBar:vertical {{
        background: {t['editor-bg']};
        width: 8px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: {t['editor-scrollbar']};
        min-height: 24px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['editor-scrollbar-h']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background: {t['editor-bg']};
        height: 8px;
        border: none;
    }}
    QScrollBar::handle:horizontal {{
        background: {t['editor-scrollbar']};
        min-width: 24px;
        border-radius: 4px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {t['editor-scrollbar-h']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ── Tab bar ─────────────────────────────────────────────────────────────── */
    QTabWidget::pane {{
        border: 1px solid {t['editor-border']};
        background: {t['editor-bg']};
    }}
    QTabBar::tab {{
        background: {t['editor-surface']};
        color: {t['editor-text-dim']};
        border: 1px solid {t['editor-border']};
        border-bottom: none;
        padding: 5px 14px;
        margin-right: 1px;
    }}
    QTabBar::tab:selected {{
        background: {t['editor-tab-active']};
        color: {t['editor-tab-text']};
        border-bottom: 2px solid {t['border-accent']};
    }}
    QTabBar::tab:hover:!selected {{
        background: {t['editor-menu-sel']};
        color: {t['editor-text']};
    }}

    /* ── Status bar ──────────────────────────────────────────────────────────── */
    QStatusBar {{
        background: {t['editor-surface']};
        color: {t['editor-text-dim']};
        border-top: 1px solid {t['editor-border']};
        font-size: {fs}px;
    }}
    QStatusBar::item {{
        border: none;
    }}

    /* ── Labels ──────────────────────────────────────────────────────────────── */
    QLabel {{
        background: transparent;
        color: {t['editor-text']};
    }}

    /* ── Push buttons (editor chrome) ────────────────────────────────────────── */
    QPushButton {{
        background: {t['editor-surface']};
        color: {t['editor-text']};
        border: 1px solid {t['editor-border']};
        padding: 5px 14px;
    }}
    QPushButton:hover {{
        background: {t['editor-accent']};
        border-color: {t['border-accent']};
        color: {t['editor-accent-text']};
    }}
    QPushButton:pressed {{
        background: {t['editor-menu-sel']};
    }}
    QPushButton:disabled {{
        color: {t['editor-text-dim']};
        border-color: {t['editor-border']};
    }}

    /* ── Line / text edits ───────────────────────────────────────────────────── */
    QLineEdit {{
        background: {t['bg-input']};
        color: {t['text-normal']};
        border: 1px solid {t['border-subtle']};
        padding: 4px 8px;
        selection-background-color: {t['selection-bg']};
    }}
    QLineEdit:focus {{
        border-color: {t['border-accent']};
        color: {t['text-bright']};
    }}

    QTextEdit, QPlainTextEdit {{
        background: {t['bg-input']};
        color: {t['text-normal']};
        border: 1px solid {t['editor-border']};
        selection-background-color: {t['selection-bg']};
    }}
    QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {t['border-accent']};
    }}

    /* ── Combo box ───────────────────────────────────────────────────────────── */
    QComboBox {{
        background: {t['editor-surface']};
        color: {t['editor-text']};
        border: 1px solid {t['editor-border']};
        padding: 4px 8px;
    }}
    QComboBox:hover {{
        border-color: {t['border-accent']};
    }}
    QComboBox QAbstractItemView {{
        background: {t['editor-menu-bg']};
        color: {t['editor-menu-text']};
        border: 1px solid {t['editor-border']};
        selection-background-color: {t['editor-menu-sel']};
        selection-color: {t['editor-text']};
        outline: none;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    /* ── Tooltip ─────────────────────────────────────────────────────────────── */
    QToolTip {{
        background: {t['editor-menu-bg']};
        color: {t['editor-text']};
        border: 1px solid {t['editor-border']};
        padding: 4px 8px;
    }}

    """


def apply_dark_theme(app: QApplication):
    app.setStyle("Fusion")

    # QPalette keeps non-QSS widgets (native dialogs, etc.) consistent
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(7,  17, 31))
    palette.setColor(QPalette.WindowText,      QColor(184, 208, 232))
    palette.setColor(QPalette.Base,            QColor(5,  11, 22))
    palette.setColor(QPalette.AlternateBase,   QColor(12, 26, 46))
    palette.setColor(QPalette.Text,            QColor(184, 208, 232))
    palette.setColor(QPalette.Button,          QColor(12, 26, 46))
    palette.setColor(QPalette.ButtonText,      QColor(184, 208, 232))
    palette.setColor(QPalette.Highlight,       QColor(26, 74, 122))
    palette.setColor(QPalette.HighlightedText, QColor(192, 222, 255))
    palette.setColor(QPalette.ToolTipBase,     QColor(8,  15, 30))
    palette.setColor(QPalette.ToolTipText,     QColor(168, 200, 232))
    app.setPalette(palette)

    # Load CSS → build QSS → apply globally
    theme = _load_theme()
    app.setStyleSheet(_build_global_qss(theme))


def run():
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    app.setFont(QFont("Segoe UI", 12))

    world = {
        "actors":   [],
        "scripts":  [],
        "selected": None,
    }

    editor = E.Editor(world)
    editor.resize(1200, 700)
    editor.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()   