"""
script_node.py
--------------
ScriptNode – a node that represents an imported .script file.

When a user picks a .script from the Project menu, a ScriptNode is placed
on the canvas.  Its pins are built by reading the target script:

  INPUT  pins  ← come from InputNode entries (sorted by input_order)
  OUTPUT pins  ← come from the OutputNode's input pins (the return values)

C++ export
----------
The ScriptNode inlines the full logic of the imported script at the call
site — no separate function is generated.  It uses the same generate_cpp
machinery on a temporary scene loaded from the imported file.

The result is substituted as an expression, so the parent script sees it
as just another value — no function call overhead in the output.
"""

import json
import os
import uuid

from PyQt5.QtGui   import QColor
from Core.NodeEditorContent.Core.node_base import BaseNode

_HDR_COLOR = QColor("#1a3a5c")


class ScriptNode(BaseNode):
    """
    Represents one imported .script file inside another graph.

    Parameters
    ----------
    node_id     : unique node ID
    script_path : absolute path to the .script file
    """

    HEADER_COLOR = _HDR_COLOR
    SUBTITLE     = "Script"

    def __init__(self, node_id: str, script_path: str):
        self.META = {
            "title"   : os.path.splitext(os.path.basename(script_path))[0],
            "category": "_script",
        }
        super().__init__(node_id)
        self.script_path = script_path
        self._build_pins_from_script()

    # ── read the target script and build pins ─────────────────
    def _build_pins_from_script(self):
        if not os.path.isfile(self.script_path):
            self.add_in("⚠ not found", "float")
            return

        try:
            with open(self.script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.add_in("⚠ parse error", "float")
            return

        nodes = data.get("nodes", [])

        # ── inputs: collect InputNode entries, sort by input_order ──
        inputs = sorted(
            [n for n in nodes if n.get("class_key") == "InputNode"],
            key=lambda n: n.get("input_order", 0)
        )
        for inp in inputs:
            self.add_in(inp.get("input_name", "In"),
                        inp.get("input_type", "float"))

        # ── outputs: read OutputNode's input pins (its return values) ──
        out_nd = next((n for n in nodes if n.get("class_key") == "OutputNode"), None)
        if out_nd:
            for pin in out_nd.get("in_pins", []):
                self.add_out(pin.get("name", "Result"),
                             pin.get("type", "float"))
        else:
            self.add_out("Result", "float")

    # ── C++ expression — inline the imported script ───────────
    def to_cpp_expr(self, out_pin_index: int, ctx: dict) -> str:
        """
        Inline the imported script's logic at this call site.

        Steps:
          1. Load the .script into a temporary NodeScene
          2. Patch the InputNode inline values with the expressions
             that are wired into THIS node's input pins
          3. Run generate_cpp on the temp scene to get the function body
          4. Extract just the return expression and any helpers,
             then return the expression for the requested output pin
        """
        if not os.path.isfile(self.script_path):
            return "0.0f  /* script not found */"

        try:
            with open(self.script_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as ex:
            return f"0.0f  /* parse error: {ex} */"

        # ── build a temporary scene ───────────────────────────
        from Core.NodeEditorContent.Core.scene       import NodeScene
        from Core.NodeEditorContent.Core.node_loader import load_nodes
        from Core.NodeEditorContent.Core.cpp_export  import (
            generate_cpp_inline, _literal, _safe_ident
        )

        load_nodes()
        tmp_scene = NodeScene()
        tmp_scene.from_dict(data)

        # ── patch InputNode inline values with parent expressions ─
        # Sort the InputNodes by order — same order as our in_pins
        inp_nodes = sorted(
            [n for n in tmp_scene.nodes
             if n.__class__.__name__ == "InputNode"],
            key=lambda n: n.input_order
        )
        for i, inp_node in enumerate(inp_nodes):
            parent_expr = ctx['expr'](self.node_id, i)
            # store the parent expression as the "inline value" override
            inp_node._cpp_override = parent_expr

        # ── generate inlined expression for the requested output ──
        func_name = self.META["title"]
        result    = generate_cpp_inline(tmp_scene, func_name, out_pin_index,
                                        ctx.get('helpers_list', []))
        return result

    # ── serialise ─────────────────────────────────────────────
    def to_dict(self) -> dict:
        d = super().to_dict()
        d["class_key"]   = "ScriptNode"
        d["script_path"] = self.script_path
        return d

    @staticmethod
    def from_dict_static(nd: dict) -> "ScriptNode":
        return ScriptNode(nd.get("id", str(uuid.uuid4())[:8]),
                          nd.get("script_path", ""))