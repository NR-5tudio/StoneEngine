import sys
from PyQt5.QtWidgets import QApplication
import Core.Editor as E
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import EasyJson as json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget
import sys
import Core.StyleLoader as style




def apply_dark_theme(app):
    app.setStyle("Fusion") 

    palette = QPalette()

    # main backgrounds
    palette.setColor(QPalette.Window, QColor(25, 25, 25))
    palette.setColor(QPalette.Base, QColor(18, 18, 18))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))

    # text
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.WindowText, Qt.white)

    # buttons
    palette.setColor(QPalette.Button, QColor(40, 40, 40))
    palette.setColor(QPalette.ButtonText, Qt.white)

    # highlights
    palette.setColor(QPalette.Highlight, QColor(80, 80, 80))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)

    app.setStyleSheet(style.generate_qss("UserSettings/Style.json"))

def run():
    app = QApplication(sys.argv)    
    apply_dark_theme(app)
    app.setFont(QFont("Arial", 13))

    world = {
        "actors": [
            
        ],

        "scripts":[

        ],

        "selected": None
    }

    editor = E.Editor(world)
    editor.resize(1200, 700)
    editor.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()