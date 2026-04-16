from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import QTimer

import Core.Viewport as V
import Core.Widgets as W
import ctypes
from PyQt5.QtCore import Qt


class Editor(QMainWindow):
    def __init__(self, world):
        super().__init__()

        self.world = world
        self.setWindowTitle("Cutie - (0.1)")

        # ---------------- VIEWPORT ----------------
        self.viewport = V.Viewport(world)
        self.setCentralWidget(self.viewport)

        # ---------------- SCENE (from Widgets.py) ----------------
        self.scene = W.SceneWidget(self, world)


        # ---------------- LOOP ----------------
        self.timer = QTimer()
        self.timer.timeout.connect(self.loop)
        self.timer.start(16)

        # Windows dark title bar (best effort)
        try:
            hwnd = self.winId().__int__()
            value = ctypes.c_int(1)

            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                20,
                ctypes.byref(value),
                ctypes.sizeof(value)
            )
        except:
            pass

    def loop(self):
        self.viewport.update()



