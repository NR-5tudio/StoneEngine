"""
node_base.py
------------
BaseNode – the parent class for every node in the editor.

All custom .node files subclass this.  The class handles:
  • pin management (add_in / add_out / remove_pin)
  • layout   (auto-sizes width from pin label + widget widths)
  • painting (dark UE-style header + body)
  • right-click context menu (add / remove pins, rename, delete)
  • serialisation (to_dict / from_dict)
  • C++ expression generation (to_cpp_expr – override in subclasses)
"""

from PyQt5.QtWidgets import (
    QGraphicsItem, QMenu, QDialog, QFormLayout,
    QLineEdit, QComboBox, QDialogButtonBox, QInputDialog
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui  import (
    QPen, QBrush, QColor, QPainter,
    QLinearGradient, QFont, QCursor
)

from Core.NodeEditorContent.Core.pin import Pin, pin_color

NODE_W   = 200
HDR_H    = 26
BODY_PAD = 8
PIN_STEP = 22
PIN_START_OFFSET = 14   # below header

TYPE_LIST = ['float', 'int', 'bool', 'string']

_DARK = ("QDialog,QWidget{background:#0d1117;color:#d4e0f0}"
         "QPushButton{background:#1c2433;color:#d4e0f0;"
         "border:1px solid #2a3a5c;border-radius:3px;padding:4px 10px}"
         "QPushButton:hover{background:#2a3a5c}"
         "QLineEdit,QComboBox{background:#0d1117;color:#d4e0f0;"
         "border:1px solid #2a3a5c;border-radius:3px;padding:3px 6px}"
         "QLabel{color:#d4e0f0}")

C_NODE_BODY = QColor("#232d3f")
C_SEL       = QColor("#00b4ff")
C_TEXT_HDR  = QColor("#ffffff")
C_TEXT_SUB  = QColor("#8899bb")


def _ask_pin(parent, title="Pin"):
    dlg = QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setStyleSheet(_DARK)
    f  = QFormLayout(dlg)
    ne = QLineEdit("value")
    tb = QComboBox()
    tb.addItems(TYPE_LIST)
    f.addRow("Name:", ne)
    f.addRow("Type:", tb)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    f.addRow(bb)
    if dlg.exec_() == QDialog.Accepted:
        return ne.text().strip() or "value", tb.currentText()
    return None, None


class BaseNode(QGraphicsItem):
    """
    Subclass this to make a custom node.

    Required overrides
    ------------------
    META : dict  – {"title": str, "category": str}
                   category can use "/" for nesting: "Math/Trig"

    Optional overrides
    ------------------
    to_cpp_expr(out_pin_index, graph_context) -> str
        Return the C++ expression that evaluates this node's output.
        graph_context is passed down from the exporter.
    """

    META          = {"title": "Node", "category": "General"}
    HEADER_COLOR  = QColor("#1a3a5c")
    SUBTITLE      = ""
    PERMANENT     = False   # True → cannot be deleted

    def __init__(self, node_id: str):
        super().__init__()
        self.node_id   = node_id
        self.in_pins  = []   # type: list[Pin]
        self.out_pins = []   # type: list[Pin]
        self.width    = NODE_W
        self.height   = HDR_H + 20

        self.setFlag(QGraphicsItem.ItemIsMovable,             True)
        self.setFlag(QGraphicsItem.ItemIsSelectable,          True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges,  True)
        self.setZValue(5)
        self.setCursor(QCursor(Qt.SizeAllCursor))

    # ── title shorthand ───────────────────────────────────────
    @property
    def title(self) -> str:
        return self.META.get("title", "Node")

    # ── pin management ────────────────────────────────────────
    def add_in(self, name: str, ptype: str = 'float') -> Pin:
        p = Pin(self, name, ptype, 'in', len(self.in_pins))
        self.in_pins.append(p)
        self._layout()
        return p

    def add_out(self, name: str, ptype: str = 'float') -> Pin:
        p = Pin(self, name, ptype, 'out', len(self.out_pins))
        self.out_pins.append(p)
        self._layout()
        return p

    def remove_pin(self, pin: Pin):
        s = self.scene()
        if s:
            for w in list(pin.wires):
                s.remove_wire(w)
        lst = self.in_pins if pin in self.in_pins else self.out_pins
        if pin in lst:
            lst.remove(pin)
        if pin.scene():
            pin.scene().removeItem(pin)
        self._layout()

    # ── layout ───────────────────────────────────────────────
    def _layout(self):
        start = HDR_H + PIN_START_OFFSET
        rows  = max(len(self.in_pins), len(self.out_pins), 1)
        self.height = start + rows * PIN_STEP + BODY_PAD

        # compute required width from widest pin row
        max_in  = max((p.total_width() for p in self.in_pins),  default=0)
        max_out = max((p.total_width() for p in self.out_pins), default=0)
        self.width = max(NODE_W, int(max_in + max_out) + 40)

        for i, p in enumerate(self.in_pins):
            p.setParentItem(self)
            p.setPos(0, start + i * PIN_STEP)

        for i, p in enumerate(self.out_pins):
            p.setParentItem(self)
            p.setPos(self.width, start + i * PIN_STEP)

        self.update()
        s = self.scene()
        if s:
            s.refresh_wires()

    # ── bounding rect ────────────────────────────────────────
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height).adjusted(-3, -3, 3, 3)

    # ── paint ────────────────────────────────────────────────
    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        r  = QRectF(0, 0, self.width, self.height)
        hr = QRectF(0, 0, self.width, HDR_H)

        # shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(r.adjusted(3, 3, 3, 3), 7, 7)

        # body
        body = C_NODE_BODY.lighter(115) if self.isSelected() else C_NODE_BODY
        painter.setBrush(QBrush(body))
        painter.setPen(QPen(C_SEL, 2) if self.isSelected()
                       else QPen(QColor("#0a1220"), 1))
        painter.drawRoundedRect(r, 7, 7)

        # header gradient
        hc = self.HEADER_COLOR
        g  = QLinearGradient(0, 0, 0, HDR_H)
        g.setColorAt(0, hc.lighter(130))
        g.setColorAt(1, hc)
        painter.setBrush(QBrush(g))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(hr, 7, 7)
        painter.drawRect(QRectF(0, HDR_H - 8, self.width, 8))

        # divider
        painter.setPen(QPen(hc.darker(200), 1))
        painter.drawLine(QPointF(0, HDR_H), QPointF(self.width, HDR_H))

        # title
        painter.setPen(QPen(C_TEXT_HDR))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(hr.adjusted(10, 0, -6, 0),
                         Qt.AlignVCenter | Qt.AlignLeft, self.title)

        # subtitle / lock
        if self.SUBTITLE:
            painter.setPen(QPen(C_TEXT_SUB))
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(hr.adjusted(0, 0, -6, 0),
                             Qt.AlignVCenter | Qt.AlignRight, self.SUBTITLE)
        if self.PERMANENT:
            painter.setPen(QPen(QColor("#aabbff")))
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(hr.adjusted(0, 0, -6, 0),
                             Qt.AlignVCenter | Qt.AlignRight, "")

    # ── item change ──────────────────────────────────────────
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            s = self.scene()
            if s and hasattr(s, 'refresh_wires'):
                s.refresh_wires()
        return super().itemChange(change, value)

    # ── context menu ─────────────────────────────────────────
    def contextMenuEvent(self, e):
        m = QMenu()
        m.setStyleSheet(_DARK)

        add_in_act  = m.addAction("+ Add Input Pin")
        add_out_act = m.addAction("+ Add Output Pin")
        m.addSeparator()

        # removable pins
        all_pins = self.in_pins + self.out_pins
        rm_menu  = None
        if all_pins:
            rm_menu = m.addMenu("Remove Pin")
            rm_menu.setStyleSheet(_DARK)
            for p in all_pins:
                arrow = '→' if p.direction == 'in' else '←'
                act   = rm_menu.addAction(f"{arrow} {p.name} [{p.pin_type}]")
                act.setData(p)

        rename_act = None
        del_act    = None
        if not self.PERMANENT:
            m.addSeparator()
            rename_act = m.addAction("Rename")
            del_act    = m.addAction("Delete Node")

        chosen = m.exec_(e.screenPos())
        if chosen is None:
            return
        if chosen == add_in_act:
            n, t = _ask_pin(None, "Add Input Pin")
            if n:
                self.add_in(n, t)
        elif chosen == add_out_act:
            n, t = _ask_pin(None, "Add Output Pin")
            if n:
                self.add_out(n, t)
        elif chosen == rename_act:
            text, ok = QInputDialog.getText(None, "Rename", "New title:", text=self.title)
            if ok and text.strip():
                self.META = dict(self.META)   # copy so we don't mutate class-level dict
                self.META['title'] = text.strip()
                self.update()
        elif chosen == del_act:
            s = self.scene()
            if s:
                s.remove_node(self)
        elif chosen and isinstance(chosen.data(), Pin):
            self.remove_pin(chosen.data())

    # ── C++ expression (override in subclasses) ───────────────
    def to_cpp_expr(self, out_pin_index: int, ctx: dict) -> str:
        """
        Return a C++ expression string for the given output pin.
        ctx['expr'](node_id, in_pin_index) → C++ expression for that input.
        Default: return the output pin name as an identifier.
        """
        if out_pin_index < len(self.out_pins):
            return self.out_pins[out_pin_index].name
        return "0"

    # ── serialise ────────────────────────────────────────────
    def to_dict(self) -> dict:
        pos = self.scenePos()
        return {
            "id"       : self.node_id,
            "class_key": self.__class__.__name__,
            "meta"     : self.META,
            "x"        : pos.x(),
            "y"        : pos.y(),
            "in_pins"  : [p.to_dict() for p in self.in_pins],
            "out_pins" : [p.to_dict() for p in self.out_pins],
        }