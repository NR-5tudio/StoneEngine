"""
nodes_script.py
---------------
Two special nodes for the script-in-script system:

InputNode  – defines an input pin for THIS script when used elsewhere.
             Has 4 settings (no pins of its own):
               Name    – string
               Type    – float | int | bool | string | custom
               Number  – sort order (int)
               Default – inline default value (same widget as pin)
             Exposes one output pin so the user can wire its value
             into the graph.

ScriptNode – represents an imported .script file placed on the canvas.
             Input pins  = the imported script's InputNodes (sorted by Number)
             Output pins = the imported script's OutputNode pins
             C++ export  inlines the imported script's full expression.
"""

import json
import os

from PyQt5.QtWidgets import (
    QGraphicsItem, QGraphicsProxyWidget,
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QSpinBox, QComboBox,
    QDoubleSpinBox, QCheckBox, QSizePolicy
)
from PyQt5.QtGui  import QColor, QFont
from PyQt5.QtCore import Qt, QRectF, QPointF

from Core.NodeEditorContent.Core.node_base import BaseNode, _DARK
from Core.NodeEditorContent.Core.pin       import Pin, pin_color, PIN_R, _make_widget, _read_widget

TYPE_LIST = ['float', 'int', 'bool', 'string', 'custom']

HDR_INPUT  = QColor("#1a3a5c")
HDR_SCRIPT = QColor("#3a1a5c")

SETTING_H  = 22   # height per setting row
HDR_H      = 26
PAD        = 8


# ─────────────────────────────────────────────────────────────
#  InputNode
# ─────────────────────────────────────────────────────────────
class InputNode(BaseNode):
    """
    Defines one input parameter for this script.
    Settings live inside the node body (no input pins).
    Exposes a single output pin so the value can be wired into the graph.
    """

    META         = {"title": "Input", "category": "_builtin"}
    HEADER_COLOR = HDR_INPUT
    SUBTITLE     = "Script Input"
    PERMANENT    = False

    # setting row order
    _FIELDS = ["Name", "Type", "Number", "Default"]

    def __init__(self, node_id: str):
        super().__init__(node_id)

        # internal state
        self._s_name    = "input"
        self._s_type    = "float"
        self._s_number  = 0
        self._s_default = 0.0

        # build the settings widget that lives inside the node
        self._settings_proxy: QGraphicsProxyWidget = None
        self._settings_widget: QWidget             = None
        self._build_settings()

        # one output pin (the value this input provides to the graph)
        self.add_out(self._s_name, self._s_type)
        self._layout()

    # ── settings widget ───────────────────────────────────────
    def _build_settings(self):
        w = QWidget()
        w.setStyleSheet("QWidget{background:#1c2433;color:#d4e0f0}"
                        "QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox,QCheckBox"
                        "{background:#0d1117;color:#d4e0f0;"
                        "border:1px solid #2a3a5c;border-radius:2px;"
                        "font-size:9px;padding:1px 3px}"
                        "QLabel{color:#8899bb;font-size:8px}")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 4, 6, 4)
        lay.setSpacing(3)

        # Name
        row_name = QHBoxLayout()
        row_name.addWidget(QLabel("Name"))
        self._w_name = QLineEdit(self._s_name)
        self._w_name.setFixedHeight(18)
        self._w_name.textChanged.connect(self._on_name_changed)
        row_name.addWidget(self._w_name)
        lay.addLayout(row_name)

        # Type
        row_type = QHBoxLayout()
        row_type.addWidget(QLabel("Type"))
        self._w_type = QComboBox()
        self._w_type.addItems(TYPE_LIST)
        self._w_type.setFixedHeight(18)
        self._w_type.currentTextChanged.connect(self._on_type_changed)
        row_type.addWidget(self._w_type)
        lay.addLayout(row_type)

        # Number (sort order)
        row_num = QHBoxLayout()
        row_num.addWidget(QLabel("Number"))
        self._w_number = QSpinBox()
        self._w_number.setRange(0, 9999)
        self._w_number.setValue(self._s_number)
        self._w_number.setFixedHeight(18)
        self._w_number.setButtonSymbols(QSpinBox.NoButtons)
        row_num.addWidget(self._w_number)
        lay.addLayout(row_num)

        # Default value (starts as float spin)
        row_def = QHBoxLayout()
        row_def.addWidget(QLabel("Default"))
        self._w_default_container = QHBoxLayout()
        row_def.addLayout(self._w_default_container)
        lay.addLayout(row_def)
        self._rebuild_default_widget()

        w.setFixedWidth(180)
        w.adjustSize()

        self._settings_widget = w
        self._settings_proxy  = QGraphicsProxyWidget(self)
        self._settings_proxy.setWidget(w)
        self._settings_proxy.setZValue(20)

    def _rebuild_default_widget(self):
        # clear old widget from container
        while self._w_default_container.count():
            item = self._w_default_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        t = self._s_type
        if t == 'float':
            dw = QDoubleSpinBox()
            dw.setRange(-1e9, 1e9); dw.setDecimals(3)
            dw.setButtonSymbols(QDoubleSpinBox.NoButtons)
            dw.setFixedHeight(18)
            try: dw.setValue(float(self._s_default))
            except: dw.setValue(0.0)
        elif t == 'int':
            dw = QSpinBox()
            dw.setRange(-999999, 999999)
            dw.setButtonSymbols(QSpinBox.NoButtons)
            dw.setFixedHeight(18)
            try: dw.setValue(int(self._s_default))
            except: dw.setValue(0)
        elif t == 'bool':
            dw = QCheckBox()
            dw.setFixedHeight(18)
            try: dw.setChecked(bool(self._s_default))
            except: dw.setChecked(False)
        else:  # string / custom
            dw = QLineEdit()
            dw.setFixedHeight(18)
            dw.setText(str(self._s_default) if self._s_default else "")

        dw.setStyleSheet("background:#0d1117;color:#d4e0f0;"
                         "border:1px solid #2a3a5c;border-radius:2px;"
                         "font-size:9px;padding:1px 3px")
        self._w_default_widget = dw
        self._w_default_container.addWidget(dw)

    def _read_default(self):
        dw = self._w_default_widget
        t  = self._s_type
        if t == 'float':  return dw.value()
        if t == 'int':    return dw.value()
        if t == 'bool':   return dw.isChecked()
        return dw.text()

    # ── setting change handlers ───────────────────────────────
    def _on_name_changed(self, text):
        self._s_name = text.strip() or "input"
        # rename output pin label
        if self.out_pins:
            self.out_pins[0].name = self._s_name
            self.out_pins[0]._label.setPlainText(self._s_name)
            self._layout()

    def _on_type_changed(self, text):
        self._s_type = text
        self._rebuild_default_widget()
        # rebuild output pin with new type
        if self.out_pins:
            old = self.out_pins[0]
            sc  = self.scene()
            if sc:
                for w in list(old.wires):
                    sc._remove_wire_no_cmd(w)
            self.out_pins.clear()
            if old.scene():
                old.scene().removeItem(old)
        self.add_out(self._s_name, self._s_type)
        self._layout()

    # ── layout override ───────────────────────────────────────
    def _layout(self):
        if self._settings_proxy:
            self._settings_widget.adjustSize()
            sw = self._settings_widget.sizeHint().width()  + 16
            sh = self._settings_widget.sizeHint().height() + 8
            self.width  = max(200, sw)
            self.height = HDR_H + sh + PAD + (22 if self.out_pins else 0) + 8
            self._settings_proxy.setPos(4, HDR_H + 4)

        pin_y = self.height - 16
        for p in self.out_pins:
            p.setParentItem(self)
            p.setPos(self.width, pin_y)
            lw = p._label.boundingRect().width()
            p._label.setPos(-PIN_R - 4 - lw, -PIN_R)

        self.update()
        sc = self.scene()
        if sc and hasattr(sc, 'refresh_wires'):
            sc.refresh_wires()

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height).adjusted(-3, -3, 3, 3)

    # ── public getters ────────────────────────────────────────
    @property
    def sort_number(self) -> int:
        return self._w_number.value() if self._w_number else self._s_number

    @property
    def param_name(self) -> str:
        return self._s_name

    @property
    def param_type(self) -> str:
        return self._s_type

    def default_value(self):
        return self._read_default()

    # ── cpp expr ─────────────────────────────────────────────
    def to_cpp_expr(self, out_pin_index: int, ctx: dict) -> str:
        # When used inside its own script, the output pin just
        # exposes whatever was passed in from the parent graph.
        # ctx['param'] holds the expression injected by the parent.
        return ctx.get('params', {}).get(self._s_name, self._cpp_default())

    def _cpp_default(self) -> str:
        v = self._read_default()
        t = self._s_type
        if t == 'float':  return f"{float(v):.6f}f"
        if t == 'int':    return str(int(v))
        if t == 'bool':   return "true" if v else "false"
        return f'"{v}"'

    # ── serialise ─────────────────────────────────────────────
    def to_dict(self) -> dict:
        d = super().to_dict()
        d['s_name']    = self._s_name
        d['s_type']    = self._s_type
        d['s_number']  = self._w_number.value()
        d['s_default'] = self._read_default()
        return d

    def _restore(self, d: dict):
        self._s_name    = d.get('s_name',    'input')
        self._s_type    = d.get('s_type',    'float')
        self._s_number  = d.get('s_number',  0)
        self._s_default = d.get('s_default', 0.0)
        self._w_name.setText(self._s_name)
        idx = self._w_type.findText(self._s_type)
        if idx >= 0: self._w_type.setCurrentIndex(idx)
        self._w_number.setValue(self._s_number)
        self._rebuild_default_widget()


# ─────────────────────────────────────────────────────────────
#  ScriptNode  (an imported .script used inside another graph)
# ─────────────────────────────────────────────────────────────
class ScriptNode(BaseNode):
    """
    Represents an imported .script file placed on the canvas.
    Input pins  ← sorted InputNodes from the imported script
    Output pins ← OutputNode's input pins from the imported script
    """

    HEADER_COLOR = HDR_SCRIPT
    SUBTITLE     = "Script"

    def __init__(self, node_id: str, script_path: str = ""):
        self.META        = {"title": "📄 (empty)", "category": "_builtin"}
        self.script_path = script_path
        self._script_data: dict = {}
        super().__init__(node_id)
        if script_path:
            self._load(script_path)

    # ── load ──────────────────────────────────────────────────
    def _load(self, path: str):
        if not os.path.isfile(path):
            self.META = dict(self.META)
            self.META['title'] = f"📄 NOT FOUND"
            return

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._script_data = data
        name = data.get('meta', {}).get('func_name',
               os.path.splitext(os.path.basename(path))[0])
        self.META = {"title": f"📄 {name}", "category": "_builtin"}

        # clear existing pins
        for p in list(self.in_pins + self.out_pins):
            if p.scene(): p.scene().removeItem(p)
        self.in_pins.clear()
        self.out_pins.clear()

        # input pins from InputNodes sorted by Number
        inputs = _extract_inputs(data)
        for inp in inputs:
            self.add_in(inp['name'], inp['type'])

        # output pins from the OutputNode
        outputs = _extract_outputs(data)
        for out in outputs:
            self.add_out(out['name'], out['type'])

        self._layout()

    # ── cpp expression ────────────────────────────────────────
    def to_cpp_expr(self, out_pin_index: int, ctx: dict) -> str:
        """
        Inline-expand the imported script.
        Passes each connected input expression as a param into the sub-graph.
        """
        if not self._script_data:
            return "0"

        from Core.NodeEditorContent.Core.cpp_export import inline_script

        # build param map: input_name -> cpp expression from this node's in-pins
        params = {}
        inputs = _extract_inputs(self._script_data)
        for i, inp in enumerate(inputs):
            params[inp['name']] = ctx['expr'](self.node_id, i)

        return inline_script(self._script_data, out_pin_index, params,
                             ctx.get('helpers_list', []))

    # ── serialise ─────────────────────────────────────────────
    def to_dict(self) -> dict:
        d = super().to_dict()
        d['script_path'] = self.script_path
        return d


# ── helpers ───────────────────────────────────────────────────

def _extract_inputs(data: dict) -> list:
    """Return sorted list of {name, type} from a script's InputNodes."""
    result = []
    for nd in data.get('nodes', []):
        if nd.get('class_key') == 'InputNode':
            result.append({
                'name'   : nd.get('s_name',   'input'),
                'type'   : nd.get('s_type',   'float'),
                'number' : nd.get('s_number', 0),
                'default': nd.get('s_default', 0),
            })
    result.sort(key=lambda x: x['number'])
    return result


def _extract_outputs(data: dict) -> list:
    """Return list of {name, type} from a script's OutputNode's in-pins."""
    for nd in data.get('nodes', []):
        if nd.get('class_key') == 'OutputNode':
            return [{'name': p.get('name','Result'),
                     'type': p.get('type','float')}
                    for p in nd.get('in_pins', [])]
    return [{'name': 'Result', 'type': 'float'}]