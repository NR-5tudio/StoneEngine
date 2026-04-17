from PyQt5.QtWidgets import QListWidget, QDockWidget
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QDockWidget, QListWidget, QPushButton, QHBoxLayout, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt





class SceneWidget:
    def __init__(self, editor, world):
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
        
    def refresh(self):
        self.list.clear()
        for obj in self.world["actors"]:
            self.list.addItem(obj["name"])


    def set_visible(self, value: bool):
        self.dock.setVisible(value)
    def on_click(self, item):
        name = item.text()

        for obj in self.world["actors"]:
            if obj["name"] == name:
                self.world["selected"] = obj

                # Selected
                on_select(self.editor.prop_window, obj)
                
                
                
                break




def on_select(prop, selected_obj):
    prop.name.setText(f"{selected_obj}")





class Properties:
    def __init__(self, editor, world):
        self.editor = editor
        self.world = world

        self.list = QListWidget()




        self.refresh()

        self.list.itemClicked.connect(self.on_click)

        self.dock = QDockWidget("Properties", editor)
        self.dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )
        
        self.name = QLabel()
        
        

        lay = QVBoxLayout()
        container = QWidget()
        
        lay.addWidget(self.name)
        container.setLayout(lay)
        self.dock.setWidget(container)
        editor.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        
    def refresh(self):
        self.list.clear()


        for obj in self.world["actors"]:
            self.list.addItem(obj["name"])


    def set_visible(self, value: bool):
        self.dock.setVisible(value)
    def on_click(self, item):
        self.world["selected"]