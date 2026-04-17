from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMainWindow, QAction
import Core.Viewport as V
import Core.Widgets as W
import ctypes
from PyQt5.QtCore import Qt
import base64
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QApplication, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt
import ctypes
from PyQt5.QtWidgets import QFileDialog
import os
import Core.Helper as helper

class WelcomeWindow(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.setStyleSheet("""
            background-color: rgba(10, 10, 10, 240);
            color: white;
            font-size: 20px;
        """)

        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Welcome to CutieEngine")
        title.setAlignment(Qt.AlignCenter)

        self.pname = QLineEdit()
        self.pname.setStyleSheet("""
            QPushButton {
                background-color: #ff4fd8;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff7ae6;
            }
        """)
        self.pname.setPlaceholderText("Project name...")



        self.ppath = QLineEdit()
        self.ppath.setStyleSheet("""
            QPushButton {
                background-color: #ff4fd8;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff7ae6;
            }
        """)
        self.ppath.setPlaceholderText("Project path...")



        createbtn = QPushButton("Create project")
        createbtn.setStyleSheet("""
            QPushButton {
                background-color: #ff4fd8;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff7ae6;
            }
        """)
        createbtn.clicked.connect(self.enter_editor)



        loadbtn = QPushButton("Load project")
        loadbtn.setStyleSheet("""
            QPushButton {
                background-color: #ff4fd8;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff7ae6;
            }
        """)
        loadbtn.clicked.connect(self.enter_editor)
        


        cancelbtn = QPushButton("Cancel")
        cancelbtn.setStyleSheet("""
            QPushButton {
                background-color: #ff4fd8;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff7ae6;
            }
        """)
        cancelbtn.clicked.connect(QApplication.quit)

        self.folder_path = ""
        
        ppathpicker = QPushButton("Pick")
        ppathpicker.setStyleSheet("""
            QPushButton {
                background-color: #ff4fd8;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
            QPushButton:hover {
                background-color: #ff7ae6;
            }
        """)
        ppathpicker.clicked.connect(self.set_path)


        self.ermsg = QLabel("Lets setup your project OwO")
        

        self.path = QHBoxLayout()
        self.path.addWidget(self.ppath)
        self.path.addWidget(ppathpicker)

        creation = QHBoxLayout()
        creation.addWidget(createbtn)
        creation.addWidget(loadbtn)

        layout.addWidget(title)
        layout.addWidget(self.pname)
        layout.addLayout(self.path)

        layout.addLayout(creation)

        layout.addWidget(cancelbtn)
        
        layout.addWidget(self.ermsg)

        self.setLayout(layout)

    def enter_editor(self):
        error = False
        print(f"{self.ppath.text()}")
        if (not os.path.exists(self.ppath.text())):
            self.ermsg.setText("Pick a real folder o-o")
            error = True
        if (self.ppath.text() == ""):
          self.ermsg.setText("You have to pick a folder first :3")
          error = True
        if (helper.has_invalid_chars(f"{self.pname.text()}")):
            self.ermsg.setText("Amm, your project name should only have:\n(0-9, a-z, A-Z, '_', Space)")
            error = True
        if (self.pname.text() == ""):
            self.ermsg.setText("Will you pick a name :3 ?")
            error = True

        if error == True: return    
        self.hide()
        self.parent().show_editor()

        return



    def set_path(self):
        self.folder_path = QFileDialog.getExistingDirectory(
            self,
            "Open Folder",
            ""
        )
        if self.folder_path:
            self.ppath.setText(self.folder_path)
