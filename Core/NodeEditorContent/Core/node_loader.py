"""
node_loader.py
--------------
Scans  NodeEditorContent/Nodes/  recursively for *.node Python files.
Each .node file must define exactly one class that subclasses BaseNode
and has a META dict.

The loader builds:
  REGISTRY  – dict[class_key: str  -> NodeClass]
  TREE      – nested dict representing the folder structure
               e.g. {"Math": {"Trig": {"Sin": SinNodeClass}}}

Usage
-----
    from NodeEditorContent.Core.node_loader import load_nodes, REGISTRY, TREE
    load_nodes()          # call once at startup / on reload
"""

import os
import sys
import types

REGISTRY : dict[str, type] = {}   # class_key -> class
TREE     : dict             = {}   # nested folder dict -> class at leaves


def _nodes_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))          # Core/
    return os.path.normpath(os.path.join(here, "..", "Nodes")) # Nodes/


def load_nodes(nodes_dir: str = None) -> None:
    """Scan the Nodes directory and populate REGISTRY and TREE."""
    from Core.NodeEditorContent.Core.node_base import BaseNode

    global REGISTRY, TREE
    REGISTRY.clear()
    TREE.clear()

    root = nodes_dir or _nodes_root()
    if not os.path.isdir(root):
        print(f"[NodeLoader] Nodes directory not found: {root}")
        return

    for dirpath, dirnames, filenames in os.walk(root):
        # skip __pycache__ etc.
        dirnames[:] = [d for d in sorted(dirnames) if not d.startswith('_')]

        for fname in sorted(filenames):
            if not fname.endswith(".node"):
                continue

            fpath = os.path.join(dirpath, fname)
            try:
                cls = _load_node_file(fpath, BaseNode)
            except Exception as ex:
                print(f"[NodeLoader] Failed to load {fpath}: {ex}")
                continue

            if cls is None:
                continue

            class_key = cls.__name__
            REGISTRY[class_key] = cls

            # build tree path from folder structure relative to root
            rel   = os.path.relpath(dirpath, root)   # e.g. "Math/Trig" or "."
            parts = [] if rel == "." else rel.replace("\\", "/").split("/")
            _insert_tree(TREE, parts, class_key, cls)

    print(f"[NodeLoader] Loaded {len(REGISTRY)} node(s).")


def _load_node_file(fpath: str, BaseNode):
    """exec() the .node file in a fresh namespace and extract the node class."""
    with open(fpath, "r", encoding="utf-8") as f:
        source = f.read()

    ns = {
        "__file__"  : fpath,
        "__name__"  : os.path.splitext(os.path.basename(fpath))[0],
        "BaseNode"  : BaseNode,
        # make the full package importable inside the .node file
        "sys"       : sys,
    }

    try:
        exec(compile(source, fpath, "exec"), ns)
    except Exception as ex:
        raise RuntimeError(f"exec error: {ex}") from ex

    # find the first class in ns that subclasses BaseNode (but isn't BaseNode itself)
    for obj in ns.values():
        if (isinstance(obj, type)
                and issubclass(obj, BaseNode)
                and obj is not BaseNode
                and hasattr(obj, "META")):
            return obj

    print(f"[NodeLoader] No valid BaseNode subclass found in {fpath}")
    return None


def _insert_tree(tree: dict, path_parts: list, key: str, cls) -> None:
    node = tree
    for part in path_parts:
        node = node.setdefault(part, {})
    node[key] = cls   # leaf: class_key -> class


# ── public helpers ────────────────────────────────────────────

def instantiate(class_key: str, node_id: str):
    """Create a node instance by its class key.  Returns None if unknown."""
    cls = REGISTRY.get(class_key)
    if cls is None:
        return None
    return cls(node_id)