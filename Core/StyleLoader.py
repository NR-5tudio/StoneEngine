import json
import os


def rgba(values: list[int]) -> str:
    """Convert [R, G, B, A] list to CSS rgba() string."""
    r, g, b, a = values
    alpha = round(a / 255, 3)
    return f"rgba({r}, {g}, {b}, {alpha})"


def generate_qss(json_path: str = "Style.json",) -> str:
    with open(json_path, "r") as f:
        c = json.load(f)

    qss = f"""
/* Auto-generated from {os.path.basename(json_path)} — do not edit manually */

/* =========================
   Windows
   ========================= */
QMainWindow, QWidget {{
    background-color: {rgba(c["QMainWindow_QWidget"]["background"])};
    color: {rgba(c["QMainWindow_QWidget"]["color"])};
}}

QDockWidget {{
    background-color: {rgba(c["QDockWidget"]["background"])};
    border: 1px solid {rgba(c["QDockWidget"]["border"])};
}}

QDockWidget::title {{
    background-color: {rgba(c["QDockWidget_title"]["background"])};
    color: {rgba(c["QDockWidget_title"]["color"])};
    padding: 6px;
    border-radius: 6px;
}}

/* =========================
   Buttons
   ========================= */
QPushButton {{
    background-color: {rgba(c["QPushButton"]["background"])};
    border-radius: 8px;
    padding: 8px;
    color: {rgba(c["QPushButton"]["color"])};
    border: 1px solid {rgba(c["QPushButton"]["border"])};
}}

QPushButton:hover {{
    background-color: {rgba(c["QPushButton_hover"]["background"])};
}}

QPushButton:pressed {{
    background-color: {rgba(c["QPushButton_pressed"]["background"])};
}}

/* =========================
   Inputs
   ========================= */
QLineEdit, QTextEdit {{
    background-color: {rgba(c["QLineEdit_QTextEdit"]["background"])};
    border-radius: 8px;
    padding: 8px;
    color: {rgba(c["QLineEdit_QTextEdit"]["color"])};
    border: 1px solid {rgba(c["QLineEdit_QTextEdit"]["border"])};
}}

QLineEdit:hover, QTextEdit:hover {{
    border: 1px solid {rgba(c["QLineEdit_QTextEdit_hover"]["border"])};
}}

/* =========================
   ComboBox
   ========================= */
QComboBox {{
    background-color: {rgba(c["QComboBox"]["background"])};
    border-radius: 8px;
    padding: 6px;
    color: {rgba(c["QComboBox"]["color"])};
    border: 1px solid {rgba(c["QComboBox"]["border"])};
}}

QComboBox:hover {{
    border: 1px solid {rgba(c["QComboBox_hover"]["border"])};
}}

QComboBox QAbstractItemView {{
    background-color: {rgba(c["QComboBox_QAbstractItemView"]["background"])};
    selection-background-color: {rgba(c["QComboBox_QAbstractItemView"]["selection_background"])};
    selection-color: {rgba(c["QComboBox_QAbstractItemView"]["selection_color"])};
    color: {rgba(c["QComboBox_QAbstractItemView"]["color"])};
    border: 1px solid {rgba(c["QComboBox_QAbstractItemView"]["border"])};
    outline: 0;
}}

QComboBox QAbstractItemView::item {{
    padding: 6px 8px;
    border-radius: 4px;
}}

QComboBox QAbstractItemView::item:hover {{
    background-color: {rgba(c["QComboBox_QAbstractItemView_item_hover"]["background"])};
    color: {rgba(c["QComboBox_QAbstractItemView_item_hover"]["color"])};
}}

/* =========================
   CheckBox
   ========================= */
QCheckBox {{
    color: {rgba(c["QCheckBox"]["color"])};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid {rgba(c["QCheckBox_indicator"]["border"])};
    background-color: {rgba(c["QCheckBox_indicator"]["background"])};
}}

QCheckBox::indicator:checked {{
    background-color: {rgba(c["QCheckBox_indicator_checked"]["background"])};
}}

/* =========================
   RadioButton
   ========================= */
QRadioButton {{
    color: {rgba(c["QRadioButton"]["color"])};
    spacing: 6px;
}}

QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid {rgba(c["QRadioButton_indicator"]["border"])};
    background-color: {rgba(c["QRadioButton_indicator"]["background"])};
}}

QRadioButton::indicator:checked {{
    background-color: {rgba(c["QRadioButton_indicator_checked"]["background"])};
}}

/* =========================
   List
   ========================= */
QListWidget {{
    background-color: {rgba(c["QListWidget"]["background"])};
    border: 1px solid {rgba(c["QListWidget"]["border"])};
    color: {rgba(c["QListWidget"]["color"])};
}}

QListWidget::item {{
    padding: 6px;
}}

QListWidget::item:hover {{
    background-color: {rgba(c["QListWidget_item_hover"]["background"])};
}}

QListWidget::item:selected {{
    background-color: {rgba(c["QListWidget_item_selected"]["background"])};
}}

/* =========================
   View Items
   ========================= */
QAbstractItemView {{
    background-color: {rgba(c["QAbstractItemView"]["background"])};
    selection-background-color: {rgba(c["QAbstractItemView"]["selection_background"])};
    color: {rgba(c["QAbstractItemView"]["color"])};
}}

/* =========================
   Scrollbar
   ========================= */
QScrollBar:vertical {{
    background: {rgba(c["QScrollBar_vertical"]["background"])};
    width: 10px;
}}

QScrollBar::handle:vertical {{
    background: {rgba(c["QScrollBar_handle_vertical"]["background"])};
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {rgba(c["QScrollBar_handle_vertical_hover"]["background"])};
}}

/* =========================
   MenuBar
   ========================= */
QMenuBar {{
    background-color: {rgba(c["QMenuBar"]["background"])};
    color: {rgba(c["QMenuBar"]["color"])};
    border-bottom: 1px solid {rgba(c["QMenuBar"]["border_bottom"])};
}}

QMenuBar::item {{
    background: transparent;
    padding: 6px 10px;
}}

QMenuBar::item:selected {{
    background-color: {rgba(c["QMenuBar_item_selected"]["background"])};
    color: {rgba(c["QMenuBar_item_selected"]["color"])};
}}

/* =========================
   Menu
   ========================= */
QMenu {{
    background-color: {rgba(c["QMenu"]["background"])};
    color: {rgba(c["QMenu"]["color"])};
    border: 1px solid {rgba(c["QMenu"]["border"])};
}}

QMenu::item {{
    padding: 6px 20px;
}}

QMenu::item:selected {{
    background-color: {rgba(c["QMenu_item_selected"]["background"])};
}}

/* =========================
   ToolButton
   ========================= */
QToolButton {{
    background-color: transparent;
    color: {rgba(c["QToolButton"]["color"])};
    padding: 6px;
    border: none;
}}

QToolButton:hover {{
    background-color: {rgba(c["QToolButton_hover"]["background"])};
    border-radius: 6px;
}}

QToolButton:pressed {{
    background-color: {rgba(c["QToolButton_pressed"]["background"])};
}}
""".strip()


    return qss


if __name__ == "__main__":
    generate_qss()