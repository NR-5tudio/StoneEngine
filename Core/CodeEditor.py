"""
BlockBuilderDock + BlockBuilderManager
=======================================
A PyQt5 dock-widget system that loads Python files as draggable code blocks.

Architecture note
-----------------
Each open file is represented by a ``FileSession``.  A FileSession owns:
  • the block-list data / logic  (``BlockEditorWidget`` — a plain QWidget)
  • save/dirty state
  • the QDockWidget shell used *only* when the session is popped out

The ``BlockBuilderManager`` owns a QStackedWidget that holds the
``BlockEditorWidget`` directly.  No widget is ever shared between a
QDockWidget and a QStackedWidget — that is what caused the blank-view bug.

Public API
----------
    manager = BlockBuilderManager(parent=main_window)
    main_window.addDockWidget(Qt.RightDockWidgetArea, manager)
    manager.open_file("/absolute/path/to/script.py")   # from file browser
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PyQt5.QtCore import Qt, QFileSystemWatcher, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat
from PyQt5.QtWidgets import (
    QAbstractItemView, QAction, QApplication, QDockWidget, QFileDialog,
    QFrame, QHBoxLayout, QInputDialog, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton,
    QSizePolicy, QSplitter, QStackedWidget, QTabBar, QVBoxLayout, QWidget,
)


_D = {
    "bg":      "#14161C",
    "border":  "#2B313D",
    "dim":     "#7C8594",

    "sel":     "#465F8F",

    "tab_on":  "#1E2A3A",
    "tab_off": "#14161C",

    "accent":  "#4A6FAF"
}

_SS = f"""
    QWidget {{
        font-family:'Consolas','Courier New',monospace;
    }}
    QListWidget {{
        alternate-background-color:#2a2a2a;
        selection-background-color:{_D['sel']}; selection-color:#fff;
    }}
    QListWidget::item {{ padding:6px 8px; border-bottom:1px solid #2e2e2e; }}
    QPlainTextEdit {{ background:{_D['bg']}; border:none; }}
    QPushButton {{
        :#ccc; border:1px solid #555;
        border-radius:4px; padding:0 10px; font-size:11px;
    }}
    QSplitter::handle {{ background:{_D['border']}; height:3px; }}
    QMenu {{ background:#2d2d2d; color:#ddd; border:1px solid #555; }}
    QMenu::item:selected {{ background:#3a3a3a; }}
"""

_DOCK_SS = f"""
    QDockWidget {{ background:{_D['bg']}; }}
    QDockWidget::title {{
        padding:4px 8px; font-weight:bold; font-size:11px;
    }}
"""

_TAB_SS = f"""
    QTabBar::tab {{
        background:{_D['tab_off']}; color:{_D['dim']};
        border:1px solid {_D['border']}; border-bottom:none;
        padding:5px 12px; margin-right:2px;
        font-size:10px; min-width:80px;
    }}
    QTabBar::tab:selected {{
        background:{_D['tab_on']}; 
        border-top:2px solid {_D['accent']};
    }}

"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _indent_level(line: str) -> int:
    s = line.lstrip()
    return 0 if not s else (len(line) - len(s)) // 4


def parse_file_to_blocks(path: Path) -> list[dict]:
    blocks = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        blocks.append({"text": raw.strip(), "indent": _indent_level(raw)})
    return blocks


def blocks_to_source(items):
    lines = []

    for it in items:
        if hasattr(it, 'indent'): pass
        else:
            it.indent = 0
        indent_level = it.indent

        if hasattr(it, 'block_text'): pass
        else:
            it.block_text = "# Error, using comment"
        text = it.block_text

        indentation = "    " * indent_level
        full_line = indentation + text

        lines.append(full_line)

    result = "\n".join(lines)
    return result


# ---------------------------------------------------------------------------
# Syntax highlighter
# ---------------------------------------------------------------------------

class _PythonHighlighter(QSyntaxHighlighter):
    _KW = (
        "False|None|True|and|as|assert|async|await|break|class|continue|"
        "def|del|elif|else|except|finally|for|from|global|if|import|in|"
        "is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield"
    )

    def __init__(self, doc):
        super().__init__(doc)

        def _f(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(QFont.Bold)
            return f

        self._rules = [
            (re.compile(r"\b(" + self._KW + r")\b"), _f("#569cd6", True)),
            (re.compile(r'\".*?\"|\'.*?\''),           _f("#ce9178")),
            (re.compile(r"#[^\n]*"),                   _f("#6a9955")),
            (re.compile(r"\b\d+(\.\d+)?\b"),           _f("#b5cea8")),
        ]

    def highlightBlock(self, text):
        for pat, fmt in self._rules:
            for m in pat.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ---------------------------------------------------------------------------
# BlockItem
# ---------------------------------------------------------------------------

class BlockItem(QListWidgetItem):
    def __init__(self, text: str, indent: int = 0):
        super().__init__()
        self.block_text = text
        self.indent = max(0, min(indent, 20))
        self._refresh()

    def _refresh(self):
        self.setText("  " * self.indent + self.block_text)
        self.setToolTip(f"indent={self.indent}  |  {self.block_text}")

    def set_text(self, text: str):
        self.block_text = text
        self._refresh()

    def set_indent(self, level: int):
        self.indent = max(0, min(level, 20))
        self._refresh()


# ---------------------------------------------------------------------------
# BlockListWidget
# ---------------------------------------------------------------------------

class BlockListWidget(QListWidget):
    blocksChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSpacing(2)
        self.setFont(QFont("Consolas", 10))
        self.model().rowsMoved.connect(lambda *_: self.blocksChanged.emit())
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx)

    def _ctx(self, pos: QPoint):
        item: Optional[BlockItem] = self.itemAt(pos)
        if item is None:
            return
        menu = QMenu(self)
        menu.setStyleSheet(_SS)
        ae = QAction("✏  Edit content",       menu)
        ai = QAction("→  Change indent level", menu)
        ad = QAction("🗑  Delete block",        menu)
        menu.addActions([ae, ai])
        menu.addSeparator()
        menu.addAction(ad)
        ae.triggered.connect(lambda: self._edit_text(item))
        ai.triggered.connect(lambda: self._edit_indent(item))
        ad.triggered.connect(lambda: self._del(item))
        menu.exec_(self.viewport().mapToGlobal(pos))

    def _edit_text(self, item: BlockItem):
        t, ok = QInputDialog.getText(self, "Edit block", "Content:", text=item.block_text)
        if ok and t.strip():
            item.set_text(t.strip())
            self.blocksChanged.emit()

    def _edit_indent(self, item: BlockItem):
        lv, ok = QInputDialog.getInt(
            self, "Indent level", "Level (0-20):", value=item.indent, min=0, max=20
        )
        if ok:
            item.set_indent(lv)
            self.blocksChanged.emit()

    def _del(self, item: BlockItem):
        self.takeItem(self.row(item))
        self.blocksChanged.emit()

    def all_blocks(self) -> list[BlockItem]:
        return [self.item(i) for i in range(self.count())]

    def add_block(self, text: str, indent: int = 0):
        self.addItem(BlockItem(text, indent))
        self.blocksChanged.emit()


# ---------------------------------------------------------------------------
# BlockEditorWidget  — the REAL content widget (plain QWidget, never a dock)
# ---------------------------------------------------------------------------

class BlockEditorWidget(QWidget):
    """
    Self-contained editor for one Python file.
    Always a plain QWidget — the manager embeds it directly in a QStackedWidget.
    A QDockWidget shell is created separately only when popped out.

    Signals
    -------
    codeChanged(str)      — on every block mutation
    saveRequested()       — Save toolbar button clicked
    saveAsRequested()     — Save As toolbar button clicked
    closeRequested()      — Close button clicked (after internal dirty check)
    returnRequested()     — Return button clicked (pop-out mode only)
    dirtyChanged(bool)    — dirty flag toggled
    """

    codeChanged     = pyqtSignal(str)
    saveRequested   = pyqtSignal()
    saveAsRequested = pyqtSignal()
    closeRequested  = pyqtSignal()
    returnRequested = pyqtSignal()
    dirtyChanged    = pyqtSignal(bool)

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self._path  = path
        self._dirty = False
        self.setStyleSheet(_SS)
        self._build()
        self._load()

    # -- build -------------------------------------------------------------

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # toolbar
        tb = QHBoxLayout()
        tb.setSpacing(4)

        self._lbl = QLabel(self._path.name)
        self._lbl.setFont(QFont("Consolas", 9))
        self._lbl.setStyleSheet(f"color:{_D['dim']};")
        self._lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._lbl.setToolTip(str(self._path))

        def _btn(label, slot):
            b = QPushButton(label)
            b.setFixedHeight(28)
            b.clicked.connect(slot)
            return b

        self._btn_add     = _btn("＋ Block",   self._add_block)
        self._btn_copy    = _btn("⎘ Copy",     self._copy)
        self._btn_save    = _btn("💾 Save",    self.saveRequested.emit)
        self._btn_save_as = _btn("💾 Save As", self.saveAsRequested.emit)
        self._btn_return  = _btn("↩ Return",   self.returnRequested.emit)
        self._btn_close   = _btn("✕ Close",    self._close_clicked)

        self._btn_return.setToolTip("Return to manager")
        self._btn_return.setVisible(False)

        for w in (
            self._lbl,
            self._btn_add, self._btn_copy,
            self._btn_save, self._btn_save_as,
            self._btn_return, self._btn_close,
        ):
            tb.addWidget(w)

        root.addLayout(tb)

        # splitter: block list / code preview
        splitter = QSplitter(Qt.Vertical)

        self._list = BlockListWidget()
        self._list.blocksChanged.connect(self._on_changed)
        splitter.addWidget(self._list)
        splitter.setSizes([400, 220])
        pf = QFrame()
        pf.setFrameShape(QFrame.StyledPanel)
        pfl = QVBoxLayout(pf)
        pfl.setContentsMargins(0, 0, 0, 0)
        pfl.setSpacing(0)

        ph = QLabel("  Generated code")
        ph.setFixedHeight(24)
        ph.setStyleSheet(
            f"color:{_D['dim']};"
            " font-size:10px; padding-left:4px;"
        )
        # pfl.addWidget(ph)

        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setFont(QFont("Consolas", 10))
        self._preview.setLineWrapMode(QPlainTextEdit.NoWrap)
        _PythonHighlighter(self._preview.document())
        # pfl.addWidget(self._preview)

        splitter.addWidget(pf)
        splitter.setSizes([400, 220])
        root.addWidget(splitter)

    # -- file loading ------------------------------------------------------

    def _load(self):
        if not self._path.exists():
            return
        blocks = parse_file_to_blocks(self._path)
        self._list.clear()
        for b in blocks:
            self._list.addItem(BlockItem(b["text"], b["indent"]))
        self._set_dirty(False)
        self._refresh_preview()

    # -- properties --------------------------------------------------------

    @property
    def path(self) -> Path:
        return self._path

    @path.setter
    def path(self, p: Path):
        self._path = p
        self._lbl.setText(p.name)
        self._lbl.setToolTip(str(p))

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def generated_code(self) -> str:
        return blocks_to_source(self._list.all_blocks())

    def mark_clean(self):
        self._set_dirty(False)

    # -- pop-out mode ------------------------------------------------------

    def set_popped_out(self, popped: bool):
        self._btn_return.setVisible(popped)

    # -- dirty flag --------------------------------------------------------

    def _set_dirty(self, dirty: bool):
        if self._dirty == dirty:
            return
        self._dirty = dirty
        self.dirtyChanged.emit(dirty)

    # -- slots -------------------------------------------------------------

    def _on_changed(self):
        self._set_dirty(True)
        self._refresh_preview()
        self.codeChanged.emit(self.generated_code())

    def _refresh_preview(self):
        self._preview.setPlainText(self.generated_code())

    def _add_block(self):
        t, ok = QInputDialog.getText(self, "New block", "Enter code line:")
        if ok and t.strip():
            self._list.add_block(t.strip(), indent=0)

    def _copy(self):
        QApplication.clipboard().setText(self.generated_code())

    def _close_clicked(self):
        if self._dirty:
            choice = self._ask_sdc()
            if choice == "cancel":
                return
            if choice == "save":
                # Emit save first; manager will call close after saving
                self.saveRequested.emit()
                return
        self.closeRequested.emit()

    # -- dialogs -----------------------------------------------------------

    def _ask_sdc(self) -> str:
        """Show Save / Don't Save / Cancel.  Returns 'save'|'discard'|'cancel'."""
        mb = QMessageBox(self)
        mb.setWindowTitle("Unsaved changes")
        mb.setText(f"<b>{self._path.name}</b> has unsaved changes.")
        mb.setInformativeText("Save before closing?")
        mb.setIcon(QMessageBox.Warning)
        bs = mb.addButton("Save",        QMessageBox.AcceptRole)
        bd = mb.addButton("Don't Save",  QMessageBox.DestructiveRole)
        bc = mb.addButton("Cancel",      QMessageBox.RejectRole)
        mb.setDefaultButton(bs)
        mb.exec_()
        c = mb.clickedButton()
        return "save" if c is bs else ("discard" if c is bd else "cancel")

    def prompt_save_discard_cancel(self) -> str:
        """Public — called by the manager on tab-bar close."""
        return self._ask_sdc()

    def notify_file_deleted(self):
        """Called when QFileSystemWatcher reports the file is gone."""
        mb = QMessageBox(self)
        mb.setWindowTitle("File no longer exists")
        mb.setIcon(QMessageBox.Warning)
        mb.setText(
            f"<b>This file no longer exists on disk:</b><br>"
            f"<code>{self._path}</code>"
        )
        mb.setInformativeText(
            "The content shown is your last known version.\n"
            "What would you like to do?"
        )
        mb.setDetailedText(self.generated_code())
        br = mb.addButton("Recreate file",           QMessageBox.AcceptRole)
        bk = mb.addButton("Keep editing (unsaved)",  QMessageBox.NoRole)
        bc = mb.addButton("Close tab",               QMessageBox.DestructiveRole)
        mb.setDefaultButton(br)
        mb.exec_()
        clicked = mb.clickedButton()
        if clicked is br:
            self.saveRequested.emit()
        elif clicked is bk:
            self._set_dirty(True)
        else:
            self._dirty = False
            self.closeRequested.emit()


# ---------------------------------------------------------------------------
# _FileSession  — internal record per open file
# ---------------------------------------------------------------------------

class _FileSession:
    def __init__(self, editor: BlockEditorWidget):
        self.editor: BlockEditorWidget = editor
        self.dock: Optional[QDockWidget] = None   # only when popped out
        self.tab_index: int = -1

    @property
    def path(self) -> Path:
        return self.editor.path

    @property
    def is_dirty(self) -> bool:
        return self.editor.is_dirty

    @property
    def is_floating(self) -> bool:
        return self.dock is not None


# ---------------------------------------------------------------------------
# BlockBuilderManager
# ---------------------------------------------------------------------------

class BlockBuilderManager(QWidget):
    """
    Widget that hosts multiple file sessions in browser-style tabs.
    Creates its own QDockWidget (self.dock) so it can be added to a QMainWindow.

    Usage
    -----
        manager = BlockBuilderManager(parent=main_window)
        # self.dock is already added to parent via addDockWidget in __init__
        manager.open_file("/path/to/script.py")
    """

    def __init__(self, parent: Optional[QMainWindow] = None):
        super().__init__()
        self._mw: Optional[QMainWindow] = parent

        self.dock = QDockWidget("Block Builder", parent)
        self.dock.setWidget(self)
        self.dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        self.dock.setStyleSheet(_DOCK_SS)

        # path -> _FileSession
        self._sessions: dict[Path, _FileSession] = {}

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)

        self._build_ui()

        if parent is not None:
            parent.addDockWidget(Qt.RightDockWidgetArea, self.dock)

    # -- UI ----------------------------------------------------------------

    def _build_ui(self):
        self.setStyleSheet(_SS)
        vl = QVBoxLayout(self)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(0)

        # tab bar row
        tab_row = QWidget()
        tab_row.setFixedHeight(34)
        tab_row.setStyleSheet(
            f"border-bottom:1px solid {_D['border']};"
        )
        trl = QHBoxLayout(tab_row)
        trl.setContentsMargins(4, 2, 4, 0)
        trl.setSpacing(0)

        self._tabs = QTabBar()
        self._tabs.setMovable(True)
        self._tabs.setTabsClosable(True)
        self._tabs.setExpanding(False)
        self._tabs.setDrawBase(False)
        self._tabs.setFont(QFont("Consolas", 10))
        self._tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._tabs.setStyleSheet(_TAB_SS)
        self._tabs.currentChanged.connect(self._on_tab_switched)
        self._tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        self._tabs.tabMoved.connect(self._rebuild_tab_indices)
        self._tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tabs.customContextMenuRequested.connect(self._tab_ctx_menu)

        trl.addWidget(self._tabs)
        vl.addWidget(tab_row)

        # stacked widget — holds BlockEditorWidgets directly (key fix)
        self._stack = QStackedWidget()
        vl.addWidget(self._stack)

        # placeholder when no files are open
        ph = QLabel("Open a file from the file browser to get started.")
        ph.setAlignment(Qt.AlignCenter)
        ph.setStyleSheet(f"color:{_D['dim']}; font-size:12px;")
        self._stack.addWidget(ph)
        self._placeholder = ph

        # layout is set directly on self — no setWidget needed

    # -- Public API --------------------------------------------------------

    def open_file(self, full_file_path: str | Path):
        """
        Open a file in the manager.
        If already open (manager or floating), focus it instead of re-opening.
        """
        path = Path(full_file_path).resolve()

        if path in self._sessions:
            sess = self._sessions[path]
            if sess.is_floating:
                if sess.dock:
                    sess.dock.raise_()
                    sess.dock.activateWindow()
            else:
                self._tabs.setCurrentIndex(sess.tab_index)
            return

        # Create editor — note: parent=None, lives inside the stack
        editor = BlockEditorWidget(path, parent=None)
        sess = _FileSession(editor)
        self._sessions[path] = sess

        # Wire signals
        editor.saveRequested.connect(  lambda p=path: self._save(p))
        editor.saveAsRequested.connect(lambda p=path: self._save_as(p))
        editor.closeRequested.connect( lambda p=path: self._remove_session(p))
        editor.returnRequested.connect(lambda p=path: self._return_from_float(p))
        editor.dirtyChanged.connect(   lambda dirty, p=path: self._update_tab_label(p, dirty))

        # Put editor directly into the stack
        self._stack.addWidget(editor)
        self._stack.setCurrentWidget(editor)

        # Add tab
        idx = self._tabs.addTab(path.name)
        self._tabs.setTabToolTip(idx, str(path))
        sess.tab_index = idx
        self._tabs.setCurrentIndex(idx)

        # Watch file
        self._watcher.addPath(str(path))

    # -- Tab events --------------------------------------------------------

    def _on_tab_switched(self, index: int):
        if index < 0:
            return
        sess = self._session_for_tab(index)
        if sess and not sess.is_floating:
            self._stack.setCurrentWidget(sess.editor)

    def _on_tab_close_requested(self, index: int):
        sess = self._session_for_tab(index)
        if sess:
            self._close_file(sess.path)

    def _tab_ctx_menu(self, pos: QPoint):
        idx = self._tabs.tabAt(pos)
        if idx < 0:
            return
        sess = self._session_for_tab(idx)
        if not sess:
            return
        menu = QMenu(self)
        menu.setStyleSheet(_SS)
        a_pop   = QAction("⧉  Pop out to own dock", menu)
        a_close = QAction("✕  Close tab",            menu)
        menu.addAction(a_pop)
        menu.addSeparator()
        menu.addAction(a_close)
        a_pop.triggered.connect(  lambda: self._pop_out(sess.path))
        a_close.triggered.connect(lambda: self._close_file(sess.path))
        menu.exec_(self._tabs.mapToGlobal(pos))

    # -- Save logic --------------------------------------------------------

    def _save(self, path: Path) -> bool:
        sess = self._sessions.get(path)
        if not sess:
            return False
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(sess.editor.generated_code(), encoding="utf-8")
            sess.editor.mark_clean()
            self._watcher.addPath(str(path))   # re-add (watcher drops deleted paths)
            return True
        except OSError as e:
            QMessageBox.critical(self, "Save failed", str(e))
            return False

    def _save_as(self, path: Path) -> bool:
        sess = self._sessions.get(path)
        if not sess:
            return False
        new_str, _ = QFileDialog.getSaveFileName(
            self, "Save As", str(path), "Python files (*.py);;All files (*)"
        )
        if not new_str:
            return False

        new_path = Path(new_str).resolve()
        try:
            new_path.parent.mkdir(parents=True, exist_ok=True)
            new_path.write_text(sess.editor.generated_code(), encoding="utf-8")
        except OSError as e:
            QMessageBox.critical(self, "Save As failed", str(e))
            return False

        # Remap session to new path
        self._sessions.pop(path)
        sess.editor.path = new_path
        self._sessions[new_path] = sess
        sess.editor.mark_clean()

        self._watcher.removePath(str(path))
        self._watcher.addPath(str(new_path))

        idx = sess.tab_index
        self._tabs.setTabText(idx, new_path.name)
        self._tabs.setTabToolTip(idx, str(new_path))
        return True

    # -- Close logic -------------------------------------------------------

    def _close_file(self, path: Path):
        """Close with dirty check.  Called from tab × or context menu."""
        sess = self._sessions.get(path)
        if not sess:
            return
        if sess.is_dirty:
            choice = sess.editor.prompt_save_discard_cancel()
            if choice == "cancel":
                return
            if choice == "save":
                if not self._save(path):
                    return
        self._remove_session(path)

    def _remove_session(self, path: Path):
        """Unconditionally tear down a session (no dirty check)."""
        sess = self._sessions.pop(path, None)
        if not sess:
            return

        # Tear down floating dock shell if present
        if sess.is_floating and sess.dock:
            sess.dock.setWidget(None)
            if self._mw:
                self._mw.removeDockWidget(sess.dock)
            sess.dock.deleteLater()
            sess.dock = None

        # Remove editor from stack
        self._stack.removeWidget(sess.editor)
        sess.editor.deleteLater()

        # Remove tab
        idx = sess.tab_index
        if 0 <= idx < self._tabs.count():
            self._tabs.removeTab(idx)
        self._rebuild_tab_indices()

        self._watcher.removePath(str(path))

        if self._tabs.count() == 0:
            self._stack.setCurrentWidget(self._placeholder)

    # -- Pop-out / return --------------------------------------------------

    def _pop_out(self, path: Path):
        sess = self._sessions.get(path)
        if not sess or sess.is_floating:
            return

        editor = sess.editor

        # Remove editor from stack (dock shell will own it temporarily)
        self._stack.removeWidget(editor)

        # Remove tab
        idx = sess.tab_index
        if 0 <= idx < self._tabs.count():
            self._tabs.removeTab(idx)
        self._rebuild_tab_indices()
        sess.tab_index = -1

        # Build a thin dock shell
        dock = QDockWidget(f"Block Builder — {path.name}", self._mw)
        dock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        dock.setStyleSheet(_DOCK_SS)
        dock.setWidget(editor)
        editor.set_popped_out(True)
        sess.dock = dock

        if self._mw:
            self._mw.addDockWidget(Qt.RightDockWidgetArea, dock)
        dock.setFloating(True)
        dock.show()

    def _return_from_float(self, path: Path):
        sess = self._sessions.get(path)
        if not sess or not sess.is_floating:
            return

        dock  = sess.dock
        editor = sess.editor

        # Detach editor from dock WITHOUT destroying it
        dock.setWidget(None)
        editor.setParent(None)          # clear Qt parent so stack can adopt it
        editor.set_popped_out(False)

        if self._mw:
            self._mw.removeDockWidget(dock)
        dock.deleteLater()
        sess.dock = None

        # Re-insert into stack
        self._stack.addWidget(editor)
        self._stack.setCurrentWidget(editor)

        # Re-add tab
        label = path.name + (" *" if sess.is_dirty else "")
        idx = self._tabs.addTab(label)
        self._tabs.setTabToolTip(idx, str(path))
        sess.tab_index = idx
        self._tabs.setCurrentIndex(idx)

    # -- File deletion detection -------------------------------------------

    def _on_file_changed(self, file_path: str):
        path = Path(file_path).resolve()
        if path.exists():
            self._watcher.addPath(str(path))   # re-add; Qt drops watched path on save
            return
        sess = self._sessions.get(path)
        if sess:
            QTimer.singleShot(200, sess.editor.notify_file_deleted)

    # -- Helpers -----------------------------------------------------------

    def _session_for_tab(self, index: int) -> Optional[_FileSession]:
        for sess in self._sessions.values():
            if sess.tab_index == index:
                return sess
        return None

    def _rebuild_tab_indices(self, *_):
        """Re-sync tab_index for all non-floating sessions after move/remove."""
        for i in range(self._tabs.count()):
            tip = self._tabs.tabToolTip(i)
            if not tip:
                continue
            p = Path(tip).resolve()
            if p in self._sessions:
                self._sessions[p].tab_index = i

    def _update_tab_label(self, path: Path, dirty: bool):
        sess = self._sessions.get(path)
        if not sess or sess.is_floating:
            return
        idx = sess.tab_index
        if 0 <= idx < self._tabs.count():
            self._tabs.setTabText(idx, path.name + (" *" if dirty else ""))


# ---------------------------------------------------------------------------
# BlockBuilderDock  — standalone single-file dock (no manager needed)
# ---------------------------------------------------------------------------

class BlockBuilderDock(QDockWidget):
    """
    Wraps a single BlockEditorWidget as a self-contained dock.
    Use BlockBuilderManager for the multi-file tabbed workflow.
    """
    codeChanged = pyqtSignal(str)
    def __init__(self, file_path: str | Path, parent=None):
        super().__init__("Block Builder", parent)
        self.setStyleSheet(_DOCK_SS)
        self.setMinimumWidth(420)

        self._path   = Path(file_path)
        self._editor = BlockEditorWidget(self._path, parent=self)
        self._editor.saveRequested.connect(self._save)
        self._editor.saveAsRequested.connect(self._save_as)
        self._editor.codeChanged.connect(self.codeChanged.emit)
        self.setWidget(self._editor)

    def load_file(self, path: str | Path):
        self._path = Path(path)
        self._editor.path = self._path
        self._editor._load()

    def generated_code(self) -> str:
        return self._editor.generated_code()

    def _save(self):
        try:
            self._path.write_text(self._editor.generated_code(), encoding="utf-8")
            self._editor.mark_clean()
        except OSError as e:
            QMessageBox.critical(self, "Save failed", str(e))

    def _save_as(self):
        p, _ = QFileDialog.getSaveFileName(
            self, "Save As", str(self._path), "Python files (*.py);;All files (*)"
        )
        if p:
            self._path = Path(p)
            self._editor.path = self._path
            self._save()




# ---------------------------------------------------------------------------
# Demo  (python block_builder_dock.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys, tempfile, os

    app = QApplication(sys.argv)

    tmp_files = []
    for name, content in [
        ("hello.py",  "def hello():\n    print('Hello, world!')\n\nhello()\n"),
        ("utils.py",  "import os\nimport sys\n\ndef get_cwd():\n    return os.getcwd()\n"),
        ("models.py", "class User:\n    def __init__(self, name):\n        self.name = name\n"),
    ]:
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=f"_{name}", delete=False, encoding="utf-8"
        )
        f.write(content)
        f.close()
        tmp_files.append(f.name)

    win = QMainWindow()
    win.setWindowTitle("Block Builder Demo")
    win.resize(1200, 750)
    win.setStyleSheet(f"QMainWindow {{ background:{_D['bg']}; }}")

    manager = BlockBuilderManager(parent=win)
    win.addDockWidget(Qt.RightDockWidgetArea, manager)

    for fp in tmp_files:
        manager.open_file(fp)

    central = QLabel(
        "<center>"
        f"<h2 style='color:{_D['accent']};'>Block Builder Manager</h2>"
        f"<p style='color:{_D['dim']};'>Right-click a tab → ⧉ Pop out to own dock</p>"
        f"<p style='color:{_D['dim']};'>Drag tabs to reorder &nbsp;|&nbsp;"
        " Click ✕ to close &nbsp;|&nbsp; Edit blocks on the right</p>"
        "</center>"
    )
    central.setStyleSheet(f"background:{_D['bg']};")
    central.setAlignment(Qt.AlignCenter)
    win.setCentralWidget(central)
    win.show()

    app.aboutToQuit.connect(
        lambda: [os.unlink(f) for f in tmp_files if os.path.exists(f)]
    )
    sys.exit(app.exec_())