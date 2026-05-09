"""
view.py  –  NodeView
Right-click menu includes:
  • Built-in Math nodes
  • Custom blank node
  • Input Node  (for script authors)
  • Project >   (scans workspace path for .script files, arbitrarily nested)
  • Nodes >     (plugin tree from Nodes/ folder)
"""

import os

from PyQt5.QtWidgets import QGraphicsView, QMenu, QInputDialog
from PyQt5.QtCore    import Qt, QPointF
from PyQt5.QtGui     import QPainter, QPen, QBrush, QColor

from Core.NodeEditorContent.Core.scene import NodeScene

C_BG         = QColor("#0d1117")
C_GRID_MINOR = QColor("#141922")
C_GRID_MAJOR = QColor("#1c2433")

_DARK  = ("QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
          "QMenu::item:selected{background:#1a2a5c}"
          "QMenu::item{padding:4px 18px}"
          "QMenu::separator{height:1px;background:#1c2433;margin:3px 0}")
_MSUB  = ("QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
          "QMenu::item:selected{background:#1a2a5c}")


class NodeView(QGraphicsView):
    def __init__(self, scene: NodeScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(C_BG))
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self._panning       = False
        self._pan_start     = None
        self._move_started  = False
        self._workspace     = ""   # set via update_path()

    # ── workspace path ────────────────────────────────────────
    def set_workspace(self, path: str):
        self._workspace = path

    # ── grid ─────────────────────────────────────────────────
    def drawBackground(self, painter: QPainter, rect):
        super().drawBackground(painter, rect)
        for step, color in ((20, C_GRID_MINOR), (100, C_GRID_MAJOR)):
            painter.setPen(QPen(color, 1))
            lx = int(rect.left())  - int(rect.left())  % step
            ty = int(rect.top())   - int(rect.top())   % step
            for x in range(lx, int(rect.right()),  step):
                painter.drawLine(x, int(rect.top()),    x, int(rect.bottom()))
            for y in range(ty, int(rect.bottom()), step):
                painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    # ── zoom / pan ────────────────────────────────────────────
    def wheelEvent(self, e):
        f = 1.12 if e.angleDelta().y() > 0 else 1 / 1.12
        self.scale(f, f)

    def mousePressEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self._panning = True; self._pan_start = e.pos()
            self.setCursor(Qt.ClosedHandCursor); return
        sc = self.scene()
        if e.button() == Qt.LeftButton and isinstance(sc, NodeScene):
            selected = [n for n in sc.nodes if n.isSelected()]
            if selected:
                sc.record_pre_move(selected)
                self._move_started = True
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._panning:
            d = e.pos() - self._pan_start; self._pan_start = e.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - d.y())
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self._panning = False; self.setCursor(Qt.ArrowCursor); return
        super().mouseReleaseEvent(e)
        if e.button() == Qt.LeftButton and self._move_started:
            sc = self.scene()
            if isinstance(sc, NodeScene):
                sc.commit_moves()
            self._move_started = False

    # ── keyboard ──────────────────────────────────────────────
    def keyPressEvent(self, e):
        sc  = self.scene()
        mod = e.modifiers()
        key = e.key()
        if not isinstance(sc, NodeScene):
            super().keyPressEvent(e); return

        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            sc.delete_selected()
        elif key == Qt.Key_Z and mod & Qt.ControlModifier:
            sc.undo_stack.redo() if mod & Qt.ShiftModifier else sc.undo_stack.undo()
        elif key == Qt.Key_Y and mod & Qt.ControlModifier:
            sc.undo_stack.redo()
        elif key == Qt.Key_C and mod & Qt.ControlModifier:
            sc.copy_selected()
        elif key == Qt.Key_V and mod & Qt.ControlModifier:
            sc.paste()
        elif key == Qt.Key_A and mod & Qt.ControlModifier:
            for item in sc.items(): item.setSelected(True)
        elif key == Qt.Key_F:
            self._frame_all()
        else:
            super().keyPressEvent(e)

    def _frame_all(self):
        r = self.scene().itemsBoundingRect()
        if not r.isNull():
            self.fitInView(r.adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)

    # ── right-click menu ──────────────────────────────────────
    def contextMenuEvent(self, e):
        sp  = self.mapToScene(e.pos())
        hit = self.itemAt(e.pos())
        if hit is not None:
            super().contextMenuEvent(e); return

        menu = QMenu(self)
        menu.setStyleSheet(_DARK)

        # Math
        math_m = menu.addMenu("∑  Math")
        math_m.setStyleSheet(_MSUB)
        for op in ["+", "-", "*", "/", "%"]:
            math_m.addAction(op, lambda o=op: self._add_math(o, sp))

        # Custom blank
        menu.addAction("◻  Custom Node", lambda: self._add_custom(sp))

        # Input Node (for script authors defining inputs)
        menu.addAction("⬡  Input Node",  lambda: self._add_input_node(sp))

        # Plugin nodes tree
        from Core.NodeEditorContent.Core.node_loader import TREE
        if TREE:
            menu.addSeparator()
            plug_m = menu.addMenu("🔌  Nodes")
            plug_m.setStyleSheet(_MSUB)
            self._build_plugin_tree(plug_m, TREE, sp)

        # Project scripts tree
        menu.addSeparator()
        proj_m = menu.addMenu("📁  Project")
        proj_m.setStyleSheet(_MSUB)
        self._build_project_tree(proj_m, sp)

        menu.exec_(e.globalPos())

    # ── project tree ──────────────────────────────────────────
    def _build_project_tree(self, parent_menu: QMenu, sp: QPointF):
        root = self._workspace
        if not root or not os.path.isdir(root):
            act = parent_menu.addAction("(no workspace set)")
            act.setEnabled(False)
            return

        self._scan_dir_for_scripts(parent_menu, root, root, sp)

    def _scan_dir_for_scripts(self, menu: QMenu, dirpath: str,
                               root: str, sp: QPointF):
        try:
            entries = sorted(os.scandir(dirpath), key=lambda e: (not e.is_dir(), e.name))
        except PermissionError:
            return

        for entry in entries:
            if entry.name.startswith('.') or entry.name.startswith('_'):
                continue
            if entry.is_dir():
                sub = menu.addMenu(f"📁 {entry.name}")
                sub.setStyleSheet(
                    "QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
                    "QMenu::item:selected{background:#1a2a5c}")
                self._scan_dir_for_scripts(sub, entry.path, root, sp)
            elif entry.name.endswith(".script"):
                label = entry.name[:-7]   # strip .script
                path  = entry.path
                menu.addAction(f"📄 {label}",
                               lambda p=path: self._add_script_node(p, sp))

    # ── plugin node tree ──────────────────────────────────────
    def _build_plugin_tree(self, parent_menu: QMenu, tree: dict, sp: QPointF):
        folders = {k: v for k, v in tree.items() if isinstance(v, dict)}
        leaves  = {k: v for k, v in tree.items() if not isinstance(v, dict)}
        for name in sorted(folders):
            sub = parent_menu.addMenu(f"📁  {name}")
            sub.setStyleSheet(
                "QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
                "QMenu::item:selected{background:#1a2a5c}")
            self._build_plugin_tree(sub, folders[name], sp)
        for ck in sorted(leaves):
            cls   = leaves[ck]
            title = getattr(cls, 'META', {}).get("title", ck)
            parent_menu.addAction(title, lambda k=ck: self._add_plugin(k, sp))

    # ── node factories ────────────────────────────────────────
    def _sc(self) -> NodeScene:
        return self.scene()

    def _uid(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]

    def _add_math(self, op: str, sp: QPointF):
        from Core.NodeEditorContent.Core.nodes_builtin import MathNode
        from Core.NodeEditorContent.Core.undo_redo    import AddNodeCmd
        node = MathNode(self._uid(), op)
        self._sc().undo_stack.push(AddNodeCmd(self._sc(), node, sp))

    def _add_custom(self, sp: QPointF):
        from Core.NodeEditorContent.Core.nodes_builtin import CustomNode
        from Core.NodeEditorContent.Core.undo_redo    import AddNodeCmd
        name, ok = QInputDialog.getText(self.window(), "Custom Node", "Node name:", text="MyNode")
        if not ok or not name.strip(): return
        node = CustomNode(self._uid(), name.strip())
        self._sc().undo_stack.push(AddNodeCmd(self._sc(), node, sp))

    def _add_input_node(self, sp: QPointF):
        from Core.NodeEditorContent.Core.nodes_script import InputNode
        from Core.NodeEditorContent.Core.undo_redo   import AddNodeCmd
        node = InputNode(self._uid())
        self._sc().undo_stack.push(AddNodeCmd(self._sc(), node, sp))

    def _add_script_node(self, path: str, sp: QPointF):
        from Core.NodeEditorContent.Core.nodes_script import ScriptNode
        from Core.NodeEditorContent.Core.undo_redo   import AddNodeCmd
        node = ScriptNode(self._uid(), path)
        self._sc().undo_stack.push(AddNodeCmd(self._sc(), node, sp))

    def _add_plugin(self, class_key: str, sp: QPointF):
        from Core.NodeEditorContent.Core.node_loader import REGISTRY
        from Core.NodeEditorContent.Core.undo_redo   import AddNodeCmd
        cls = REGISTRY.get(class_key)
        if cls is None: return
        node = cls(self._uid())
        self._sc().undo_stack.push(AddNodeCmd(self._sc(), node, sp))