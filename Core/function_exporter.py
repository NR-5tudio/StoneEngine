"""
cpp_exporter.py
---------------
Standalone converter: .script file -> C++ function string.

Usage
-----
    from cpp_exporter import ConvertScriptToCpp

    cpp = ConvertScriptToCpp("path/to/file.script")
    print(cpp)

Returns None if the file could not be read.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def ConvertScriptToCpp(script_path: str) -> str | None:
    """
    Load a .script file and return the generated C++ function as a string.

    Parameters
    ----------
    script_path : str
        Full or relative path to the .script JSON file.

    Returns
    -------
    str   – the C++ function string
    None  – if the file could not be found or parsed
    """
    if not os.path.isfile(script_path):
        print(f"[CppExporter] File not found: {script_path}")
        return None

    try:
        with open(script_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as ex:
        print(f"[CppExporter] Failed to read {script_path}: {ex}")
        return None

    func_name = data.get("meta", {}).get("func_name", "my_function")

    # Build a temporary scene and load the graph into it
    from NodeEditorContent.Core.scene      import NodeScene
    from NodeEditorContent.Core.node_loader import load_nodes
    from NodeEditorContent.Core.cpp_export  import generate_cpp

    load_nodes()

    scene = NodeScene()
    scene.from_dict(data)

    return generate_cpp(scene, func_name)


# ── CLI usage: python cpp_exporter.py my_file.script ──────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cpp_exporter.py <path_to_script>")
        sys.exit(1)

    result = ConvertScriptToCpp(sys.argv[1])
    if result:
        print(result)