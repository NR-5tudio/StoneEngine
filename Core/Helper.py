import re
import random
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QHBoxLayout, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from pathlib import Path
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QDoubleSpinBox,
    QApplication
)
import mouse

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
    (base / "Game").mkdir(exist_ok=True)
    (base / "Game" / "Content").mkdir(exist_ok=True)
    (base / "worlds").mkdir(exist_ok=True)

    # files
    (base / "README.md").write_text(f"# {name}\n")

    new_project_path = base / "Game"

    return str(new_project_path)

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDoubleSpinBox, QApplication


class _DragSpinBox(QDoubleSpinBox):
    def __init__(self):
        super().__init__()

        self.setDecimals(3)
        self.setRange(-1e12, 1e12)
        self.setSingleStep(0.1)
        self.setButtonSymbols(QDoubleSpinBox.NoButtons)

        self._dragging = False
        self._lock_point = None
        self._warping = False

        # Snapping accumulators
        self._drag_start_value = 0.0
        self._accum_dy = 0               # total vertical movement in pixels
        self._drag_sensitivity = 10      # pixels per 0.1 step

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.ClickFocus)

    # -------------------------
    # PUBLIC DRAG API
    # -------------------------
    def start_drag(self):
        if self._dragging:
            return
        self._dragging = True

        self._drag_start_value = self.value()
        self._accum_dy = 0

        # Lock to center of widget
        self._lock_point = self.mapToGlobal(self.rect().center())

        self.grabMouse()
        QApplication.setOverrideCursor(Qt.BlankCursor)
        QCursor.setPos(self._lock_point)

    def stop_drag(self):
        if not self._dragging:
            return
        self._dragging = False
        self._lock_point = None

        self.releaseMouse()
        QApplication.restoreOverrideCursor()

    # -------------------------
    # EVENTS
    # -------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_drag()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and not self._warping:
            current = event.globalPos()

            # Movement from lock point (positive dy = move up → increase value)
            dy = self._lock_point.y() - current.y()
            self._accum_dy += dy

            # Compute total steps from start (rounded to nearest integer)
            steps = round(self._accum_dy / self._drag_sensitivity)
            new_value = self._drag_start_value + steps * self.singleStep()
            new_value = max(self.minimum(), min(self.maximum(), new_value))

            if new_value != self.value():
                self.setValue(new_value)

            # Warp mouse back to lock point
            self._warping = True
            QCursor.setPos(self._lock_point)
            self._warping = False

            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self.stop_drag()
            event.accept()
            return
        super().mouseReleaseEvent(event)

class Vector3Editor(QWidget):
    def __init__(self, parent=None, label="Vector", callback=None):
        super().__init__(parent)

        self.callback = callback
        self.name = label

        root = QVBoxLayout()
        root.setContentsMargins(6, 4, 6, 4)
        root.setSpacing(4)

        # title
        title = QLabel(label)
        title.setStyleSheet("""
            color:#cfcfcf;
            font-weight:bold;
            font-size:11px;
        """)
        root.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(4)

        self.x = _DragSpinBox()
        self.y = _DragSpinBox()
        self.z = _DragSpinBox()

        for s in (self.x, self.y, self.z):
            s.valueChanged.connect(self._on_change)

        self._axis(row, "X", self.x, "#d14")
        self._axis(row, "Y", self.y, "#4a4")
        self._axis(row, "Z", self.z, "#48f")

        root.addLayout(row)
        self.setLayout(root)

        self.setStyleSheet("""
            QWidget {
                background: #252526;
            }
        """)

    # -------------------------
    # axis row (UE style)
    # -------------------------
    def _axis(self, layout, name, spin, color):
        container = QHBoxLayout()
        container.setSpacing(3)

        lbl = QLabel(name)
        lbl.setFixedWidth(12)
        lbl.setStyleSheet(f"color:{color}; font-weight:bold;")

        hold = QPushButton("≡")
        hold.setFixedWidth(18)

        hold.setStyleSheet("""
            QPushButton {
                background:#2a2a2a;
                color:#aaa;
                border:1px solid #444;
            }
            QPushButton:pressed {
                background:#3a3a3a;
            }
        """)

        hold.pressed.connect(spin.start_drag)
        hold.released.connect(spin.stop_drag)

        container.addWidget(lbl)
        container.addWidget(hold)
        container.addWidget(spin)

        w = QWidget()
        w.setLayout(container)

        layout.addWidget(w)

    # -------------------------
    # callback
    # -------------------------
    def _on_change(self):
        if self.callback:
            self.callback(
                (
                    clean(self.x.value()),
                    clean(self.y.value()),
                    clean(self.z.value())
                ),
                self.name
            )

    # -------------------------
    # API
    # -------------------------
    def set_value(self, x, y, z):
        self.blockSignals(True)
        self.x.setValue(x)
        self.y.setValue(y)
        self.z.setValue(z)
        self.blockSignals(False)

    def get_value(self):
        return (
            self.x.value(),
            self.y.value(),
            self.z.value()
        )
    

from PyQt5.QtWidgets import QToolTip
from PyQt5.QtGui import QFont


def ToolTip(widget, text: str):
    """
    Attaches a styled tooltip to any QWidget.

    Usage:
        Helper.ToolTip(my_widget, f"FileName: {name}\nPath: {path}")
    """
    widget.setToolTip(text)
    widget.setToolTipDuration(8000)