"""
editor_widget.py
----------------
NodeEditorWidget – the complete editor UI as a single QWidget.

Contains:
  • Top toolbar  (function name field, Save, Open, Export C++,
                  Undo, Redo, Copy, Paste, Delete, Frame, Reload Nodes)
  • NodeView     (canvas)

This widget is embedded inside NodeEditorDock (dock.py).
It can also be shown standalone via NodeEditor.py.
"""

import json
import os

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFileDialog, QMessageBox,
    QDialog, QTextEdit, QApplication
)
from PyQt5.QtCore import Qt

from Core.NodeEditorContent.Core.scene          import NodeScene
from Core.NodeEditorContent.Core.view           import NodeView
from Core.NodeEditorContent.Core.nodes_builtin  import OutputNode
from Core.NodeEditorContent.Core.cpp_export     import generate_cpp
from Core.NodeEditorContent.Core.node_loader    import load_nodes
import Core.NodeEditorContent.Core.node_loader  as node_loader

_DARK = ("QWidget{background:#0d1117;color:#d4e0f0}"
         "QPushButton{background:#1c2433;color:#d4e0f0;"
         "border:1px solid #2a3a5c;border-radius:3px;padding:2px 10px}"
         "QPushButton:hover{background:#2a3a5c;color:#ffffff}"
         "QLineEdit{background:#0d1117;color:#d4e0f0;"
         "border:1px solid #2a3a5c;border-radius:3px;padding:2px 6px}"
         "QLabel{color:#5a7090;font-size:9px}"
         "QTextEdit{background:#060a10;color:#a0d4a0;"
         "border:1px solid #2a3a5c;"
         "font-family:Consolas,monospace;font-size:11px}")

_BTN_STYLE = ("QPushButton{background:#1c2433;color:#d4e0f0;"
              "border:1px solid #2a3a5c;border-radius:3px;"
              "padding:2px 10px;font-size:11px}"
              "QPushButton:hover{background:#2a3a5c;color:#ffffff}")


class NodeEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(_DARK)

        self._file = ""

        # ── Scene + View ──────────────────────────────────────
        self.scene = NodeScene()
        self.view  = NodeView(self.scene)

        # seed with one Output node
        self._seed_output()

        # ── Toolbar ───────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        toolbar.setContentsMargins(4, 4, 4, 4)

        def btn(label, slot, tip=""):
            b = QPushButton(label)
            b.setFixedHeight(24)
            b.setToolTip(tip)
            b.setStyleSheet(_BTN_STYLE)
            b.clicked.connect(slot)
            toolbar.addWidget(b)
            return b

        # function name
        fn_lbl = QLabel("Function:")
        fn_lbl.setStyleSheet("color:#8899bb;font-size:10px")
        toolbar.addWidget(fn_lbl)

        self._func_name = QLineEdit("my_function")
        self._func_name.setFixedWidth(140)
        self._func_name.setFixedHeight(24)
        self._func_name.setToolTip("C++ function name")
        toolbar.addWidget(self._func_name)

        toolbar.addSpacing(8)

        btn("Save",      self.save,        "Save script (Ctrl+S)")
        btn("Open",      self.open_file,   "Open script file")
        btn("Export C++", self.export_cpp,  "Generate C++ function")
        toolbar.addSpacing(4)
        btn("↩ Undo",   self.undo,   "(Ctrl+Z)")
        btn("↪ Redo",   self.redo,   "(Ctrl+Y)")
        btn("Copy Node(s)",   self.copy,   "Copy Selected Nodes (Ctrl+C)")
        btn("Paste Node(s)",  self.paste,  "Paste the copied Nodes (Ctrl+V)")
        btn("Delete", self.delete_sel, "Delete selected")
        toolbar.addSpacing(4)
        btn("Focus",  self.frame_all,  "F key")
        btn("Reload Nodes", self.reload_nodes, "Reload Nodes/ folder")

        toolbar.addStretch()
        hint = QLabel("Middle: pan  •  Scroll: zoom  •  Right-click: add node  •  F: frame all")
        hint.setStyleSheet("color:#2a3a5c;font-size:9px")
        toolbar.addWidget(hint)

        # ── Root layout ───────────────────────────────────────
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tb_widget = QWidget()
        tb_widget.setLayout(toolbar)
        tb_widget.setStyleSheet("QWidget{background:#0d1117;"
                                "border-bottom:1px solid #1c2433}")
        tb_widget.setFixedHeight(32)
        root.addWidget(tb_widget)
        root.addWidget(self.view)

    # ── seed ─────────────────────────────────────────────────
    def _seed_output(self):
        from PyQt5.QtCore import QPointF
        out = OutputNode(self._uid())
        self.scene.add_node(out, QPointF(500, 200))

    def _uid(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]

    # ── toolbar actions ───────────────────────────────────────
    def save(self):
        if not self._file:
            self._file, _ = QFileDialog.getSaveFileName(
                self, "Save Blueprint", "", "Script Files (*.script)")
        if not self._file:
            return
        data = self.scene.to_dict()
        data["meta"] = {"func_name": self._func_name.text()}
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save_as(self):
        self._file = ""
        self.save()

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Blueprint", "", "Script Files (*.script)")
        if path:
            self.load_from(path)

    def load_from(self, path: str):
        """
        Public API — called by Open_Script() in dock.py.
        If path does not exist, shows a warning and opens empty.
        """
        if not os.path.isfile(path):
            QMessageBox.warning(
                self, "File Not Found",
                f"The file was not found:\n{path}\n\nOpening an empty graph.")
            self._open_empty()
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as ex:
            QMessageBox.critical(
                self, "Load Error", f"Could not read file:\n{ex}")
            self._open_empty()
            return

        # restore function name
        meta = data.get("meta", {})
        self._func_name.setText(meta.get("func_name", "my_function"))

        self.scene.from_dict(data)
        self._file = path

        # if no Output node survived, add one
        from Core.NodeEditorContent.Core.nodes_builtin import OutputNode as ON
        if not any(isinstance(n, ON) for n in self.scene.nodes):
            self._seed_output()

        self.view._frame_all()

    def _open_empty(self):
        self.scene.from_dict({"nodes": [], "wires": []})
        self._file = ""
        self._func_name.setText("my_function")
        self._seed_output()

    def export_cpp(self):
        code = generate_cpp(self.scene, self._func_name.text().strip() or "my_function")

        dlg = QDialog(self)
        dlg.setWindowTitle("C++ Export")
        dlg.resize(700, 480)
        dlg.setStyleSheet(_DARK)
        vl  = QVBoxLayout(dlg)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setPlainText(code)
        vl.addWidget(txt)

        row = QHBoxLayout()

        def _save():
            fname = self._func_name.text().strip() or "output"
            p, _  = QFileDialog.getSaveFileName(
                dlg, "Save C++", f"{fname}.cpp", "C++ Files (*.cpp)")
            if p:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(code)
                QMessageBox.information(dlg, "Saved", f"Saved to:\n{p}")

        sb = QPushButton("💾 Save .cpp"); sb.setStyleSheet(_BTN_STYLE)
        sb.clicked.connect(_save)
        row.addWidget(sb)

        cb = QPushButton("📋 Copy"); cb.setStyleSheet(_BTN_STYLE)
        cb.clicked.connect(lambda: QApplication.clipboard().setText(code))
        row.addWidget(cb)

        row.addStretch()
        xb = QPushButton("Close"); xb.setStyleSheet(_BTN_STYLE)
        xb.clicked.connect(dlg.accept)
        row.addWidget(xb)

        vl.addLayout(row)
        dlg.exec_()

    def undo(self):       self.scene.undo_stack.undo()
    def redo(self):       self.scene.undo_stack.redo()
    def copy(self):       self.scene.copy_selected()
    def paste(self):      self.scene.paste()
    def delete_sel(self): self.scene.delete_selected()

    def frame_all(self):
        r = self.scene.itemsBoundingRect()
        if not r.isNull():
            self.view.fitInView(r.adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)

    def reload_nodes(self):
        load_nodes()
        n = len(node_loader.REGISTRY)
        QMessageBox.information(self, "Nodes Reloaded",
                                f"{n} node(s) loaded from Nodes/ folder.")

    # ── function name property ────────────────────────────────
    @property
    def func_name(self) -> str:
        return self._func_name.text().strip()

    @func_name.setter
    def func_name(self, value: str):
        self._func_name.setText(value)
