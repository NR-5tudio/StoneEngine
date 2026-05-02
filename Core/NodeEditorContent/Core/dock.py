"""
dock.py
-------
NodeEditorDock – a QDockWidget that wraps NodeEditorWidget.

By default the dock is HIDDEN.  Nothing appears until Open_Script() is called.

Public API
----------
    dock = NodeEditorDock(parent=main_window)
    main_window.addDockWidget(Qt.RightDockWidgetArea, dock)

    # open a file (shows the dock)
    dock.Open_Script("path/to/file.script")

    # open empty (shows the dock)
    dock.Open_Script("")

    # can be called from game engine browser when user double-clicks a .script file
    dock.Open_Script(path)

The dock is:
  • Floatable  (can be torn off into its own window)
  • Movable    (drag to any dock area)
  • Closable   (X button hides it; does NOT destroy it)
  • Resizable  (normal window resize when floating)

When called with a path that does not exist the editor opens empty and
shows a QMessageBox warning — that warning is handled inside
NodeEditorWidget.load_from().
"""

import os

from PyQt5.QtWidgets import QDockWidget, QMessageBox
from PyQt5.QtCore    import Qt

from Core.NodeEditorContent.Core.editor_widget import NodeEditorWidget
from Core.NodeEditorContent.Core.node_loader   import load_nodes


class NodeEditorDock(QDockWidget):
    """
    Floating/dockable Node Editor panel.

    Parameters
    ----------
    parent : QMainWindow  (the host application's main window)
    """

    def __init__(self, parent=None):
        super().__init__("Blueprint Node Editor", parent)

        # dock behaviour flags
        self.setFeatures(
            QDockWidget.DockWidgetFloatable  |
            QDockWidget.DockWidgetMovable    |
            QDockWidget.DockWidgetClosable
        )
        self.setAllowedAreas(Qt.AllDockWidgetAreas)

        # load plugins once at construction
        load_nodes()

        # build the inner widget
        self._editor = NodeEditorWidget(self)
        self.setWidget(self._editor)

        # start hidden — nothing appears until Open_Script() is called
        self.hide()

    # ── public API ────────────────────────────────────────────

    def Open_Script(self, path: str) -> None:
        """
        Open a .script file in the dock and show it.

        Parameters
        ----------
        path : str
            Full path to a .script file.
            Pass "" or None to open an empty graph.
        """
        if path:
            self._editor.load_from(path)
            # update dock title to show filename
            self.setWindowTitle(f"Node Editor — {os.path.basename(path)}")
        else:
            self._editor._open_empty()
            self.setWindowTitle("Node Editor — (untitled)")

        self.show()
        self.raise_()

    def close_editor(self) -> None:
        """Programmatically hide the dock (same as clicking the X)."""
        self.hide()

    # ── forward save/load shortcuts ───────────────────────────

    def save(self) -> None:
        self._editor.save()

    def save_as(self) -> None:
        self._editor.save_as()

    @property
    def editor(self) -> NodeEditorWidget:
        """Direct access to the inner NodeEditorWidget if needed."""
        return self._editor

    # ── close event — hide instead of destroy ─────────────────
    def closeEvent(self, e):
        self.hide()
        e.ignore()   # don't destroy the widget
