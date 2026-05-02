"""
view.py
-------
NodeView – QGraphicsView subclass.

Handles:
  • Grid background (minor + major lines)
  • Middle-mouse pan, scroll-wheel zoom
  • Right-click context menu (built-ins + plugin tree mirroring Nodes/ structure)
  • Keyboard: Delete, Ctrl+Z/Y, Ctrl+C/V, F (frame all)
  • Mouse-press position tracking → sent to scene for MoveNodeCmd
"""

from PyQt5.QtWidgets import (
    QGraphicsView, QMenu, QInputDialog, QAction
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui  import QPainter, QPen, QBrush, QColor, QKeySequence

from Core.NodeEditorContent.Core.scene import NodeScene

C_BG         = QColor("#0d1117")
C_GRID_MINOR = QColor("#141922")
C_GRID_MAJOR = QColor("#1c2433")

_DARK = ("QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
         "QMenu::item:selected{background:#1a2a5c}"
         "QMenu::item{padding:4px 18px}"
         "QMenu::separator{height:1px;background:#1c2433;margin:3px 0}")


class NodeView(QGraphicsView):
    def __init__(self, scene: NodeScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(C_BG))
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)

        self._panning   = False
        self._pan_start = None
        self._move_started = False   # track if a node drag began

    # ── grid ────────────────────────────────────────────────
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

    # ── zoom ────────────────────────────────────────────────
    def wheelEvent(self, e):
        factor = 1.12 if e.angleDelta().y() > 0 else 1 / 1.12
        self.scale(factor, factor)

    # ── pan ─────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self._panning   = True
            self._pan_start = e.pos()
            self.setCursor(Qt.ClosedHandCursor)
            e.accept()
            return

        # record positions before a potential drag
        sc = self.scene()
        if e.button() == Qt.LeftButton and isinstance(sc, NodeScene):
            selected = [n for n in sc.nodes if n.isSelected()]
            if selected:
                sc.record_pre_move(selected)
                self._move_started = True

        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._panning:
            d = e.pos() - self._pan_start
            self._pan_start = e.pos()
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - d.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - d.y())
            e.accept()
            return
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.ArrowCursor)
            e.accept()
            return

        super().mouseReleaseEvent(e)

        if e.button() == Qt.LeftButton and self._move_started:
            sc = self.scene()
            if isinstance(sc, NodeScene):
                sc.commit_moves()
            self._move_started = False

    # ── keyboard ────────────────────────────────────────────
    def keyPressEvent(self, e):
        sc = self.scene()
        if not isinstance(sc, NodeScene):
            super().keyPressEvent(e)
            return

        mod = e.modifiers()
        key = e.key()

        if key == Qt.Key_Delete or key == Qt.Key_Backspace:
            sc.delete_selected()

        elif key == Qt.Key_Z and mod & Qt.ControlModifier:
            if mod & Qt.ShiftModifier:
                sc.undo_stack.redo()
            else:
                sc.undo_stack.undo()

        elif key == Qt.Key_Y and mod & Qt.ControlModifier:
            sc.undo_stack.redo()

        elif key == Qt.Key_C and mod & Qt.ControlModifier:
            sc.copy_selected()

        elif key == Qt.Key_V and mod & Qt.ControlModifier:
            sc.paste()

        elif key == Qt.Key_A and mod & Qt.ControlModifier:
            for item in sc.items():
                item.setSelected(True)

        elif key == Qt.Key_F:
            self._frame_all()

        else:
            super().keyPressEvent(e)

    def _frame_all(self):
        r = self.scene().itemsBoundingRect()
        if not r.isNull():
            self.fitInView(r.adjusted(-60, -60, 60, 60), Qt.KeepAspectRatio)

    # ── right-click context menu ──────────────────────────────
    def contextMenuEvent(self, e):
        sp = self.mapToScene(e.pos())

        # only show if we right-clicked on empty canvas
        hit = self.itemAt(e.pos())
        if hit is not None:
            super().contextMenuEvent(e)
            return

        menu = QMenu(self)
        menu.setStyleSheet(_DARK)
        menu.setTitle("Add Node")

        # ── Built-in math ──────────────────────────────
        math_menu = menu.addMenu("∑  Math")
        math_menu.setStyleSheet(_DARK)
        for op in ["+", "-", "*", "/", "%"]:
            _op = op
            math_menu.addAction(op, lambda o=_op: self._add_math(o, sp))

        # ── Custom blank node ──────────────────────────
        menu.addAction("◻  Custom Node", lambda: self._add_custom(sp))

        # ── Plugin nodes (from Nodes/ folder) ──────────
        from Core.NodeEditorContent.Core.node_loader import TREE
        if TREE:
            menu.addSeparator()
            plug_menu = menu.addMenu("🔌  Nodes")
            plug_menu.setStyleSheet(_DARK)
            self._build_tree_menu(plug_menu, TREE, sp)

        menu.exec_(e.globalPos())

    def _build_tree_menu(self, parent_menu: QMenu, tree: dict, sp: QPointF):
        """Recursively build the folder tree into QMenu entries."""
        from Core.NodeEditorContent.Core.node_loader import REGISTRY

        # separate sub-folders from leaf classes
        folders = {k: v for k, v in tree.items() if isinstance(v, dict)}
        leaves  = {k: v for k, v in tree.items() if not isinstance(v, dict)}

        for folder_name in sorted(folders):
            sub = parent_menu.addMenu(f"📁  {folder_name}")
            sub.setStyleSheet(
                "QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
                "QMenu::item:selected{background:#1a2a5c}"
            )
            self._build_tree_menu(sub, folders[folder_name], sp)

        for class_key in sorted(leaves):
            cls   = leaves[class_key]
            title = getattr(cls, 'META', {}).get("title", class_key)
            _ck   = class_key
            parent_menu.addAction(title, lambda k=_ck: self._add_plugin(k, sp))

    # ── node factories ────────────────────────────────────────
    def _scene(self) -> NodeScene:
        return self.scene()

    def _add_math(self, op: str, sp: QPointF):
        from Core.NodeEditorContent.Core.nodes_builtin import MathNode
        from Core.NodeEditorContent.Core.undo_redo import AddNodeCmd
        sc   = self._scene()
        node = MathNode(sc._new_id() if hasattr(sc, '_new_id') else self._uid(), op)
        cmd  = AddNodeCmd(sc, node, sp)
        sc.undo_stack.push(cmd)

    def _add_custom(self, sp: QPointF):
        from Core.NodeEditorContent.Core.nodes_builtin import CustomNode
        from Core.NodeEditorContent.Core.undo_redo import AddNodeCmd
        name, ok = QInputDialog.getText(self.window(), "Custom Node", "Node name:", text="MyNode")
        if not ok or not name.strip():
            return
        sc   = self._scene()
        node = CustomNode(self._uid(), name.strip())
        cmd  = AddNodeCmd(sc, node, sp)
        sc.undo_stack.push(cmd)

    def _add_plugin(self, class_key: str, sp: QPointF):
        from Core.NodeEditorContent.Core.node_loader import REGISTRY
        from Core.NodeEditorContent.Core.undo_redo import AddNodeCmd
        cls = REGISTRY.get(class_key)
        if cls is None:
            return
        sc   = self._scene()
        node = cls(self._uid())
        cmd  = AddNodeCmd(sc, node, sp)
        sc.undo_stack.push(cmd)

    def _uid(self) -> str:
        import uuid
        return str(uuid.uuid4())[:8]
