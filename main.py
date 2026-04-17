import sys
from PyQt5.QtWidgets import QApplication
import Core.Editor as E
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

import EasyJson as json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget
import sys





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

    app.setStyleSheet("""
        QMainWindow {
            background-color: #1a1a1a;
        }
        QDockWidget {
            background-color: #1a1a1a;
            border: 1px solid #2a2a2a;
        }
        QDockWidget::title {
            background-color: #222222;
            color: white;
            padding: 4px;
        }
        QListWidget {
            background-color: #151515;
            color: white;
            border: none;
        }
        QWidget {
            background-color: #1a1a1a;
        }
        QAbstractItemView {
            background-color: #151515;
            color: white;
            selection-background-color: #444444;
        }
    """)

def run():
    app = QApplication(sys.argv)
    apply_dark_theme(app)
    app.setFont(QFont("Arial", 13))

    world = {
        "actors": [
            {
                "id": "1823",
                "name": "A",
                "type": "cube",
                "pos":  [0, 0, 0],
                "size": [1, 2, 1],
                "rot":  [0, 0, 0],
                "color": (180, 140, 100, 255), 
            },
            {
                "id": "1253",
                "name": "B",
                "type": "cube",
                "pos":  [2, 0, 0],
                "size": [1, 4, 1],
                "rot":  [0, 30, 0],
                "color": (100, 160, 220, 255),  
            },
            {
                "id": "1233",
                "name": "C",
                "type": "cube",
                "pos":  [4, 0, 0],
                "size": [1, 8, 1],
                "rot":  [0, 0, 0],
                "color": (120, 200, 120, 255),  
            },
        ],
        "selected": None
    }

    editor = E.Editor(world)
    editor.resize(1200, 700)
    editor.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()