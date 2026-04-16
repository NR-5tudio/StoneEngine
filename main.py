import sys
from PyQt5.QtWidgets import QApplication
import Core.Editor as E
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt


def apply_dark_theme(app):
    app.setStyle("Fusion")  # 🔥 important (kills native white UI)

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
    world = {
        "actors": [
            {"name": "Test1", "type": "cube", "pos": [2, 0, 0], "size": [1, 2, 1], "rot": [0, 0, 0]},
            {"name": "Test2", "type": "cube", "pos": [3, 0, 4], "size": [1, 3, 1], "rot": [0, 0, 0]},
            {"name": "Test3", "type": "cube", "pos": [0, 0, 0], "size": [1, 4, 1], "rot": [0, 0, 0]},
        ],
        "selected": None
    }

    editor = E.Editor(world)
    editor.resize(1200, 700)
    editor.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    run()