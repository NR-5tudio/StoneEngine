"""
nodes_builtin.py
----------------
Built-in node types that ship with the editor:
  • MathNode   – binary arithmetic (+  -  *  /  %)
  • OutputNode – the single permanent sink; defines the function's return value
  • CustomNode – a blank user-named node (add pins manually)
"""

from PyQt5.QtGui import QColor
from Core.NodeEditorContent.Core.node_base import BaseNode

_CPP_TYPE = {
    'float' : 'float',
    'int'   : 'int',
    'bool'  : 'bool',
    'string': 'std::string',
}


def cpp_type(ptype: str) -> str:
    return _CPP_TYPE.get(ptype, 'auto')


# ─────────────────────────────────────────────────────────────
class MathNode(BaseNode):
    """Binary math operator:  Result = A  op  B"""

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


# ─────────────────────────────────────────────────────────────
class OutputNode(BaseNode):
    """
    Permanent sink node.
    Its input pins define the function's return values.
    The function name is set in the toolbar — not here.
    """

    HEADER_COLOR = QColor("#6b2020")
    SUBTITLE     = "Output"
    PERMANENT    = True

    def __init__(self, node_id: str):
        self.META = {"title": "Output", "category": "_builtin"}
        super().__init__(node_id)
        self.add_in("Result", "float")

    # Output node: allow adding/removing value inputs only
    def contextMenuEvent(self, e):
        from PyQt5.QtWidgets import QMenu
        from Core.NodeEditorContent.Core.node_base import _ask_pin, _DARK
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
            if n:
                self.add_in(n, t)
        elif chosen and hasattr(chosen, 'data') and isinstance(chosen.data(), __import__('Core.NodeEditorContent.Core.pin', fromlist=['Pin']).Pin):
            self.remove_pin(chosen.data())


# ─────────────────────────────────────────────────────────────
class CustomNode(BaseNode):
    """A blank user-named node.  Pins added via right-click."""

    HEADER_COLOR = QColor("#1a3a5c")

    def __init__(self, node_id: str, title: str = "Node"):
        self.META = {"title": title, "category": "Custom"}
        super().__init__(node_id)

    def to_cpp_expr(self, out_pin_index: int, ctx: dict) -> str:
        # default: pass-through the first input or '0'
        if self.in_pins:
            return ctx['expr'](self.node_id, 0)
        return "0"
