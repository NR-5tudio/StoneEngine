"""node_loader.py  –  scans Nodes/ folder, builds REGISTRY + TREE"""

import os
import sys

REGISTRY = {}   # class_key -> class
TREE     = {}   # nested folder dict, leaves are classes


def _nodes_root() -> str:
    here = os.path.dirname(os.path.abspath(__file__))          # Core/NodeEditorContent/Core/
    return os.path.normpath(os.path.join(here, "..", "Nodes")) # Core/NodeEditorContent/Nodes/


def load_nodes(nodes_dir: str = None) -> None:
    from Core.NodeEditorContent.Core.node_base import BaseNode

    global REGISTRY, TREE
    REGISTRY.clear()
    TREE.clear()

    root = nodes_dir or _nodes_root()
    if not os.path.isdir(root):
        print(f"[NodeLoader] Nodes directory not found: {root}")
        return

    for dirpath, dirnames, filenames in os.walk(root):
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
            rel   = os.path.relpath(dirpath, root)
            parts = [] if rel == "." else rel.replace("\\", "/").split("/")
            _insert_tree(TREE, parts, class_key, cls)

    print(f"[NodeLoader] Loaded {len(REGISTRY)} node(s).")


def _load_node_file(fpath: str, BaseNode):
    with open(fpath, "r", encoding="utf-8") as f:
        source = f.read()

    ns = {
        "__file__" : fpath,
        "__name__" : os.path.splitext(os.path.basename(fpath))[0],
        "BaseNode" : BaseNode,
        "sys"      : sys,
    }
    try:
        exec(compile(source, fpath, "exec"), ns)
    except Exception as ex:
        raise RuntimeError(f"exec error: {ex}") from ex

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
    node[key] = cls


def instantiate(class_key: str, node_id: str):
    cls = REGISTRY.get(class_key)
    if cls is None:
        return None
    return cls(node_id)