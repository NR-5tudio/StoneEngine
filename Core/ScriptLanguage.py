import sys
import os
import re

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget,
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QPushButton, QFileDialog, QMenu,
    QDialog, QLineEdit, QLabel, QToolBar,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QMessageBox, QComboBox, QGroupBox,
    QStatusBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QRegularExpression
from PyQt6.QtGui import (
    QFont, QColor, QSyntaxHighlighter, QTextCharFormat,
    QPalette, QTextCursor, QIcon, QAction
)


# ─────────────────────────────────────────────
#  COLOUR PALETTE
# ─────────────────────────────────────────────
DARK_BG       = "#0f1117"
PANEL_BG      = "#161b27"
EDITOR_BG     = "#1a2035"
BORDER        = "#2a3550"
ACCENT        = "#4fc3f7"
ACCENT2       = "#69f0ae"
ACCENT3       = "#ff8a65"
TEXT_MAIN     = "#e8eaf6"
TEXT_DIM      = "#7986cb"
ERROR_RED     = "#ef5350"
WARNING_YEL   = "#ffca28"
SUCCESS_GRN   = "#66bb6a"

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {DARK_BG};
    color: {TEXT_MAIN};
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}}
QDockWidget {{
    background: {PANEL_BG};
    border: 1px solid {BORDER};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background: {PANEL_BG};
    border-bottom: 2px solid {ACCENT};
    padding: 6px 10px;
    font-weight: bold;
    color: {ACCENT};
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QTextEdit {{
    background-color: {EDITOR_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 13px;
    selection-background-color: #3949ab;
}}
QPushButton {{
    background-color: {PANEL_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px 14px;
    font-weight: bold;
}}
QPushButton:hover {{
    background-color: {BORDER};
    border-color: {ACCENT};
    color: {ACCENT};
}}
QPushButton:pressed {{
    background-color: #263050;
}}
QPushButton#accent {{
    background-color: {ACCENT};
    color: {DARK_BG};
    border: none;
}}
QPushButton#accent:hover {{
    background-color: #81d4fa;
    color: {DARK_BG};
}}
QPushButton#danger {{
    background-color: transparent;
    color: {ERROR_RED};
    border: 1px solid {ERROR_RED};
}}
QPushButton#danger:hover {{
    background-color: {ERROR_RED};
    color: white;
}}
QTableWidget {{
    background-color: {EDITOR_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
}}
QTableWidget::item {{
    padding: 4px 8px;
}}
QTableWidget::item:selected {{
    background-color: #283593;
    color: white;
}}
QHeaderView::section {{
    background-color: {PANEL_BG};
    color: {ACCENT};
    border: none;
    border-bottom: 2px solid {ACCENT};
    padding: 6px 10px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-size: 11px;
}}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    background: {PANEL_BG};
}}
QTabBar::tab {{
    background: {PANEL_BG};
    color: {TEXT_DIM};
    border: 1px solid {BORDER};
    border-bottom: none;
    padding: 6px 18px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    font-weight: bold;
}}
QTabBar::tab:selected {{
    background: {EDITOR_BG};
    color: {ACCENT};
    border-bottom: 2px solid {ACCENT};
}}
QToolBar {{
    background-color: {PANEL_BG};
    border-bottom: 2px solid {BORDER};
    spacing: 6px;
    padding: 4px 8px;
}}
QStatusBar {{
    background-color: {PANEL_BG};
    border-top: 1px solid {BORDER};
    color: {TEXT_DIM};
    font-size: 11px;
}}
QLabel {{
    color: {TEXT_MAIN};
}}
QLabel#title {{
    color: {ACCENT};
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QLineEdit {{
    background-color: {EDITOR_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 8px;
}}
QLineEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox {{
    background-color: {EDITOR_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 8px;
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {EDITOR_BG};
    color: {TEXT_MAIN};
    border: 1px solid {ACCENT};
    selection-background-color: #283593;
}}
QMenu {{
    background-color: {PANEL_BG};
    color: {TEXT_MAIN};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 7px 24px 7px 14px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: #283593;
    color: {ACCENT};
}}
QMenu::separator {{
    height: 1px;
    background-color: {BORDER};
    margin: 4px 8px;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 6px;
    color: {TEXT_DIM};
    font-size: 11px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    color: {ACCENT};
    font-weight: bold;
}}
QScrollBar:vertical {{
    background: {PANEL_BG};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""


# ─────────────────────────────────────────────
#  SCRIPT LANGUAGE DEFINITION
# ─────────────────────────────────────────────
TEMPLATES = {
    # Variables
    "Create Variable": {
        "category": "Variables",
        "english": 'create variable "{Name}" as {Type} = {Value}',
        "cpp": '{Type} {Name} = {Value};',
        "inputs": [("Name", "myVar"), ("Type", "int"), ("Value", "0")],
        "hint": "Creates a new variable you can use later."
    },
    "Set Variable": {
        "category": "Variables",
        "english": 'set "{Name}" to {Value}',
        "cpp": '{Name} = {Value};',
        "inputs": [("Name", "myVar"), ("Value", "0")],
        "hint": "Changes the value of an existing variable."
    },
    "Delete Variable": {
        "category": "Variables",
        "english": 'delete "{Name}"',
        "cpp": '// variable {Name} no longer used',
        "inputs": [("Name", "myVar")],
        "hint": "Marks a variable as deleted (comment in C++)."
    },

    # Output
    "Print": {
        "category": "Output",
        "english": 'print "{Message}"',
        "cpp": 'std::cout << "{Message}" << std::endl;',
        "inputs": [("Message", "Hello World")],
        "hint": "Prints text to the screen / console."
    },
    "Print Variable": {
        "category": "Output",
        "english": 'print value of {Name}',
        "cpp": 'std::cout << {Name} << std::endl;',
        "inputs": [("Name", "myVar")],
        "hint": "Prints the current value of a variable."
    },

    # Control Flow
    "If": {
        "category": "Branches",
        "english": 'if {Condition} then',
        "cpp": 'if ({Condition}) {{\n    // your code here\n}}',
        "inputs": [("Condition", "x > 0")],
        "hint": "Runs code only when a condition is true."
    },
    "If / Else": {
        "category": "Branches",
        "english": 'if {Condition} then\n    // yes\nelse\n    // no',
        "cpp": 'if ({Condition}) {{\n    // yes\n}} else {{\n    // no\n}}',
        "inputs": [("Condition", "x > 0")],
        "hint": "Runs one block if true, another if false."
    },
    "For Loop": {
        "category": "Loops",
        "english": 'repeat {Count} times as {Var}',
        "cpp": 'for (int {Var} = 0; {Var} < {Count}; {Var}++) {{\n    // your code here\n}}',
        "inputs": [("Var", "i"), ("Count", "10")],
        "hint": "Repeats a block of code a set number of times."
    },
    "While Loop": {
        "category": "Loops",
        "english": 'while {Condition} keep doing',
        "cpp": 'while ({Condition}) {{\n    // your code here\n}}',
        "inputs": [("Condition", "running == true")],
        "hint": "Keeps repeating as long as a condition stays true."
    },

    # Functions
    "Define Function": {
        "category": "Functions",
        "english": 'define function {Name}({Params}) returns {ReturnType}',
        "cpp": '{ReturnType} {Name}({Params}) {{\n    // your code here\n    return 0;\n}}',
        "inputs": [("Name", "myFunc"), ("Params", "int x, int y"), ("ReturnType", "int")],
        "hint": "Creates a reusable block of code you can call later."
    },
    "Call Function": {
        "category": "Functions",
        "english": 'call {Name}({Args})',
        "cpp": '{Name}({Args});',
        "inputs": [("Name", "myFunc"), ("Args", "1, 2")],
        "hint": "Runs a function that was defined earlier."
    },
    "Return": {
        "category": "Functions",
        "english": 'return {Value}',
        "cpp": 'return {Value};',
        "inputs": [("Value", "0")],
        "hint": "Sends a value back from a function."
    },

    # Math
    "Add": {
        "category": "Math",
        "english": 'add {A} and {B} store in {Result}',
        "cpp": '{Result} = {A} + {B};',
        "inputs": [("A", "x"), ("B", "y"), ("Result", "sum")],
        "hint": "Adds two values together."
    },
    "Subtract": {
        "category": "Math",
        "english": 'subtract {B} from {A} store in {Result}',
        "cpp": '{Result} = {A} - {B};',
        "inputs": [("A", "x"), ("B", "y"), ("Result", "diff")],
        "hint": "Subtracts one value from another."
    },
    "Multiply": {
        "category": "Math",
        "english": 'multiply {A} by {B} store in {Result}',
        "cpp": '{Result} = {A} * {B};',
        "inputs": [("A", "x"), ("B", "y"), ("Result", "product")],
        "hint": "Multiplies two values."
    },
    "Divide": {
        "category": "Math",
        "english": 'divide {A} by {B} store in {Result}',
        "cpp": '{Result} = {A} / {B};',
        "inputs": [("A", "x"), ("B", "y"), ("Result", "quotient")],
        "hint": "Divides one value by another."
    },

    # Game Engine
    "Spawn Object": {
        "category": "Game Engine",
        "english": 'spawn object {Class} at position ({X}, {Y}, {Z})',
        "cpp": '{Class}* obj = new {Class}();\nobj->SetPosition({X}, {Y}, {Z});',
        "inputs": [("Class", "Actor"), ("X", "0.0f"), ("Y", "0.0f"), ("Z", "0.0f")],
        "hint": "Creates a game object and places it in the world."
    },
    "Destroy Object": {
        "category": "Game Engine",
        "english": 'destroy object {Name}',
        "cpp": 'delete {Name};\n{Name} = nullptr;',
        "inputs": [("Name", "obj")],
        "hint": "Removes a game object from the world."
    },
    "Move Object": {
        "category": "Game Engine",
        "english": 'move {Name} by ({DX}, {DY}, {DZ})',
        "cpp": '{Name}->Translate({DX}, {DY}, {DZ});',
        "inputs": [("Name", "obj"), ("DX", "1.0f"), ("DY", "0.0f"), ("DZ", "0.0f")],
        "hint": "Moves a game object by an offset."
    },
    "Log Message": {
        "category": "Game Engine",
        "english": 'log "{Message}"',
        "cpp": 'ENGINE_LOG("{Message}");',
        "inputs": [("Message", "debug info here")],
        "hint": "Writes a message to the engine's debug log."
    },
}

# C++ type keywords
CPP_TYPES    = ["int", "float", "double", "bool", "char", "string",
                "void", "auto", "long", "short", "unsigned"]
CPP_KEYWORDS = ["if", "else", "for", "while", "return", "delete",
                "new", "class", "struct", "namespace", "include",
                "nullptr", "true", "false", "const", "static",
                "public", "private", "protected", "virtual", "override"]
ENG_KEYWORDS = ["create", "set", "delete", "print", "if", "else",
                "repeat", "while", "define", "call", "return",
                "add", "subtract", "multiply", "divide",
                "spawn", "destroy", "move", "log", "then", "as",
                "times", "doing", "function", "variable", "value",
                "store", "and", "from", "by", "to", "at",
                "position", "object", "returns", "keep"]


# ─────────────────────────────────────────────
#  SYNTAX HIGHLIGHTERS
# ─────────────────────────────────────────────
def _fmt(color, bold=False, italic=False):
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:   f.setFontWeight(700)
    if italic: f.setFontItalic(True)
    return f

class EnglishHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self.rules = []
        kw = _fmt(ACCENT, bold=True)
        for w in ENG_KEYWORDS:
            self.rules.append((QRegularExpression(rf'\b{w}\b', QRegularExpression.PatternOption.CaseInsensitiveOption), kw))
        # Quoted strings
        self.rules.append((QRegularExpression(r'"[^"]*"'), _fmt(ACCENT2)))
        # Numbers
        self.rules.append((QRegularExpression(r'\b\d+(\.\d+)?\b'), _fmt(ACCENT3)))
        # Comments
        self.rules.append((QRegularExpression(r'//[^\n]*'), _fmt(TEXT_DIM, italic=True)))
        # Types
        for t in CPP_TYPES:
            self.rules.append((QRegularExpression(rf'\b{t}\b'), _fmt(WARNING_YEL)))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)

class CppHighlighter(QSyntaxHighlighter):
    def __init__(self, doc):
        super().__init__(doc)
        self.rules = []
        kw_fmt  = _fmt(ACCENT, bold=True)
        typ_fmt = _fmt(WARNING_YEL, bold=True)
        str_fmt = _fmt(ACCENT2)
        num_fmt = _fmt(ACCENT3)
        cmt_fmt = _fmt(TEXT_DIM, italic=True)
        pre_fmt = _fmt("#ce93d8")   # preprocessor purple

        for k in CPP_KEYWORDS:
            self.rules.append((QRegularExpression(rf'\b{k}\b'), kw_fmt))
        for t in CPP_TYPES:
            self.rules.append((QRegularExpression(rf'\b{t}\b'), typ_fmt))
        self.rules.append((QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), str_fmt))
        self.rules.append((QRegularExpression(r'\b\d+(\.\d+)?f?\b'), num_fmt))
        self.rules.append((QRegularExpression(r'//[^\n]*'), cmt_fmt))
        self.rules.append((QRegularExpression(r'#\w+'), pre_fmt))
        # Function calls
        self.rules.append((QRegularExpression(r'\b\w+(?=\s*\()'), _fmt("#80cbc4")))
        # Operators
        self.rules.append((QRegularExpression(r'[=+\-*/<>!&|^~%]'), _fmt(ERROR_RED)))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


# ─────────────────────────────────────────────
#  INSERT TEMPLATE DIALOG
# ─────────────────────────────────────────────
class InsertDialog(QDialog):
    def __init__(self, parent, action, english_editor, variables, functions):
        super().__init__(parent)
        self.action = action
        self.english_editor = english_editor
        self.variables  = variables
        self.functions  = functions
        self.setWindowTitle(f"  ＋  {action}")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"""
            QDialog {{ background: {PANEL_BG}; border: 1px solid {ACCENT}; border-radius: 8px; }}
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        data = TEMPLATES[action]

        # Hint
        hint = QLabel(f"💡  {data['hint']}")
        hint.setStyleSheet(f"color: {ACCENT2}; font-style: italic; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Preview
        preview_label = QLabel("PREVIEW")
        preview_label.setObjectName("title")
        layout.addWidget(preview_label)

        self.preview = QLabel(data["english"])
        self.preview.setStyleSheet(f"""
            background: {EDITOR_BG}; color: {TEXT_MAIN};
            font-family: monospace; font-size: 12px;
            border: 1px solid {BORDER}; border-radius: 4px;
            padding: 8px 10px;
        """)
        self.preview.setWordWrap(True)
        layout.addWidget(self.preview)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER};")
        layout.addWidget(sep)

        inputs_label = QLabel("FILL IN THE BLANKS")
        inputs_label.setObjectName("title")
        layout.addWidget(inputs_label)

        self.inputs = {}
        for name, default in data["inputs"]:
            row = QHBoxLayout()
            lbl = QLabel(name + ":")
            lbl.setFixedWidth(90)
            lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
            inp = QLineEdit()
            inp.setPlaceholderText(default)
            inp.setText(default)
            inp.textChanged.connect(self.update_preview)
            row.addWidget(lbl)
            row.addWidget(inp)
            layout.addLayout(row)
            self.inputs[name] = inp

        self.insert_btn = QPushButton("  ＋  Insert into Script")
        self.insert_btn.setObjectName("accent")
        self.insert_btn.clicked.connect(self.do_insert)
        layout.addWidget(self.insert_btn)

    def update_preview(self):
        data = TEMPLATES[self.action]
        text = data["english"]
        for k, v in self.inputs.items():
            text = text.replace("{" + k + "}", v.text() or f"[{k}]")
        self.preview.setText(text)

    def do_insert(self):
        data = TEMPLATES[self.action]
        english = data["english"]
        for k, v in self.inputs.items():
            english = english.replace("{" + k + "}", v.text())
        self.english_editor.insertPlainText(english + "\n")
        self.accept()


# ─────────────────────────────────────────────
#  VARIABLES TABLE DOCK
# ─────────────────────────────────────────────
class VariablesDock(QWidget):
    def __init__(self, on_change=None):
        super().__init__()
        self.on_change = on_change

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        add_row = QHBoxLayout()
        self.name_inp  = QLineEdit(); self.name_inp.setPlaceholderText("name")
        self.type_inp  = QComboBox()
        self.type_inp.addItems(["int", "float", "double", "bool", "char", "string", "auto"])
        self.val_inp   = QLineEdit(); self.val_inp.setPlaceholderText("value")

        add_btn = QPushButton("+")
        add_btn.setFixedWidth(32)
        add_btn.setObjectName("accent")
        add_btn.clicked.connect(self.add_row)

        add_row.addWidget(self.name_inp, 2)
        add_row.addWidget(self.type_inp, 1)
        add_row.addWidget(self.val_inp, 2)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Type", "Value", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(3, 30)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def add_row(self, name=None, typ=None, val=None):
        n = name or self.name_inp.text().strip()
        t = typ or self.type_inp.currentText()
        v = val or self.val_inp.text().strip()
        if not n: return

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(n))
        self.table.setItem(row, 1, QTableWidgetItem(t))
        self.table.setItem(row, 2, QTableWidgetItem(v))

        btn = QPushButton("✕")
        btn.clicked.connect(lambda: self.remove_row(btn))
        self.table.setCellWidget(row, 3, btn)

        if self.on_change: self.on_change()

    def remove_row(self, btn):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 3) == btn:
                self.table.removeRow(r)
                break
        if self.on_change: self.on_change()

    def get_all(self):
        data = []
        for r in range(self.table.rowCount()):
            n = self.table.item(r, 0)
            t = self.table.item(r, 1)
            v = self.table.item(r, 2)
            data.append((
                n.text() if n else "",
                t.text() if t else "int",
                v.text() if v else "0"
            ))
        return data


# ─────────────────────────────────────────────
#  FUNCTIONS TABLE DOCK
# ─────────────────────────────────────────────
class FunctionsDock(QWidget):
    def __init__(self, on_insert=None):
        super().__init__()
        self.on_insert = on_insert

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        add_row = QHBoxLayout()
        self.fn_name  = QLineEdit()
        self.fn_ret   = QComboBox()
        self.fn_ret.addItems(["void", "int", "float", "double", "bool", "string", "auto"])
        self.fn_params = QLineEdit()

        add_btn = QPushButton("+")
        add_btn.clicked.connect(self.add_row)

        add_row.addWidget(self.fn_name)
        add_row.addWidget(self.fn_ret)
        add_row.addWidget(self.fn_params)
        add_row.addWidget(add_btn)
        layout.addLayout(add_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Name", "Returns", "Params", ""])
        self.table.cellDoubleClicked.connect(self._insert_call)
        layout.addWidget(self.table)

    def add_row(self, name=None, ret=None, params=None):
        n = name or self.fn_name.text().strip()
        r = ret or self.fn_ret.currentText()
        p = params or self.fn_params.text().strip()
        if not n: return

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(n))
        self.table.setItem(row, 1, QTableWidgetItem(r))
        self.table.setItem(row, 2, QTableWidgetItem(p))

        btn = QPushButton("✕")
        btn.clicked.connect(lambda: self.remove_row(btn))
        self.table.setCellWidget(row, 3, btn)

    def remove_row(self, btn):
        for r in range(self.table.rowCount()):
            if self.table.cellWidget(r, 3) == btn:
                self.table.removeRow(r)
                break

    def _insert_call(self, row, col):
        if self.on_insert:
            n = self.table.item(row, 0)
            p = self.table.item(row, 2)
            name = n.text() if n else ""
            params = p.text() if p else ""
            args = ", ".join(["0"] * len(params.split(",")) if params else [])
            self.on_insert(f"call {name}({args})\n")

    def get_all(self):
        data = []
        for r in range(self.table.rowCount()):
            n = self.table.item(r, 0)
            ret = self.table.item(r, 1)
            p = self.table.item(r, 2)
            data.append((
                n.text() if n else "",
                ret.text() if ret else "void",
                p.text() if p else ""
            ))
        return data


# ─────────────────────────────────────────────
#  ENGLISH → C++ COMPILER
# ─────────────────────────────────────────────
class Compiler:
    """
    Translates the plain-English script into C++ code.
    Returns (cpp_code, errors).
    """

    ENGLISH_TO_CPP = {
        # Pattern: (regex, cpp_template, error_if_bad)
    }

    RULES = [
        # Variables
        (r'^create variable "(.+?)" as (\w+) = (.+)$',
         lambda m: f'{m.group(2)} {m.group(1)} = {m.group(3)};'),
        (r'^set "(.+?)" to (.+)$',
         lambda m: f'{m.group(1)} = {m.group(2)};'),
        (r'^delete "(.+?)"$',
         lambda m: f'// variable {m.group(1)} deleted'),
        # Output
        (r'^print "(.+)"$',
         lambda m: f'std::cout << "{m.group(1)}" << std::endl;'),
        (r'^print value of (\w+)$',
         lambda m: f'std::cout << {m.group(1)} << std::endl;'),
        # Branches
        (r'^if (.+) then$',
         lambda m: f'if ({m.group(1)}) {{'),
        (r'^else$',
         lambda m: '} else {'),
        (r'^end$',
         lambda m: '}'),
        # Loops
        (r'^repeat (\d+) times as (\w+)$',
         lambda m: f'for (int {m.group(2)} = 0; {m.group(2)} < {m.group(1)}; {m.group(2)}++) {{'),
        (r'^while (.+) keep doing$',
         lambda m: f'while ({m.group(1)}) {{'),
        # Functions
        (r'^define function (\w+)\((.+)\) returns (\w+)$',
         lambda m: f'{m.group(3)} {m.group(1)}({m.group(2)}) {{'),
        (r'^define function (\w+)\(\) returns (\w+)$',
         lambda m: f'{m.group(2)} {m.group(1)}() {{'),
        (r'^call (\w+)\((.+)\)$',
         lambda m: f'{m.group(1)}({m.group(2)});'),
        (r'^call (\w+)\(\)$',
         lambda m: f'{m.group(1)}();'),
        (r'^return (.+)$',
         lambda m: f'return {m.group(1)};'),
        # Math
        (r'^add (.+) and (.+) store in (\w+)$',
         lambda m: f'{m.group(3)} = {m.group(1)} + {m.group(2)};'),
        (r'^subtract (.+) from (.+) store in (\w+)$',
         lambda m: f'{m.group(3)} = {m.group(2)} - {m.group(1)};'),
        (r'^multiply (.+) by (.+) store in (\w+)$',
         lambda m: f'{m.group(3)} = {m.group(1)} * {m.group(2)};'),
        (r'^divide (.+) by (.+) store in (\w+)$',
         lambda m: f'{m.group(3)} = {m.group(1)} / {m.group(2)};'),
        # Game Engine
        (r'^spawn object (\w+) at position \((.+), (.+), (.+)\)$',
         lambda m: f'{m.group(1)}* obj = new {m.group(1)}();\nobj->SetPosition({m.group(2)}, {m.group(3)}, {m.group(4)});'),
        (r'^destroy object (\w+)$',
         lambda m: f'delete {m.group(1)};\n{m.group(1)} = nullptr;'),
        (r'^move (\w+) by \((.+), (.+), (.+)\)$',
         lambda m: f'{m.group(1)}->Translate({m.group(2)}, {m.group(3)}, {m.group(4)});'),
        (r'^log "(.+)"$',
         lambda m: f'ENGINE_LOG("{m.group(1)}");'),
        # Comments
        (r'^//(.*)$',
         lambda m: f'//{m.group(1)}'),
        (r'^#(.*)$',
         lambda m: f'// {m.group(1)}'),
    ]

    # Plain-English error explanations
    ERROR_HINTS = {
        "create variable": 'Try:  create variable "myVar" as int = 0',
        "set":             'Try:  set "myVar" to 42',
        "print":           'Try:  print "Hello World"',
        "if":              'Try:  if x > 0 then',
        "repeat":          'Try:  repeat 10 times as i',
        "while":           'Try:  while running == true keep doing',
        "define function": 'Try:  define function myFunc(int x) returns int',
        "call":            'Try:  call myFunc(1, 2)',
        "add":             'Try:  add x and y store in sum',
        "subtract":        'Try:  subtract y from x store in diff',
        "multiply":        'Try:  multiply x by y store in product',
        "divide":          'Try:  divide x by y store in quotient',
        "spawn":           'Try:  spawn object Actor at position (0.0f, 0.0f, 0.0f)',
    }

    def compile(self, english_text, variables, functions):
        lines = english_text.split("\n")
        cpp_lines = []
        errors    = []
        indent    = 0

        # Header
        cpp_lines.append("#include <iostream>")
        cpp_lines.append("#include <string>")
        cpp_lines.append("")

        # Variables from table
        if variables:
            cpp_lines.append("// ── Variables ──────────────────────────")
            for name, typ, val in variables:
                cpp_lines.append(f"{typ} {name} = {val};")
            cpp_lines.append("")

        # Function declarations from table
        if functions:
            cpp_lines.append("// ── Function Declarations ───────────────")
            for name, ret, params in functions:
                cpp_lines.append(f"{ret} {name}({params});")
            cpp_lines.append("")

        cpp_lines.append("// ── Script ──────────────────────────────")

        for i, raw in enumerate(lines, 1):
            stripped = raw.strip()
            if not stripped:
                cpp_lines.append("")
                continue

            matched = False
            for pattern, converter in self.RULES:
                m = re.match(pattern, stripped, re.IGNORECASE)
                if m:
                    result = converter(m)
                    # handle de-indent keywords
                    if stripped.lower() in ("else", "end", "}", "};"):
                        indent = max(0, indent - 1)
                    indented = "\n".join("    " * indent + l for l in result.split("\n"))
                    cpp_lines.append(indented)
                    # increase indent after openers
                    if result.rstrip().endswith("{"):
                        indent += 1
                    matched = True
                    break

            if not matched and stripped:
                # Guess what the user was trying
                first_word = stripped.split()[0].lower()
                hint = ""
                for kw, tip in self.ERROR_HINTS.items():
                    if kw in stripped.lower():
                        hint = f"\n   💡 {tip}"
                        break
                errors.append(f"Line {i}: I don't understand → \"{stripped}\"{hint}")
                cpp_lines.append("    " * indent + f"// ❌ Unknown: {stripped}")

        return "\n".join(cpp_lines), errors


# ─────────────────────────────────────────────
#  MAIN EDITOR
# ─────────────────────────────────────────────
class StoneEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🪨  Stone Engine  —  Script Editor")
        self.resize(1400, 860)
        self.compiler = Compiler()
        self._build_ui()
        self._connect()
        self._compile()

    # ── Build UI ────────────────────────────────
    def _build_ui(self):
        # ─ Toolbar ─
        tb = QToolBar("Main")
        tb.setMovable(False)
        self.addToolBar(tb)

        def tb_btn(label, tip, slot):
            btn = QPushButton(label)
            btn.setToolTip(tip)
            btn.clicked.connect(slot)
            tb.addWidget(btn)

        tb_btn("📂 Open", "Open file", self.open_file)
        tb_btn("💾 Save", "Save file", self.save_file)
        tb_btn("▶ Compile", "Compile script", self._compile)

        # ─ Status bar ─
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # ─ Central ─
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(splitter)

        # ─ English Editor ─
        self.english = QTextEdit()
        splitter.addWidget(self.english)

        # ─ C++ Output ─
        self.cpp_out = QTextEdit()
        self.cpp_out.setReadOnly(True)
        splitter.addWidget(self.cpp_out)

        # ─ LEFT DOCK (FIXED) ─
        left_dock = QDockWidget("📊 Data Tables")

        tabs = QTabWidget()

        self.vars_dock = VariablesDock(on_change=self._compile)
        self.fns_dock  = FunctionsDock(on_insert=self._insert_fn_call)

        tabs.addTab(self.vars_dock, "🗂 Variables")
        tabs.addTab(self.fns_dock,  "🔧 Functions")

        left_dock.setWidget(tabs)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, left_dock)
        left_dock.setMinimumWidth(320)

        # ─ Errors panel ─
        err_dock = QDockWidget("⚠️ Errors")
        self.errors_out = QTextEdit()
        self.errors_out.setReadOnly(True)
        err_dock.setWidget(self.errors_out)

        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, err_dock)

    # ── Connections ──────────────────────────────
    def _connect(self):
        timer = QTimer(self)
        timer.setInterval(600)
        timer.timeout.connect(self._compile)
        self.english.textChanged.connect(timer.start)

    # ── Compile ──────────────────────────────────
    def _compile(self):
        text = self.english.toPlainText()
        variables = self.vars_dock.get_all()
        functions = self.fns_dock.get_all()

        cpp, errors = self.compiler.compile(text, variables, functions)
        self.cpp_out.setPlainText(cpp)

        if errors:
            self.errors_out.setPlainText("\n\n".join(errors))
            self.status.showMessage(f"{len(errors)} errors")
        else:
            self.errors_out.setPlainText("No errors")
            self.status.showMessage("Compiled")

    # ── Insert function call ─
    def _insert_fn_call(self, text):
        self.english.insertPlainText(text)

    # ── File ops ─
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self)
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.english.setPlainText(f.read())

    def save_file(self):
        path, _ = QFileDialog.getSaveFileName(self)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.english.toPlainText())


# ─────────────────────────────────────────────
#  ENTRY
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    # Seed with a demo script
    w = StoneEditor()
    w.english.setPlainText(
        '// Stone Engine Demo Script\n'
        'create variable "score" as int = 0\n'
        'create variable "playerName" as string = "Hero"\n'
        '\n'
        'define function setup() returns void\n'
        '    print "Game started!"\n'
        '    spawn object Actor at position (0.0f, 0.0f, 0.0f)\n'
        'end\n'
        '\n'
        'if score > 100 then\n'
        '    print "You win!"\n'
        'else\n'
        '    print "Keep going!"\n'
        'end\n'
        '\n'
        'repeat 5 times as i\n'
        '    add score and 10 store in score\n'
        'end\n'
    )

    # Seed variables table
    for n, t, v in [("score","int","0"),("playerName","string",'"Hero"')]:
        w.vars_dock.add_row(n, t, v)

    # Seed functions table
    w.fns_dock.add_row("setup", "void", "")

    w.show()
    sys.exit(app.exec())