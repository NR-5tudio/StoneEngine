from PyQt5.QtWidgets import QListWidget, QDockWidget
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QMenu, QAction, QDockWidget, QListWidgetItem, QListWidget, QPushButton, QHBoxLayout, QLabel, QWidget, QVBoxLayout, QScrollArea
from PyQt5.QtCore import Qt
import Core.Modals as modals
import Core.Helper as helper


class SceneWidget:
    def __init__(self, editor, world: dict):
        self.editor = editor
        self.world = world

        self.list = QListWidget()
        

        self.refresh()

        self.list.itemClicked.connect(self.on_click)

        self.dock = QDockWidget("Scene", editor)
        self.dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )
        
        AddButton = QPushButton("Add")
        AddButton.clicked.connect(lambda: modals.AddObjectModal(self))
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
        self.editor = editor
        self.world = world
        self.dock = QDockWidget("Properties", editor)
        self.dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )

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



import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QTreeView, QFileSystemModel,
    QListView, QSplitter, QHBoxLayout,
    QDockWidget, QMenu, QMessageBox
)
from PyQt5.QtCore import Qt, QSize, QDir




class AssetBrowser(QWidget):
    def __init__(self, editor, root_path):
        super().__init__()

        self.editor = editor

        self.dock = QDockWidget("Browser", editor)
        self.dock.setWidget(self) 
        self.dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )

        self._root_path = None
        self.model = QFileSystemModel()

        # UI
        layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeView()
        self.grid = QListView()

        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(64, 64))
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setSpacing(10)

        self.tree.clicked.connect(self.on_tree_click)
        self.grid.doubleClicked.connect(self.on_double_click)
        self.grid.setContextMenuPolicy(Qt.CustomContextMenu)
        self.grid.customContextMenuRequested.connect(self.on_right_click)

        splitter.addWidget(self.tree)
        splitter.addWidget(self.grid)
        splitter.setSizes([250, 700])

        layout.addWidget(splitter)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(root_path))
        self.tree.hideColumn(1)  # Size
        self.tree.hideColumn(2)  # Type
        self.tree.hideColumn(3)

        self.set_root(root_path)
        self.grid.setIconSize(QSize(64, 64))
        self.grid.setUniformItemSizes(True)
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setGridSize(QSize(80, 80))
        self.grid.setWordWrap(True)
        editor.addDockWidget(Qt.BottomDockWidgetArea, self.dock)
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

            if file_path.endswith(".py"):
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

    def on_tree_click(self, index):
        path = self.model.filePath(index)
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
    def on_right_click(self, pos):
        index = self.grid.indexAt(pos)
        menu = QMenu(self)

        if not index.isValid():
            create_action = menu.addAction("New Folder")
            script_action = menu.addAction("New Script")
            import_action = menu.addAction("Import File")

            action = menu.exec(self.grid.viewport().mapToGlobal(pos))

            if action == create_action:
                print("Create new folder")

            elif action == script_action:
                print("Create new script")

            elif action == import_action:
                print("Import file")

            return  # stop here

        path = self.model.filePath(index)

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
                if self.model.isDir(index):
                    QDir(path).rmdir(path)
                else:
                    os.remove(path)

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Delete Failed",
                    f"Could not delete:\n{name}\n\nError: {str(e)}"
                )
    def is_inside_root(self, path: str) -> bool:
        if not self._root_path:
            return False

        path = os.path.abspath(path)
        root = os.path.abspath(self._root_path)

        return path.startswith(root)
    