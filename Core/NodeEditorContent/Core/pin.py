"""
pin.py
------
A Pin is a connection point on a node.
- direction : 'in' | 'out'
- pin_type  : 'float' | 'int' | 'bool' | 'string'

Unconnected INPUT pins show an inline value widget (QGraphicsProxyWidget).
The widget hides when a wire connects and reappears (with saved value) when
the wire is removed.
"""

from PyQt5.QtWidgets import (
    QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsProxyWidget,
    QLineEdit, QSpinBox, QCheckBox, QDoubleSpinBox
)
from PyQt5.QtCore  import Qt, QPointF
from PyQt5.QtGui   import QPen, QBrush, QColor, QPainter, QPainterPath, QCursor, QFont

PIN_COLORS = {
    'float' : QColor("#5bb8c4"),
    'int'   : QColor("#3ca370"),
    'bool'  : QColor("#c0392b"),
    'string': QColor("#e83e8c"),
}

PIN_R = 6


def pin_color(ptype: str) -> QColor:
    return PIN_COLORS.get(ptype, QColor("#9b59b6"))


def _make_widget(ptype: str, saved_value):
    """Return a plain Qt widget for the given pin type, pre-filled with saved_value."""
    style = ("background:#0a1520; color:#d4e0f0; border:1px solid #2a3a5c;"
             "border-radius:2px; font-size:9px;")

    if ptype == 'float':
        w = QDoubleSpinBox()
        w.setRange(-1e9, 1e9)
        w.setDecimals(3)
        w.setSingleStep(0.1)
        w.setButtonSymbols(QDoubleSpinBox.NoButtons)
        w.setFixedSize(64, 18)
        w.setStyleSheet(style)
        try:
            w.setValue(float(saved_value))
        except (TypeError, ValueError):
            w.setValue(0.0)
        return w

    if ptype == 'int':
        w = QSpinBox()
        w.setRange(-999999, 999999)
        w.setButtonSymbols(QSpinBox.NoButtons)
        w.setFixedSize(56, 18)
        w.setStyleSheet(style)
        try:
            w.setValue(int(saved_value))
        except (TypeError, ValueError):
            w.setValue(0)
        return w

    if ptype == 'bool':
        w = QCheckBox()
        w.setFixedSize(18, 18)
        w.setStyleSheet("QCheckBox::indicator{width:12px;height:12px;"
                        "border:1px solid #2a3a5c;border-radius:2px;background:#0a1520;}"
                        "QCheckBox::indicator:checked{background:#c0392b;}")
        try:
            w.setChecked(bool(saved_value))
        except (TypeError, ValueError):
            w.setChecked(False)
        return w

    if ptype == 'string':
        w = QLineEdit()
        w.setFixedSize(72, 18)
        w.setStyleSheet(style)
        w.setText(str(saved_value) if saved_value is not None else "")
        return w

    return None


def _default_value(ptype: str):
    return {'float': 0.0, 'int': 0, 'bool': False, 'string': ''}. get(ptype, 0.0)


def _read_widget(ptype: str, widget) -> object:
    if ptype == 'float':  return widget.value()
    if ptype == 'int':    return widget.value()
    if ptype == 'bool':   return widget.isChecked()
    if ptype == 'string': return widget.text()
    return 0.0


class Pin(QGraphicsEllipseItem):
    """
    A typed connection point.
    Input pins (direction == 'in') host an inline value widget when unconnected.
    """

    def __init__(self, node, name: str, pin_type: str, direction: str, index: int):
        super().__init__(-PIN_R, -PIN_R, PIN_R * 2, PIN_R * 2)
        self.node       = node
        self.name       = name
        self.pin_type   = pin_type
        self.direction  = direction
        self.index      = index
        self.wires      = []                        # connected Wire objects
        self._saved_val = _default_value(pin_type)  # persists across connect/disconnect

        self._color = pin_color(pin_type)
        self.setBrush(QBrush(self._color))
        self.setPen(QPen(self._color.darker(150), 1))

        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, False)
        self.setCursor(QCursor(Qt.CrossCursor))
        self.setZValue(10)

        # Label
        self._label = QGraphicsTextItem(name, self)
        self._label.setDefaultTextColor(QColor("#d4e0f0"))
        self._label.setFont(QFont("Consolas", 7))
        self._label.setZValue(11)

        # Inline value widget (input pins only)
        self._proxy : QGraphicsProxyWidget = None
        self._widget = None
        if direction == 'in':
            self._build_proxy()

        self._place_children()

    # ── proxy / widget ────────────────────────────────────────
    def _build_proxy(self):
        w = _make_widget(self.pin_type, self._saved_val)
        if w is None:
            return
        self._widget = w
        self._proxy  = QGraphicsProxyWidget(self)
        self._proxy.setWidget(w)
        self._proxy.setZValue(20)

    def _place_children(self):
        lw = self._label.boundingRect().width()
        if self.direction == 'in':
            self._label.setPos(PIN_R + 4, -PIN_R)
            if self._proxy:
                lbl_right = PIN_R + 4 + lw + 4
                self._proxy.setPos(lbl_right, -9)
        else:
            self._label.setPos(-PIN_R - 4 - lw, -PIN_R)

    # ── public: label width for node layout ───────────────────
    def _proxy_visible(self) -> bool:
        """QGraphicsProxyWidget uses isVisible(), not isHidden()."""
        return self._proxy is not None and self._proxy.isVisible()

    def total_width(self) -> float:
        lw = self._label.boundingRect().width()
        if self.direction == 'in' and self._proxy_visible():
            return PIN_R + 4 + lw + 4 + self._proxy.boundingRect().width() + 6
        return PIN_R + 4 + lw + 8

    # ── wire connect / disconnect ─────────────────────────────
    def on_connected(self):
        if self._proxy:
            if self._widget:
                self._saved_val = _read_widget(self.pin_type, self._widget)
            self._proxy.hide()

    def on_disconnected(self):
        if self._proxy:
            # restore saved value into widget
            if self._widget:
                if self.pin_type == 'float':
                    self._widget.setValue(float(self._saved_val))
                elif self.pin_type == 'int':
                    self._widget.setValue(int(self._saved_val))
                elif self.pin_type == 'bool':
                    self._widget.setChecked(bool(self._saved_val))
                elif self.pin_type == 'string':
                    self._widget.setText(str(self._saved_val))
            self._proxy.show()

    # ── current value (for C++ export) ───────────────────────
    def inline_value(self):
        if self._widget and self._proxy_visible():
            return _read_widget(self.pin_type, self._widget)
        return self._saved_val

    # ── scene helpers ─────────────────────────────────────────
    def scene_center(self) -> QPointF:
        return self.mapToScene(QPointF(0, 0))

    # ── paint: diamond for float, circle for others ───────────
    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        c = self._color
        painter.setBrush(QBrush(c))
        painter.setPen(QPen(c.darker(150), 1))

        if self.pin_type == 'float':
            # diamond
            path = QPainterPath()
            path.moveTo(0, -PIN_R)
            path.lineTo(PIN_R, 0)
            path.lineTo(0, PIN_R)
            path.lineTo(-PIN_R, 0)
            path.closeSubpath()
            painter.drawPath(path)
        else:
            super().paint(painter, option, widget)

    def hoverEnterEvent(self, e):
        self.setPen(QPen(self._color.lighter(160), 2))
        self.update()
        super().hoverEnterEvent(e)

    def hoverLeaveEvent(self, e):
        self.setPen(QPen(self._color.darker(150), 1))
        self.update()
        super().hoverLeaveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            from Core.NodeEditorContent.Core.scene import NodeScene
            s = self.scene()
            if isinstance(s, NodeScene):
                s.start_wire(self)
        e.accept()

    # ── serialise ─────────────────────────────────────────────
    def to_dict(self) -> dict:
        val = self._saved_val
        if self._widget and self._proxy_visible():
            val = _read_widget(self.pin_type, self._widget)
        return {"name": self.name, "type": self.pin_type, "value": val}