"""
undo_redo.py
------------
QUndoCommand subclasses for every undoable action:
  AddNodeCmd      – place a node
  RemoveNodeCmd   – delete a node (blocked on PERMANENT nodes)
  MoveNodeCmd     – drag a node to a new position
  AddWireCmd      – connect two pins
  RemoveWireCmd   – disconnect a wire
  PasteCmd        – paste a clipboard snapshot

All commands talk to NodeScene via its public API so they stay thin.
"""

import copy
from PyQt5.QtCore    import QPointF
from PyQt5.QtWidgets import QUndoCommand


# ─────────────────────────────────────────────────────────────
class AddNodeCmd(QUndoCommand):
    def __init__(self, scene, node, pos: QPointF):
        super().__init__(f"Add {node.title}")
        self._scene = scene
        self._node  = node
        self._pos   = pos

    def redo(self):
        self._scene.add_node(self._node, self._pos)

    def undo(self):
        self._scene._remove_node_no_cmd(self._node)


# ─────────────────────────────────────────────────────────────
class RemoveNodeCmd(QUndoCommand):
    def __init__(self, scene, node):
        super().__init__(f"Delete {node.title}")
        self._scene     = scene
        self._node      = node
        # snapshot wire connectivity so we can restore on undo
        self._wire_data = []
        for p in node.in_pins + node.out_pins:
            for w in list(p.wires):
                try:
                    si = w.src.node.out_pins.index(w.src)
                    di = w.dst.node.in_pins.index(w.dst)
                    self._wire_data.append((w.src.node, si, w.dst.node, di))
                except ValueError:
                    pass
        self._pos = node.scenePos()

    def redo(self):
        self._scene._remove_node_no_cmd(self._node)

    def undo(self):
        self._scene.add_node(self._node, self._pos)
        for src_node, si, dst_node, di in self._wire_data:
            if si < len(src_node.out_pins) and di < len(dst_node.in_pins):
                self._scene._finalize_wire(src_node.out_pins[si],
                                           dst_node.in_pins[di])


# ─────────────────────────────────────────────────────────────
class MoveNodeCmd(QUndoCommand):
    def __init__(self, node, old_pos: QPointF, new_pos: QPointF):
        super().__init__(f"Move {node.title}")
        self._node    = node
        self._old_pos = old_pos
        self._new_pos = new_pos
        self._first   = True   # skip first redo (move already applied)

    def redo(self):
        if self._first:
            self._first = False
            return
        self._node.setPos(self._new_pos)
        s = self._node.scene()
        if s:
            s.refresh_wires()

    def undo(self):
        self._node.setPos(self._old_pos)
        s = self._node.scene()
        if s:
            s.refresh_wires()


# ─────────────────────────────────────────────────────────────
class AddWireCmd(QUndoCommand):
    def __init__(self, scene, src_pin, dst_pin):
        super().__init__("Add Wire")
        self._scene   = scene
        self._src_pin = src_pin
        self._dst_pin = dst_pin
        self._wire    = None

    def redo(self):
        self._wire = self._scene._finalize_wire(self._src_pin, self._dst_pin)

    def undo(self):
        if self._wire:
            self._scene._remove_wire_no_cmd(self._wire)
            self._wire = None


# ─────────────────────────────────────────────────────────────
class RemoveWireCmd(QUndoCommand):
    def __init__(self, scene, wire):
        super().__init__("Delete Wire")
        self._scene   = scene
        self._wire    = wire
        self._src_pin = wire.src
        self._dst_pin = wire.dst

    def redo(self):
        self._scene._remove_wire_no_cmd(self._wire)

    def undo(self):
        self._wire = self._scene._finalize_wire(self._src_pin, self._dst_pin)


# ─────────────────────────────────────────────────────────────
class PasteCmd(QUndoCommand):
    """
    Paste a list of (node, offset_pos) pairs.
    node objects are already cloned before this command is created.
    """
    def __init__(self, scene, nodes_and_positions: list, wire_defs: list):
        super().__init__("Paste")
        self._scene  = scene
        self._items  = nodes_and_positions   # [(node, QPointF), ...]
        self._wdefs  = wire_defs             # [(src_node, si, dst_node, di), ...]
        self._wires  = []

    def redo(self):
        self._wires.clear()
        for node, pos in self._items:
            self._scene.add_node(node, pos)
        for src_node, si, dst_node, di in self._wdefs:
            if si < len(src_node.out_pins) and di < len(dst_node.in_pins):
                w = self._scene._finalize_wire(src_node.out_pins[si],
                                               dst_node.in_pins[di])
                if w:
                    self._wires.append(w)

    def undo(self):
        for w in self._wires:
            self._scene._remove_wire_no_cmd(w)
        self._wires.clear()
        for node, _ in self._items:
            self._scene._remove_node_no_cmd(node)
