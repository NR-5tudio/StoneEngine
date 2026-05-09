"""
input_node.py
-------------
InputNode – a special node that defines a SCRIPT INPUT (an argument).

It has NO connection pins — only three settings fields drawn inside the node:
  1. Name   (text)    – the argument name,  e.g. "X"
  2. Type   (combo)   – float | int | bool | string
  3. Number (spinbox) – sort order (lowest appears first when script is used elsewhere)

When the .script is imported into another graph as a ScriptNode, all InputNodes
are collected, sorted by Number, and turned into input PINS on that ScriptNode.
"""

import uuid

from PyQt5.QtWidgets import (
    QGraphicsItem, QGraphicsProxyWidget,
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui  import (
    QPen, QBrush, QColor, QPainter,
    QLinearGradient, QFont, QCursor
)

_HDR_COLOR  = QColor("#2a1a3a")
_BODY_COLOR = QColor("#232d3f")
_SEL_COLOR  = QColor("#00b4ff")
_HDR_H      = 26
_BODY_W     = 220

TYPE_OPTIONS = ["float", "int", "bool", "string"]

_FIELD_STYLE = ("background:#0a1520; color:#d4e0f0;"
                "border:1px solid #2a3a5c; border-radius:2px;"
                "font-size:9px; padding:1px 4px;")


class InputNode(QGraphicsItem):
    """
    Defines one input argument for this script.
    Sorted by Number when used as a ScriptNode in another graph.
    """

    PERMANENT   = False
    HEADER_COLOR = _HDR_COLOR

    def __init__(self, node_id: str = None):
        super().__init__()
        self.node_id  = node_id or str(uuid.uuid4())[:8]
        self.in_pins  = []   # always empty — no connection pins
        self.out_pins = []   # always empty

        self.width  = _BODY_W
        self.height = _HDR_H + 84

        self.setFlag(QGraphicsItem.ItemIsMovable,            True)
        self.setFlag(QGraphicsItem.ItemIsSelectable,         True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(5)
        self.setCursor(QCursor(Qt.SizeAllCursor))

        self._build_widget()

    # ── inline settings widget ────────────────────────────────
    def _build_widget(self):
        container = QWidget()
        container.setFixedSize(self.width - 12, 72)
        container.setStyleSheet("QWidget { background: transparent; }")

        lay = QVBoxLayout(container)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(3)

        # Name
        row1 = QHBoxLayout(); row1.setSpacing(4)
        lbl1 = QLabel("Name")
        lbl1.setStyleSheet("color:#8899bb; font-size:8px;")
        lbl1.setFixedWidth(36)
        self._name_edit = QLineEdit("Input")
        self._name_edit.setStyleSheet(_FIELD_STYLE)
        self._name_edit.setFixedHeight(18)
        row1.addWidget(lbl1); row1.addWidget(self._name_edit)
        lay.addLayout(row1)

        # Type
        row2 = QHBoxLayout(); row2.setSpacing(4)
        lbl2 = QLabel("Type")
        lbl2.setStyleSheet("color:#8899bb; font-size:8px;")
        lbl2.setFixedWidth(36)
        self._type_combo = QComboBox()
        self._type_combo.addItems(TYPE_OPTIONS)
        self._type_combo.setStyleSheet(
            "QComboBox{" + _FIELD_STYLE + "}"
            "QComboBox::drop-down{border:none;}"
            "QComboBox QAbstractItemView{background:#0d1117;color:#d4e0f0;"
            "selection-background-color:#1a2a5c;}"
        )
        self._type_combo.setFixedHeight(18)
        row2.addWidget(lbl2); row2.addWidget(self._type_combo)
        lay.addLayout(row2)

        # Number (sort order)
        row3 = QHBoxLayout(); row3.setSpacing(4)
        lbl3 = QLabel("Order")
        lbl3.setStyleSheet("color:#8899bb; font-size:8px;")
        lbl3.setFixedWidth(36)
        self._order_spin = QSpinBox()
        self._order_spin.setRange(0, 9999)
        self._order_spin.setValue(0)
        self._order_spin.setButtonSymbols(QSpinBox.NoButtons)
        self._order_spin.setStyleSheet(_FIELD_STYLE)
        self._order_spin.setFixedHeight(18)
        row3.addWidget(lbl3); row3.addWidget(self._order_spin)
        lay.addLayout(row3)

        self._proxy = QGraphicsProxyWidget(self)
        self._proxy.setWidget(container)
        self._proxy.setPos(6, _HDR_H + 6)
        self._proxy.setZValue(20)

    # ── public accessors ──────────────────────────────────────
    @property
    def input_name(self) -> str:
        return self._name_edit.text().strip() or "Input"

    @property
    def input_type(self) -> str:
        return self._type_combo.currentText()

    @property
    def input_order(self) -> int:
        return self._order_spin.value()

    @property
    def title(self) -> str:
        return "Input"

    # ── graphics ─────────────────────────────────────────────
    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self.width, self.height).adjusted(-3, -3, 3, 3)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        r  = QRectF(0, 0, self.width, self.height)
        hr = QRectF(0, 0, self.width, _HDR_H)

        # shadow
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(r.adjusted(3, 3, 3, 3), 7, 7)

        # body
        body = _BODY_COLOR.lighter(115) if self.isSelected() else _BODY_COLOR
        painter.setBrush(QBrush(body))
        painter.setPen(QPen(_SEL_COLOR, 2) if self.isSelected()
                       else QPen(QColor("#0a1220"), 1))
        painter.drawRoundedRect(r, 7, 7)

        # header
        g = QLinearGradient(0, 0, 0, _HDR_H)
        g.setColorAt(0, _HDR_COLOR.lighter(130))
        g.setColorAt(1, _HDR_COLOR)
        painter.setBrush(QBrush(g))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(hr, 7, 7)
        painter.drawRect(QRectF(0, _HDR_H - 8, self.width, 8))

        # header text
        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(hr.adjusted(10, 0, -6, 0),
                         Qt.AlignVCenter | Qt.AlignLeft, "📥  Input")

        # subtitle — show current name + type for quick reading
        painter.setPen(QPen(QColor("#8899bb")))
        painter.setFont(QFont("Segoe UI", 7))
        painter.drawText(hr.adjusted(0, 0, -6, 0),
                         Qt.AlignVCenter | Qt.AlignRight,
                         f"{self.input_name} : {self.input_type}")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            s = self.scene()
            if s and hasattr(s, 'refresh_wires'):
                s.refresh_wires()
        return super().itemChange(change, value)

    def contextMenuEvent(self, e):
        from PyQt5.QtWidgets import QMenu
        _DARK = ("QMenu{background:#0d1117;color:#d4e0f0;border:1px solid #2a3a5c}"
                 "QMenu::item:selected{background:#1a2a5c}")
        m = QMenu()
        m.setStyleSheet(_DARK)
        del_act = m.addAction("🗑  Delete")
        if m.exec_(e.screenPos()) == del_act:
            s = self.scene()
            if s:
                s.remove_node(self)

    # ── serialise ─────────────────────────────────────────────
    def to_dict(self) -> dict:
        pos = self.scenePos()
        return {
            "id"         : self.node_id,
            "class_key"  : "InputNode",
            "input_name" : self.input_name,
            "input_type" : self.input_type,
            "input_order": self.input_order,
            "x"          : pos.x(),
            "y"          : pos.y(),
            "in_pins"    : [],
            "out_pins"   : [],
        }

    @staticmethod
    def from_dict(nd: dict) -> "InputNode":
        node = InputNode(nd.get("id"))
        node._name_edit.setText(nd.get("input_name", "Input"))
        idx = TYPE_OPTIONS.index(nd.get("input_type", "float")) \
              if nd.get("input_type", "float") in TYPE_OPTIONS else 0
        node._type_combo.setCurrentIndex(idx)
        node._order_spin.setValue(nd.get("input_order", 0))
        return node