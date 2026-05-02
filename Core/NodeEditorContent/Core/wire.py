"""
wire.py
-------
Wire        – a permanent bezier connection between two pins.
TempWire    – the dashed preview drawn while dragging a new connection.
"""

from PyQt5.QtWidgets import QGraphicsPathItem, QMenu
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QPen, QPainterPath

from Core.NodeEditorContent.Core.pin import pin_color


# ── dark menu style (shared mini-helper) ──────────────────────
_DARK = ("QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
         "QMenu::item:selected{background:#1a2a5c}")


class Wire(QGraphicsPathItem):
    def __init__(self, src, dst):
        super().__init__()
        self.src = src   # out-pin
        self.dst = dst   # in-pin
        self._set_pen(False)
        self.setZValue(1)
        self.setFlag(QGraphicsPathItem.ItemIsSelectable, True)
        self.update_path()

    def _set_pen(self, selected: bool):
        c = pin_color(self.src.pin_type)
        w = 3 if selected else 2
        lc = c.lighter(160) if selected else c
        self.setPen(QPen(lc, w, Qt.SolidLine, Qt.RoundCap))

    def update_path(self):
        p1 = self.src.scene_center()
        p2 = self.dst.scene_center()
        dx = max(abs(p2.x() - p1.x()) * 0.6, 60)
        path = QPainterPath(p1)
        path.cubicTo(p1.x() + dx, p1.y(),
                     p2.x() - dx, p2.y(),
                     p2.x(),      p2.y())
        self.setPath(path)

    def itemChange(self, change, value):
        if change == QGraphicsPathItem.ItemSelectedHasChanged:
            self._set_pen(bool(value))
        return super().itemChange(change, value)

    def contextMenuEvent(self, e):
        m = QMenu()
        m.setStyleSheet(_DARK)
        act = m.addAction("🗑  Delete Wire")
        if m.exec_(e.screenPos()) == act:
            s = self.scene()
            if s:
                s.remove_wire(self)


class TempWire(QGraphicsPathItem):
    def __init__(self, src_pin):
        super().__init__()
        self.src_pin = src_pin
        c = pin_color(src_pin.pin_type)
        self.setPen(QPen(c, 2, Qt.DashLine, Qt.RoundCap))
        self.setZValue(100)

    def update_end(self, end):
        p1 = self.src_pin.scene_center()
        dx = max(abs(end.x() - p1.x()) * 0.6, 60)
        path = QPainterPath(p1)
        path.cubicTo(p1.x() + dx, p1.y(),
                     end.x() - dx, end.y(),
                     end.x(),      end.y())
        self.setPath(path)
