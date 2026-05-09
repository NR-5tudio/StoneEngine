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
import EasyJson as json


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





def create_project(name, path: str, project):
    base = Path(path) / name 

    # create main project folder
    base.mkdir(parents=True, exist_ok=True)

    # structure
    (base / "Game").mkdir(exist_ok=True)
    (base / "Game" / "Content").mkdir(exist_ok=True)

    # files
    (base / "README.md").write_text(f"# {name}\n")
    json.Save(project, f"{base}/{name}.stone")
    new_project_path = base / "Game"
    new_file_path = base / f"{name}.stone"

    return str(new_project_path), str(new_file_path)

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
    def __init__(self, parent=None, label="Vector", callback=None, editor=None):
        super().__init__(parent)

        self.callback = callback
        self.name = label
        self.setAcceptDrops(True)
        self.project_path = ""
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
        self.Binder = ScriptsComboBox(
            root_path=editor.project_path,
            on_bind=self.on_bind_script
        )
        print(f"ProjecPath: {self.project_path}")
        root.addWidget(self.Binder)
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
    def on_bind_script(self, path):
        print(path)

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

    def dropEvent(self, event):
        files = event.mimeData().urls()
        if files:
            file_path = files[0].toLocalFile()
            print(file_path)

    def UpdatePath(self, path):
        self.Binder._root_path = path

from PyQt5.QtWidgets import QToolTip
from PyQt5.QtGui import QFont


def ToolTip(widget, text: str):
    """
    Attaches a styled tooltip to any QWidget.

    Usage:
        Helper.ToolTip(my_widget, f"This is how to use TootTip, Enjoy!")
    """
    widget.setToolTip(text)
    widget.setToolTipDuration(8000)




















import os
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QToolButton, QFrame, QSizePolicy,
    QApplication,
)
from PyQt5.QtCore import Qt, QPoint, QEvent, QFileSystemWatcher, QTimer
from PyQt5.QtGui import QFont


class ScriptsComboBox(QWidget):
    """Searchable .script file picker with an inline X clear button."""

    def __init__(
        self,
        root_path: str = "",
        on_bind=None,
        placeholder: str = "Search script…",
        parent=None,
    ):
        super().__init__(parent)
        self._root_path = root_path
        self._on_bind = on_bind          # callable(path: str | None)
        self._all_files: list[tuple[str, str]] = []   # [(display_name, full_path)]
        self._current_path: str | None = None
        self._popup: QFrame | None = None
        self._suppress_text_change = False

        # QFileSystemWatcher for live file-change detection
        self._watcher = QFileSystemWatcher(self)
        self._watcher.directoryChanged.connect(self._on_directory_changed)
        self._watcher.fileChanged.connect(self._on_file_changed)

        # Debounce timer — coalesces rapid bursts (e.g. bulk rename) into one rescan
        self._rescan_timer = QTimer(self)
        self._rescan_timer.setSingleShot(True)
        self._rescan_timer.setInterval(150)   # ms
        self._rescan_timer.timeout.connect(self._rescan)

        self._build_ui(placeholder)
        self._scan_files()

    # ------------------------------------------------------------------ #
    #  UI construction                                                     #
    # ------------------------------------------------------------------ #

    def _build_ui(self, placeholder: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # --- search / display line edit ---
        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.setMinimumWidth(200)
        self._edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._edit.textChanged.connect(self._on_text_changed)
        self._edit.installEventFilter(self)   # catch focus & key events

        # --- X clear button ---
        self._clear_btn = QToolButton()
        self._clear_btn.setText("✕")
        self._clear_btn.setToolTip("Clear selection")
        self._clear_btn.setFixedSize(24, 24)
        self._clear_btn.setFocusPolicy(Qt.NoFocus)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_selection)

        # style
        self._edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 4px;
                padding: 3px 6px;
                background: #2b2b2b;
                color: #e8e8e8;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #4a9eff;
            }
        """)
        self._clear_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #555;
                border-radius: 4px;
                background: #2b2b2b;
                color: #aaa;
                font-size: 11px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: #3a3a3a;
                color: #ff6b6b;
                border-color: #ff6b6b;
            }
            QToolButton:pressed {
                background: #1e1e1e;
            }
        """)

        # --- refresh button ---
        self._refresh_btn = QToolButton()
        self._refresh_btn.setText("↻")
        self._refresh_btn.setToolTip("Refresh file list")
        self._refresh_btn.setFixedSize(24, 24)
        self._refresh_btn.setFocusPolicy(Qt.NoFocus)
        self._refresh_btn.setCursor(Qt.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.refresh)
        self._refresh_btn.setStyleSheet("""
            QToolButton {
                border: 1px solid #555;
                border-radius: 4px;
                background: #2b2b2b;
                color: #aaa;
                font-size: 14px;
            }
            QToolButton:hover {
                background: #3a3a3a;
                color: #4a9eff;
                border-color: #4a9eff;
            }
            QToolButton:pressed {
                background: #1e1e1e;
            }
        """)

        layout.addWidget(self._edit)
        layout.addWidget(self._refresh_btn)
        layout.addWidget(self._clear_btn)

    # ------------------------------------------------------------------ #
    #  File scanning                                                       #
    # ------------------------------------------------------------------ #

    def _scan_files(self) -> None:
        """Recursively collect all *.script files under root_path and (re)register watcher paths."""
        self._all_files.clear()

        # Unwatch everything first
        if self._watcher.directories():
            self._watcher.removePaths(self._watcher.directories())
        if self._watcher.files():
            self._watcher.removePaths(self._watcher.files())

        if not self._root_path or not os.path.isdir(self._root_path):
            return

        dirs_to_watch: list[str] = []
        for dirpath, subdirs, filenames in os.walk(self._root_path):
            dirs_to_watch.append(dirpath)          # watch every sub-directory
            for fname in filenames:
                if fname.lower().endswith(".script"):
                    full = os.path.join(dirpath, fname)
                    self._all_files.append((fname, full))

        self._all_files.sort(key=lambda x: x[0].lower())

        # Register directories so we detect new/deleted/renamed files
        if dirs_to_watch:
            self._watcher.addPaths(dirs_to_watch)

    # -- watcher callbacks ------------------------------------------------

    def _on_directory_changed(self, _path: str) -> None:
        """A directory was modified (file created / deleted / renamed)."""
        self._rescan_timer.start()   # debounce

    def _on_file_changed(self, _path: str) -> None:
        """A watched file itself was modified (handles edge-case watchers)."""
        self._rescan_timer.start()

    def _rescan(self) -> None:
        """Triggered by the debounce timer — re-scan and refresh the popup."""
        prev_path = self._current_path
        self._scan_files()

        # If the currently selected file was deleted/renamed, auto-clear
        existing_paths = {fp for _, fp in self._all_files}
        if prev_path and prev_path not in existing_paths:
            self._clear_selection()

        # Refresh popup list if it's open right now
        if self._popup and self._popup.isVisible():
            self._filter_popup(self._edit.text())

    def refresh(self) -> None:
        """Manually trigger a re-scan (e.g. after a bulk operation)."""
        self._rescan()

    # ------------------------------------------------------------------ #
    #  Popup                                                               #
    # ------------------------------------------------------------------ #

    def _show_popup(self) -> None:
        if self._popup and self._popup.isVisible():
            self._filter_popup(self._edit.text())
            return

        # Tool + WindowDoesNotAcceptFocus = visible overlay, focus stays on the line-edit
        flags = Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
        self._popup = QFrame(None, flags)
        self._popup.setAttribute(Qt.WA_ShowWithoutActivating)
        self._popup.setFrameShape(QFrame.StyledPanel)
        self._popup.setStyleSheet("""
            QFrame {
                background: #1e1e1e;
                border: 1px solid #4a9eff;
                border-radius: 4px;
            }
        """)

        from PyQt5.QtWidgets import QVBoxLayout
        vlay = QVBoxLayout(self._popup)
        vlay.setContentsMargins(2, 2, 2, 2)
        vlay.setSpacing(0)

        self._list = QListWidget()
        self._list.setFocusPolicy(Qt.NoFocus)   # keep typing focus on the line-edit
        self._list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                color: #e8e8e8;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 5px 8px;
                border-radius: 3px;
            }
            QListWidget::item:hover {
                background: #2a3f5f;
            }
            QListWidget::item:selected {
                background: #1a5fa8;
                color: #ffffff;
            }
        """)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.itemClicked.connect(self._on_item_clicked)

        vlay.addWidget(self._list)

        # position below the line edit
        pos: QPoint = self._edit.mapToGlobal(QPoint(0, self._edit.height() + 2))
        self._popup.move(pos)
        self._popup.resize(self._edit.width() + self._clear_btn.width() + 4, 200)

        self._filter_popup(self._edit.text())
        self._popup.show()

        # App-level filter to detect clicks outside the popup
        QApplication.instance().installEventFilter(self)

    def _hide_popup(self) -> None:
        if self._popup:
            self._popup.hide()
            self._popup.deleteLater()
            self._popup = None

    def _filter_popup(self, query: str) -> None:
        if not self._popup:
            return
        self._list.clear()
        query = query.strip().lower()
        for fname, fpath in self._all_files:
            if query in fname.lower():
                item = QListWidgetItem(fname)
                item.setData(Qt.UserRole, fpath)
                item.setToolTip(fpath)
                self._list.addItem(item)

        if self._list.count() == 0:
            placeholder = QListWidgetItem("No results")
            placeholder.setFlags(Qt.NoItemFlags)
            placeholder.setForeground(Qt.gray)
            self._list.addItem(placeholder)

    # ------------------------------------------------------------------ #
    #  Event handling                                                      #
    # ------------------------------------------------------------------ #

    def eventFilter(self, obj, event):
        # ── App-level mouse press: close popup if clicking outside it ──────
        if event.type() == QEvent.MouseButtonPress and self._popup and self._popup.isVisible():
            # global position of the click
            gpos = event.globalPos()
            popup_rect = self._popup.frameGeometry()
            edit_rect  = self._edit.rect().translated(self._edit.mapToGlobal(QPoint(0, 0)))
            if not popup_rect.contains(gpos) and not edit_rect.contains(gpos):
                self._hide_popup()
                # don't consume the event — let it reach its target widget

        # ── Open popup when edit is clicked / focused ─────────────────────
        if obj is self._edit and event.type() == QEvent.FocusIn:
            self._show_popup()

        # ── Line-edit key handling ─────────────────────────────────────────
        if obj is self._edit and event.type() == QEvent.KeyPress:
            key = event.key()

            if key == Qt.Key_Escape:
                self._hide_popup()
                return True

            elif key in (Qt.Key_Return, Qt.Key_Enter):
                # Pick the first enabled item in the list (regardless of selection)
                if self._popup and self._popup.isVisible():
                    for i in range(self._list.count()):
                        item = self._list.item(i)
                        if item and item.flags() & Qt.ItemIsEnabled:
                            self._on_item_clicked(item)
                            break
                return True

            elif key == Qt.Key_Down and self._popup and self._popup.isVisible():
                # Move visual highlight down without moving focus
                cur = self._list.currentRow()
                nxt = cur + 1 if cur < self._list.count() - 1 else 0
                self._list.setCurrentRow(nxt)
                return True

            elif key == Qt.Key_Up and self._popup and self._popup.isVisible():
                cur = self._list.currentRow()
                prv = cur - 1 if cur > 0 else self._list.count() - 1
                self._list.setCurrentRow(prv)
                return True

        return super().eventFilter(obj, event)

    def _on_text_changed(self, text: str) -> None:
        if self._suppress_text_change:
            return
        self._current_path = None
        self._filter_popup(text)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        if not (item.flags() & Qt.ItemIsEnabled):
            return
        full_path: str = item.data(Qt.UserRole)

        self._current_path = full_path

        self._suppress_text_change = True
        self._edit.setText(full_path)
        self._suppress_text_change = False

        if callable(self._on_bind):
            self._on_bind(full_path)
        self._hide_popup()

    def _clear_selection(self) -> None:
        self._current_path = None
        self._suppress_text_change = True
        self._edit.clear()
        self._suppress_text_change = False

        if callable(self._on_bind):
            self._on_bind(None)


    @property
    def current_path(self) -> str | None:
        """The currently selected full file path, or None."""
        return self._current_path

    def set_root_path(self, path: str) -> None:
        """Change the root directory, rewire the watcher, and re-scan."""
        self._root_path = path
        self._scan_files()   # also re-registers watcher paths
        self._clear_selection()

    def set_value(self, full_path: str | None) -> None:
        """Programmatically set the selected path (triggers on_bind)."""
        if full_path is None:
            self._clear_selection()
            return
        fname = os.path.basename(full_path)
        self._current_path = full_path
        self._suppress_text_change = True
        self._edit.setText(fname)
        self._suppress_text_change = False
        if callable(self._on_bind):
            self._on_bind(full_path)
