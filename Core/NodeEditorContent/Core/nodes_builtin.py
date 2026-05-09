"""nodes_builtin.py  –  MathNode, OutputNode, CustomNode"""

from PyQt5.QtGui     import QColor
from PyQt5.QtWidgets import QMenu
from Core.NodeEditorContent.Core.node_base import BaseNode, _ask_pin, _DARK
from Core.NodeEditorContent.Core.pin       import Pin

_CPP_TYPE = {'float':'float','int':'int','bool':'bool',
             'string':'std::string','custom':''}


def cpp_type(ptype: str) -> str:
    return _CPP_TYPE.get(ptype, 'auto')


class MathNode(BaseNode):
    HEADER_COLOR = QColor("#1e3a2a")
    SUBTITLE     = "Math"

    def __init__(self, node_id: str, op: str = "+"):
        self.META = {"title": op, "category": "Math"}
        super().__init__(node_id)
        self.add_in("A", "float")
        self.add_in("B", "float")
        self.add_out("Result", "float")

    def to_cpp_expr(self, out_pin_index: int, ctx: dict) -> str:
        a = ctx['expr'](self.node_id, 0)
        b = ctx['expr'](self.node_id, 1)
        return f"({a} {self.title} {b})"

    def to_dict(self):
        d = super().to_dict()
        d['op'] = self.title
        return d


class OutputNode(BaseNode):
    HEADER_COLOR = QColor("#6b2020")
    SUBTITLE     = "Output"
    PERMANENT    = True

    def __init__(self, node_id: str):
        self.META = {"title": "Output", "category": "_builtin"}
        super().__init__(node_id)
        self.add_in("Result", "float")

    def contextMenuEvent(self, e):
        m = QMenu()
        m.setStyleSheet(_DARK)
        add_act = m.addAction("＋ Add Return Value")
        rm_menu = None
        if self.in_pins:
            rm_menu = m.addMenu("➖ Remove Return Value")
            rm_menu.setStyleSheet(_DARK)
            for p in self.in_pins:
                act = rm_menu.addAction(f"→ {p.name} [{p.pin_type}]")
                act.setData(p)
        chosen = m.exec_(e.screenPos())
        if chosen is None:
            return
        if chosen == add_act:
            n, t = _ask_pin(None, "Add Return Value")
            if n: self.add_in(n, t)
        elif chosen and isinstance(chosen.data(), Pin):
            self.remove_pin(chosen.data())


class CustomNode(BaseNode):
    HEADER_COLOR = QColor("#1a3a5c")

    def __init__(self, node_id: str, title: str = "Node"):
        self.META = {"title": title, "category": "Custom"}
        super().__init__(node_id)

    def to_cpp_expr(self, out_pin_index: int, ctx: dict) -> str:
        if self.in_pins:
            return ctx['expr'](self.node_id, 0)
        return "0"