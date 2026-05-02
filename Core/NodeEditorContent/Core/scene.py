"""
scene.py
--------
NodeScene – QGraphicsScene subclass.

Responsibilities:
  • Holds all nodes and wires
  • Manages temp-wire drag
  • Fires QUndoCommands for every mutation
  • Copy / Paste
  • Save / Load (JSON)
  • refresh_wires()
"""

import copy
import json
import uuid

from PyQt5.QtWidgets import QGraphicsScene, QUndoStack
from PyQt5.QtCore    import QPointF, Qt

from Core.NodeEditorContent.Core.pin        import Pin
from Core.NodeEditorContent.Core.wire       import Wire, TempWire
from Core.NodeEditorContent.Core.undo_redo  import (
    AddNodeCmd, RemoveNodeCmd, MoveNodeCmd,
    AddWireCmd, RemoveWireCmd, PasteCmd
)


def _new_id() -> str:
    return str(uuid.uuid4())[:8]


class NodeScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self.setSceneRect(-5000, -5000, 10000, 10000)

        self.nodes : list = []
        self.wires : list = []

        self._temp_wire : TempWire = None
        self._wire_src  : Pin      = None

        self._undo = QUndoStack(self)

        # clipboard: raw dict snapshot
        self._clipboard = None

        # track pre-move positions for MoveNodeCmd
        self._pre_move : dict = {}   # node -> QPointF

    # ── undo stack access ────────────────────────────────────
    @property
    def undo_stack(self) -> QUndoStack:
        return self._undo

    # ── node management ──────────────────────────────────────
    def add_node(self, node, pos: QPointF = None, push_undo: bool = False):
        if push_undo:
            cmd = AddNodeCmd(self, node, pos or QPointF(0, 0))
            self._undo.push(cmd)
            return node
        self.nodes.append(node)
        self.addItem(node)
        if pos is not None:
            node.setPos(pos)
        return node

    def remove_node(self, node):
        """Public: push a RemoveNodeCmd onto the undo stack."""
        if getattr(node, 'PERMANENT', False):
            return
        cmd = RemoveNodeCmd(self, node)
        self._undo.push(cmd)

    def _remove_node_no_cmd(self, node):
        """Internal: actually remove without touching the undo stack."""
        for p in node.in_pins + node.out_pins:
            for w in list(p.wires):
                self._remove_wire_no_cmd(w)
        if node in self.nodes:
            self.nodes.remove(node)
        if node.scene():
            self.removeItem(node)

    # ── wire management ──────────────────────────────────────
    def _finalize_wire(self, src: Pin, dst: Pin):
        """Internal: create Wire, register it, notify pins. Returns the wire."""
        if src.direction == 'in':
            src, dst = dst, src

        # disconnect existing wire on dst (one wire per in-pin enforced)
        for w in list(dst.wires):
            self._remove_wire_no_cmd(w)

        w = Wire(src, dst)
        self.addItem(w)
        self.wires.append(w)
        src.wires.append(w)
        dst.wires.append(w)
        src.on_connected()
        dst.on_connected()
        return w

    def remove_wire(self, wire: Wire):
        """Public: push RemoveWireCmd."""
        cmd = RemoveWireCmd(self, wire)
        self._undo.push(cmd)

    def _remove_wire_no_cmd(self, wire: Wire):
        """Internal: actually remove wire, notify pins."""
        for lst in (wire.src.wires, wire.dst.wires, self.wires):
            if wire in lst:
                lst.remove(wire)
        if not wire.src.wires:
            wire.src.on_disconnected()
        if not wire.dst.wires:
            wire.dst.on_disconnected()
        if wire.scene():
            self.removeItem(wire)

    def refresh_wires(self):
        for w in self.wires:
            w.update_path()

    # ── temp wire (drag) ─────────────────────────────────────
    def start_wire(self, pin: Pin):
        if self._temp_wire:
            self.removeItem(self._temp_wire)
        self._wire_src  = pin
        self._temp_wire = TempWire(pin)
        self.addItem(self._temp_wire)

    def mouseMoveEvent(self, e):
        if self._temp_wire:
            self._temp_wire.update_end(e.scenePos())
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        if self._temp_wire and e.button() == Qt.LeftButton:
            hit = next(
                (it for it in self.items(e.scenePos())
                 if isinstance(it, Pin) and it is not self._wire_src),
                None
            )
            if hit and self._can_connect(self._wire_src, hit):
                cmd = AddWireCmd(self, self._wire_src, hit)
                self._undo.push(cmd)
            self.removeItem(self._temp_wire)
            self._temp_wire = None
            self._wire_src  = None
        super().mouseReleaseEvent(e)

    def _can_connect(self, a: Pin, b: Pin) -> bool:
        if a.direction == b.direction:
            return False
        return a.pin_type == b.pin_type

    # ── move tracking (for MoveNodeCmd) ──────────────────────
    def record_pre_move(self, nodes):
        self._pre_move = {n: n.scenePos() for n in nodes}

    def commit_moves(self):
        for node, old_pos in self._pre_move.items():
            new_pos = node.scenePos()
            if (new_pos - old_pos).manhattanLength() > 1:
                cmd = MoveNodeCmd(node, old_pos, new_pos)
                self._undo.push(cmd)
        self._pre_move.clear()

    # ── copy / paste ─────────────────────────────────────────
    def copy_selected(self):
        selected = [n for n in self.nodes if n.isSelected()]
        if not selected:
            return
        self._clipboard = {
            "nodes": [n.to_dict() for n in selected],
            "wires": self._wires_between(selected),
        }

    def paste(self):
        if not self._clipboard:
            return
        offset = QPointF(30, 30)

        # rebuild nodes with new IDs
        id_remap   = {}   # old_id -> new_node
        new_items  = []
        for nd in self._clipboard["nodes"]:
            node = self._rebuild_node(nd)
            if node is None:
                continue
            old_id       = nd["id"]
            node.node_id = _new_id()
            id_remap[old_id] = node
            pos = QPointF(nd.get("x", 0), nd.get("y", 0)) + offset
            new_items.append((node, pos))

        # rebuild wires between pasted nodes only
        wire_defs = []
        for wd in self._clipboard.get("wires", []):
            sn = id_remap.get(wd["src"])
            dn = id_remap.get(wd["dst"])
            if sn and dn:
                wire_defs.append((sn, wd["sp"], dn, wd["dp"]))

        cmd = PasteCmd(self, new_items, wire_defs)
        self._undo.push(cmd)

        # select pasted nodes
        self.clearSelection()
        for node, _ in new_items:
            node.setSelected(True)

    def _wires_between(self, nodes) -> list:
        node_set = set(id(n) for n in nodes)
        result   = []
        for w in self.wires:
            if (id(w.src.node) in node_set and id(w.dst.node) in node_set):
                try:
                    si = w.src.node.out_pins.index(w.src)
                    di = w.dst.node.in_pins.index(w.dst)
                    result.append({"src": w.src.node.node_id, "sp": si,
                                   "dst": w.dst.node.node_id, "dp": di})
                except ValueError:
                    pass
        return result

    # ── delete selected ───────────────────────────────────────
    def delete_selected(self):
        from Core.NodeEditorContent.Core.wire import Wire as WireClass
        self._undo.beginMacro("Delete Selection")
        for item in list(self.selectedItems()):
            if isinstance(item, WireClass):
                self.remove_wire(item)
        for item in list(self.selectedItems()):
            from Core.NodeEditorContent.Core.node_base import BaseNode
            if isinstance(item, BaseNode) and not item.PERMANENT:
                self.remove_node(item)
        self._undo.endMacro()

    # ── save / load ───────────────────────────────────────────
    def to_dict(self) -> dict:
        wire_data = []
        for w in self.wires:
            try:
                si = w.src.node.out_pins.index(w.src)
                di = w.dst.node.in_pins.index(w.dst)
                wire_data.append({"src": w.src.node.node_id, "sp": si,
                                  "dst": w.dst.node.node_id, "dp": di})
            except ValueError:
                pass
        return {"nodes": [n.to_dict() for n in self.nodes],
                "wires": wire_data}

    def from_dict(self, data: dict):
        # clear everything
        for n in list(self.nodes):
            self._remove_node_no_cmd(n)
        for w in list(self.wires):
            self._remove_wire_no_cmd(w)
        self.nodes.clear()
        self.wires.clear()
        self._undo.clear()

        id_map = {}
        for nd in data.get("nodes", []):
            node = self._rebuild_node(nd)
            if node is None:
                continue
            pos = QPointF(nd.get("x", 0), nd.get("y", 0))
            self.add_node(node, pos)
            id_map[nd["id"]] = node

        for wd in data.get("wires", []):
            sn = id_map.get(wd["src"])
            dn = id_map.get(wd["dst"])
            if sn and dn:
                si, di = wd["sp"], wd["dp"]
                if si < len(sn.out_pins) and di < len(dn.in_pins):
                    self._finalize_wire(sn.out_pins[si], dn.in_pins[di])

    def _rebuild_node(self, nd: dict):
        """Reconstruct a node from its serialised dict."""
        from Core.NodeEditorContent.Core.nodes_builtin import (
            MathNode, OutputNode, CustomNode
        )
        from Core.NodeEditorContent.Core.node_loader import REGISTRY

        ck = nd.get("class_key", "")
        nid = nd.get("id", _new_id())

        # built-ins
        if ck == "MathNode":
            node = MathNode(nid, nd.get("op", "+"))
        elif ck == "OutputNode":
            node = OutputNode(nid)
        elif ck == "CustomNode":
            title = nd.get("meta", {}).get("title", "Node")
            node  = CustomNode(nid, title)
        elif ck in REGISTRY:
            node = REGISTRY[ck](nid)
        else:
            node = CustomNode(nid, nd.get("meta", {}).get("title", ck))

        # restore extra pins beyond the defaults
        default_in  = len(node.in_pins)
        default_out = len(node.out_pins)
        for pd in nd.get("in_pins",  [])[default_in:]:
            node.add_in(pd["name"], pd.get("type", "float"))
        for pd in nd.get("out_pins", [])[default_out:]:
            node.add_out(pd["name"], pd.get("type", "float"))

        # restore saved inline values
        for i, pd in enumerate(nd.get("in_pins", [])):
            if i < len(node.in_pins):
                node.in_pins[i]._saved_val = pd.get("value", 0)
                node.in_pins[i].on_disconnected()   # refresh widget

        return node