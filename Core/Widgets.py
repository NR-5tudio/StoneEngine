from PyQt5.QtWidgets import QListWidget, QDockWidget
from PyQt5.QtCore import Qt



class SceneWidget:
    def __init__(self, editor, world):
        self.editor = editor
        self.world = world

        self.list = QListWidget()

        self.refresh()

        self.list.itemClicked.connect(self.on_click)

        self.dock = QDockWidget("Scene", editor)
        self.dock.setWidget(self.list)

        editor.addDockWidget(Qt.LeftDockWidgetArea, self.dock)

    def refresh(self):
        self.list.clear()
        for obj in self.world["actors"]:
            self.list.addItem(obj["name"])

    def on_click(self, item):
        name = item.text()

        for obj in self.world["actors"]:
            if obj["name"] == name:
                self.world["selected"] = obj
                print("Selected:", name)
                break