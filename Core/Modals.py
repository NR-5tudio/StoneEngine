from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox,
    QScrollArea, QWidget, QPushButton, QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt
import ctypes
import Core.Helper as helpers
# validation check (call this when submitting)

def AddObjectModal(parent=None):
    dialog = QDialog(parent.editor)


    dialog.setWindowTitle("Adding an object!")

    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)

    scroll = QScrollArea(dialog)
    scroll.setWidgetResizable(True)

    panel = QWidget()
    layout = QVBoxLayout()

    # ===== UI CONTENT =====
    layout.addWidget(QLabel("Create Object"))

    name_input = QLineEdit()
    name_input.setPlaceholderText("Object name")
    layout.addWidget(name_input)

    code_name_input = QLineEdit()
    code_name_input.setPlaceholderText("Code name (Don't reuse code names.)")
    code_name_input.setToolTip("The name you'll use when you code\n(Don't use code names that you used already)")
    layout.addWidget(code_name_input)
    type_combo = QComboBox()
    type_combo.addItems(["Cube", "Custom"])
    layout.addWidget(type_combo)
    
    CanScriptBox = QCheckBox("Can Be Scripted")
    layout.addWidget(CanScriptBox)


    def is_valid():
        text = code_name_input.text().strip()
        if not text:
            code_name_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid red;
                }
            """)
            return False
        else:
            code_name_input.setStyleSheet("")  # reset
            return True

    def Create():
        if not is_valid():
            return
        parent.editor.world["actors"].append(
            {
                "id": helpers.make_random_id(),
                "code_name": code_name_input.text(),
                "name": name_input.text(),
                "type": str(type_combo.currentText()).lower(),
                "pos":  [0, 0, 0],
                "size": [1, 1, 1],
                "rot":  [0, 0, 0],
                "color": (255, 255, 255, 255), 
            }
        )
        parent.refresh()
        dialog.close()






    CreateButton = QPushButton("Add Object")
    CreateButton.clicked.connect(Create)
    layout.addWidget(CreateButton)




    panel.setLayout(layout)
    scroll.setWidget(panel)

    # dialog layout
    main_layout = QVBoxLayout()
    main_layout.addWidget(scroll)
    dialog.setLayout(main_layout)

    try:
        hwnd = dialog.winId().__int__()
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            20,
            ctypes.byref(value),
            ctypes.sizeof(value)
        )
    except:
        pass

    dialog.exec_()


from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QApplication
)
import sys


def InputTextDialog(label="Label", message="Message",
                    Exitable=False, DoneName="Done"):

    class _Dialog(QDialog):
        def __init__(self):
            super().__init__()

            self.result_text = None
            self.setWindowTitle(label)

            layout = QVBoxLayout()

            self.msg = QLabel(message)
            layout.addWidget(self.msg)

            self.input = QLineEdit()
            layout.addWidget(self.input)

            btn_layout = QHBoxLayout()

            self.done_btn = QPushButton(DoneName)
            self.cancel_btn = QPushButton("Cancel")

            btn_layout.addWidget(self.done_btn)
            if Exitable:
                btn_layout.addWidget(self.cancel_btn)

            layout.addLayout(btn_layout)
            self.setLayout(layout)

            self.done_btn.clicked.connect(self.finish)
            self.input.returnPressed.connect(self.finish)

            if Exitable:
                self.cancel_btn.clicked.connect(self.reject)

            if not Exitable:
                self.setWindowFlags(self.windowFlags() & ~self.windowFlags())

        def finish(self):
            text = self.input.text().strip()
            if text == "" and not Exitable:
                return
            if text == "" and Exitable:
                self.result_text = None
            else:
                self.result_text = text
            self.accept()

        def closeEvent(self, event):
            if not Exitable and not self.result_text:
                event.ignore()
            else:
                event.accept()

    app = QApplication.instance()
    created_app = False

    if not app:
        app = QApplication(sys.argv)
        created_app = True

    dlg = _Dialog()
    dlg.exec_()

    result = dlg.result_text

    if created_app:
        app.quit()

    return result