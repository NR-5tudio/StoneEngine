"""
NodeEditor.py
-------------
Standalone launcher for the Blueprint Node Editor.

Run this directly to test the editor without launching the full engine:
    python NodeEditor.py
    python NodeEditor.py path/to/file.script

The editor lives inside a dock widget embedded in a minimal QMainWindow.
When integrated into the engine (main.py), import NodeEditorDock instead:

    from NodeEditorContent.Core.dock import NodeEditorDock
    dock = NodeEditorDock(parent=self)
    self.addDockWidget(Qt.RightDockWidgetArea, dock)
    dock.Open_Script("path/to/file.script")
"""

import sys
import os

# ── make sure NodeEditorContent is importable ─────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor

from Core.NodeEditorContent.Core.dock import NodeEditorDock


class _StandaloneWindow(QMainWindow):
    """
    Bare-bones host window used only when NodeEditor.py is run directly.
    In the real engine, main.py is the host and provides its own QMainWindow.
    """

    def __init__(self, open_path: str = ""):
        super().__init__()
        self.setWindowTitle("Node Editor — Standalone")
        self.resize(1400, 900)
        self.setStyleSheet("QMainWindow { background: #0d1117; }")

        # central placeholder (the dock floats over / docks into this)
        placeholder = QLabel("Node Editor is in the dock →\n"
                             "Drag it, float it, or close it with ✕")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("color: #2a3a5c; font-size: 14px;")
        self.setCentralWidget(placeholder)

        # create the dock
        self.node_dock = NodeEditorDock(parent=self)
        self.addDockWidget(Qt.RightDockWidgetArea, self.node_dock)

        # open file or empty graph
        self.node_dock.Open_Script(open_path)

    def closeEvent(self, e):
        # nothing special needed — dock is a child widget
        super().closeEvent(e)


def Open_Script(path: str = "") -> None:
    """
    Convenience function: launch the standalone window and open a script.
    Can also be called from other modules for quick testing.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")

    win = _StandaloneWindow(open_path=path)
    win.show()

    if not QApplication.instance():
        sys.exit(app.exec_())
    else:
        app.exec_()


# ── entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else ""
    Open_Script(path)
