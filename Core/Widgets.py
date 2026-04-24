from PyQt5.QtWidgets import QListWidget, QDockWidget
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QMenu, QFileDialog, QAction, QDockWidget, QListWidgetItem, QListWidget, QPushButton, QHBoxLayout, QLabel, QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt, QModelIndex 
from PyQt5.QtGui import QIcon, QPixmap
import Core.Modals as modals
import Core.Helper as helper
import shutil
from send2trash import send2trash

class SceneWidget:
    def __init__(self, editor, world: dict):
        self.editor = editor
        self.world = world

        self.list = QListWidget()
        

        self.refresh()

        self.list.itemClicked.connect(self.on_click)

        self.dock = QDockWidget("Scene", editor)
        
        AddButton = QPushButton("Add")
        AddButton.clicked.connect(lambda: modals.AddObjectModal(self))
        helper.ToolTip(AddButton, "Add an object")
        DeleteButton = QPushButton("Delete")
        Vlayout = QVBoxLayout()
        Hlayout = QHBoxLayout()

        Hlayout.addWidget(AddButton)
        Hlayout.addWidget(DeleteButton)
        Vlayout.addLayout(Hlayout)
        Vlayout.addWidget(self.list)

        container = QWidget()
        container.setLayout(Vlayout)
        self.dock.setWidget(container)

        editor.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.show_menu)

    def refresh(self):
        self.list.clear()
        for obj in self.world["actors"]:
            item = QListWidgetItem(obj["name"])  # show name
            item.setData(Qt.UserRole, obj["id"])  # store id (hidden)
            self.list.addItem(item)

    def show_menu(self, pos):
        item = self.list.itemAt(pos)

        if item is None:
            return  # clicked empty space

        menu = QMenu()

        UnSelect = menu.addAction("UnSelect")
        Delete = menu.addAction("Delete")

        action = menu.exec_(self.list.mapToGlobal(pos))

        actor_id = item.data(Qt.UserRole)
        if action == Delete:
            self.list.takeItem(self.list.row(item))
            id = actor_id
            old = list(self.world["actors"])
            new = []
            print("Searching")
            for i in old:
                if (i["id"] != id):
                    new.append(i)
                    print(f"Found: {i}")
            self.world["actors"] = new
            print("Done")

    def set_visible(self, value: bool):
        self.dock.setVisible(value)


    def on_click(self, item):
        obj_id = item.data(Qt.UserRole)  # get id instead of name

        for obj in self.world["actors"]:
            if obj["id"] == obj_id:
                self.world["selected"] = obj

                # Selected
                self.editor.prop_window.on_select(obj)
                break








class Properties:
    def __init__(self, editor, world):
        self.obj_id = None
        self.editor = editor
        self.world = world
        self.dock = QDockWidget("Properties", editor)

        # root widget
        container = QWidget()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        self.lay = QVBoxLayout(content)
        self.lay.setAlignment(Qt.AlignTop)

        self.name = QLabel()
        self.lay.addWidget(self.name)
        self.code_name = QLabel()
        self.lay.addWidget(self.code_name)

        self.pos = helper.Vector3Editor(label="Position", callback=self.update_v3_object)
        self.lay.addWidget(self.pos)

        self.rot = helper.Vector3Editor(label="Rotation", callback=self.update_v3_object)
        self.lay.addWidget(self.rot)

        self.size = helper.Vector3Editor(label="Size", callback=self.update_v3_object)
        self.lay.addWidget(self.size)

        scroll.setWidget(content)

        # final layout wrapper
        root_layout = QVBoxLayout(container)
        root_layout.addWidget(scroll)

        self.dock.setWidget(container)
        editor.addDockWidget(Qt.RightDockWidgetArea, self.dock)
    def set_visible(self, value: bool):
        self.dock.setVisible(value)
    def on_select(self, selected_obj):
        self.obj_id = selected_obj["id"]
        self.name.setText(f"Object Name: {selected_obj["name"]}")
        self.code_name.setText(f"Code Name: {selected_obj["code_name"]}")
        self.pos.set_value(selected_obj["pos"][0], selected_obj["pos"][1], selected_obj["pos"][2])
        self.rot.set_value(selected_obj["rot"][0], selected_obj["rot"][1], selected_obj["rot"][2])
        self.size.set_value(selected_obj["size"][0], selected_obj["size"][1], selected_obj["size"][2])

    def update_v3_object(self, v3, name):
        if not self.obj_id: return
        Actors = self.world["actors"]
        Object = helper.get_by_id(Actors, self.obj_id)
        if name == "Rotation": Object["rot"] = [v3[0], v3[1], v3[2]]
        elif name == "Position": Object["pos"] = [v3[0], v3[1], v3[2]]
        elif name == "Size": Object["size"] = [v3[0], v3[1], v3[2]]
        else:
            print(f"Unknowen name: '{name}'")



import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QTreeView, QFileSystemModel,
    QListView, QSplitter, QHBoxLayout,
    QDockWidget, QMenu, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QDir

class CustomFileSystemModel(QFileSystemModel):
    def __init__(self, icon_map=None, parent=None):
        super().__init__(parent)

        base = os.path.dirname(__file__)

        self.icon_map = icon_map or {
            ".script": QIcon("Core/Icons/script.png"),
            ".obj": QIcon("Core/Icons/model.png"),
            ".fbx": QIcon("Core/Icons/model.png"),
            ".wave": QIcon("Core/Icons/wave.png"),
            ".mp3": QIcon("Core/Icons/wave.png"),
            "folder": QIcon("Core/Icons/folder.png"),
        }

        self._thumb_cache = {}  # important for performance

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None

        file_path = self.filePath(index)

        # ---------------- ICONS ----------------
        if role == Qt.DecorationRole:

            # folder icon
            if self.isDir(index):
                return self.icon_map["folder"]

            ext = os.path.splitext(file_path)[1].lower()

            # PNG thumbnail
            if ext == ".png":
                if file_path in self._thumb_cache:
                    return self._thumb_cache[file_path]

                pix = QPixmap(file_path)

                if not pix.isNull():
                    icon = QIcon(pix.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    self._thumb_cache[file_path] = icon
                    return icon

            # normal icons
            if ext in self.icon_map:
                return self.icon_map[ext]
        if role == Qt.ToolTipRole:
            name = self.fileName(index)
            path = file_path
            return f"FileName: {name}\nPath: {path}"
        return super().data(index, role)

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class WrappingIconDelegate(QStyledItemDelegate):
    """Delegate that respects word-wrapped text and icons for grid view."""
    def sizeHint(self, option, index):
        # Get the default size hint
        default = super().sizeHint(option, index)
        text = index.data(Qt.DisplayRole)
        if not text:
            return default

        # Get icon size from the view (or fallback to 64x64)
        view = option.widget
        if view:
            icon_size = view.iconSize()
        else:
            icon_size = QSize(64, 64)

        # Measure text height with wrapping
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setPlainText(text)
        # Width available for text = icon width + some margin
        text_width = icon_size.width() + 12
        doc.setTextWidth(text_width)
        text_height = doc.size().height()

        # Total cell size = icon height + text height + vertical spacing
        total_height = int(icon_size.height() + text_height + 12)
        total_width = int(icon_size.width() + 16)
        return QSize(total_width, total_height)


class AssetBrowser(QWidget):
    def __init__(self, editor, root_path):
        super().__init__()

        self.editor = editor

        self.dock = QDockWidget("Browser", editor)
        self.dock.setWidget(self) 

        self._root_path = None
        self.model = CustomFileSystemModel()  # assume this exists

        # UI
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeView()
        self.grid = QListView()

        # Grid view configuration
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(64, 64))
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setSpacing(12)
        self.grid.setWordWrap(True)
        self.grid.setTextElideMode(Qt.ElideNone)   # never cut text, always wrap
        self.grid.setItemDelegate(WrappingIconDelegate(self.grid))

        # Remove the problematic lines:
        # self.grid.setUniformItemSizes(True)
        # self.grid.setGridSize(QSize(80, 80))

        self.tree.clicked.connect(self.on_tree_click)
        self.grid.doubleClicked.connect(self.on_double_click)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.on_right_click)

        splitter.addWidget(self.tree)
        splitter.addWidget(self.grid)
        splitter.setSizes([250, 700])

        layout.addWidget(splitter)

        # Model setup
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path))
        self.tree.hideColumn(1)  # Size
        self.tree.hideColumn(2)  # Type
        self.tree.hideColumn(3)  # Date modified (if any)

        self.set_root(root_path)

        editor.addDockWidget(Qt.BottomDockWidgetArea, self.dock)

    # Your existing methods: on_tree_click, on_double_click, on_right_click, set_root, etc.
    # They remain unchanged.
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        source = self.sourceModel()
        file_path = source.filePath(index)

        # only modify "Type" column (usually column 2)
        if role == Qt.DisplayRole and index.column() == 2:

            if os.path.isdir(file_path):
                return "Folder"

            file_path = file_path.lower()

            if file_path.endswith(".script"):
                return "Script"
            if file_path.endswith(".obj") or file_path.endswith(".fbx"):
                return "3D Model"
            if file_path.endswith(".png") or file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
                return "Image"

            return "File"

        return super().data(index, role)
    def set_root(self, path):
        path = os.path.abspath(path)

        self._root_path = path
        self.model.setRootPath(path)

        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(path))

        self.grid.setModel(self.model)
        self.grid.setRootIndex(self.model.index(path))
        path = f"{path}/Content"
        self.set_folder(path)

    def on_tree_click(self, index):
        path = self.model.filePath(index)
        name = self.model.fileName(index)

        if self.model.isDir(index):
            self.set_folder(path)
    def set_folder(self, path):
        path = os.path.abspath(path)
        if path.startswith(self._root_path):
            self.grid.setRootIndex(self.model.index(path))

    def on_double_click(self, index):
        path = self.model.filePath(index)
        if self.model.isDir(index):
            self.set_folder(path)
        else:

            # LOAD SCRIPTS
            if path.endswith(".script"):
                self.editor.Coder.open_file(path)
        

    def on_right_click(self, pos):
        index = self.grid.indexAt(pos)
        menu = QMenu(self)

        if not index.isValid():
            create_action = menu.addAction("New Folder")
            script_action = menu.addAction("New Script")
            import_action = menu.addAction("Import File")
            path = self.model.rootPath()
            new_folder_path = os.path.join(path, "New Folder")
            action = menu.exec(self.grid.viewport().mapToGlobal(pos))

            if action == create_action:
                self.create_folder()

            elif action == script_action:
                self.create_script()

            elif action == import_action:
                self.import_file()

            return  # stop here

        path = os.path.abspath(self.model.filePath(index))

        open_action = menu.addAction("Open")
        reveal_action = menu.addAction("Reveal Path")
        delete_action = menu.addAction("Delete")

        action = menu.exec(self.grid.viewport().mapToGlobal(pos))

        if action == open_action:
            self.on_double_click(index)

        elif action == reveal_action:
            QMessageBox.information(self, "Path", path)

        elif action == delete_action:
            if not self.is_inside_root(path):
                return

            name = os.path.basename(path)

            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                f"Are you sure you want to delete '{name}'?\n\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            try: 
                print("Deleting:", path)
                send2trash(path)
            except Exception as e: QMessageBox.critical(self, "Delete Failed", f"Could not delete:\n{name}\n\nError: {str(e)}")
    
    def is_inside_root(self, path: str) -> bool:
        if not self._root_path:
            return False

        path = os.path.abspath(path)
        root = os.path.abspath(self._root_path)

        return path.startswith(root)
    def create_folder(self):
        path = self.model.filePath(self.grid.rootIndex())
        new_folder_path = os.path.join(path, "New Folder")

        i = 1
        while os.path.exists(new_folder_path):
            new_folder_path = os.path.join(path, f"New Folder {i}")
            i += 1

        os.makedirs(new_folder_path)
        print("Folder created:", new_folder_path)

        index = self.grid.rootIndex()
        self.grid.setRootIndex(QModelIndex())
        self.grid.setRootIndex(index)


    def create_script(self):
        path = self.model.filePath(self.grid.rootIndex())
        new_script_path = os.path.join(path, "NewScript.script")

        i = 1
        while os.path.exists(new_script_path):
            new_script_path = os.path.join(path, f"new_script_{i}.script")
            i += 1

        with open(new_script_path, "w") as f:
            f.write("# new script\n")

        print("Script created:", new_script_path)

        index = self.grid.rootIndex()
        self.grid.setRootIndex(QModelIndex())
        self.grid.setRootIndex(index)


    def import_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Import File")

        if not file_path:
            return
        current_path = self.model.filePath(self.grid.rootIndex())
        dest = os.path.join(current_path, os.path.basename(file_path))
        shutil.copy(file_path, dest)

        print("Imported:", dest)