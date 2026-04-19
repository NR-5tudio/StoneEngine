import re
import random
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QHBoxLayout, QLabel
from pathlib import Path

def has_invalid_chars(text: str) -> bool:
    """Used for better ProjectNaming"""
    return bool(re.search(r"[^a-zA-Z0-9 _]", text))


def make_random_id() -> float:
    """Generates a unique id"""
    Result = (random.uniform(0, 10000) * random.randint(0, 10000) + random.randint(0, 10000) / random.randint(0, 10000))
    return float(Result)

def get_by_id(items, target_id):
    """Speed run getting the targeted object!"""
    for item in items:
        if item.get("id") == target_id:
            return item
    return None
def clean(v):
    return float(f"{v:.12g}")  # keeps precision, removes float noise





def create_project(name, path: str):
    base = Path(path) / name 

    # create main project folder
    base.mkdir(parents=True, exist_ok=True)

    # structure
    (base / "content").mkdir(exist_ok=True)
    (base / "content" / "assets").mkdir(exist_ok=True)
    (base / "content" / "scripts").mkdir(exist_ok=True)
    (base / "worlds").mkdir(exist_ok=True)

    # files
    (base / "README.md").write_text(f"# {name}\n")

    new_project_path = base

    return str(new_project_path)



class Vector3Editor(QWidget):
    def __init__(self, parent=None, label="None", callback=None):
        super().__init__(parent)

        self.callback = callback
        self.name = label  # store name (position, rotation, etc...)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(f"{label}:")
        layout.addWidget(self.label)

        self.x = QDoubleSpinBox()
        self.y = QDoubleSpinBox()
        self.z = QDoubleSpinBox()

        for s in (self.x, self.y, self.z):
            s.setRange(-999999, 999999)
            s.setDecimals(3)
            s.setSingleStep(0.1)
            s.valueChanged.connect(self._on_change)

        layout.addWidget(QLabel("X"))
        layout.addWidget(self.x)

        layout.addWidget(QLabel("Y"))
        layout.addWidget(self.y)

        layout.addWidget(QLabel("Z"))
        layout.addWidget(self.z)

        self.setLayout(layout)

    def _on_change(self, _):
        if self.callback:
            x, y, z = self.get_value()
            self.callback(
                (clean(x), clean(y), clean(z)),
                self.name
            )

    def set_value(self, x, y, z):
        self.blockSignals(True)
        self.x.setValue(x)
        self.y.setValue(y)
        self.z.setValue(z)
        self.blockSignals(False)

    def get_value(self):
        return (self.x.value(), self.y.value(), self.z.value())