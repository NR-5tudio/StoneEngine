import sys
import math
import time

from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from OpenGL.GL import *
from OpenGL.GLU import *

import Core.RenderEngine as Render


class Viewport(QOpenGLWidget):
    def __init__(self, world):
        super().__init__()

        self.world = world

        self.last_time = time.time()
        self.delta_time = 0.0

        self.pos = [0.0, 0.0, 5.0]
        self.yaw = 0.0
        self.pitch = 0.0

        self.speed = 1.0
        self.keys = set()

        self.fov = 90
        self.move_mode = False

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

    # ---------------- INPUT ----------------

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self.move_mode = True
            self.setCursor(Qt.BlankCursor)
            self.lock_mouse()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.RightButton:
            self.move_mode = False
            self.setCursor(Qt.ArrowCursor)
            self.keys.clear()

    def keyPressEvent(self, e):
        if self.move_mode:
            self.keys.add(e.key())

    def keyReleaseEvent(self, e):
        self.keys.discard(e.key())

    def mouseMoveEvent(self, e):
        if not self.move_mode:
            return

        center = self.rect().center()

        dx = e.x() - center.x()
        dy = e.y() - center.y()

        self.yaw += dx * 0.2
        self.pitch += dy * 0.2
        self.pitch = max(-89, min(89, self.pitch))

        self.lock_mouse()

    def lock_mouse(self):
        QCursor.setPos(self.mapToGlobal(self.rect().center()))

    # ---------------- OPENGL ----------------

    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        glClearColor(0.1, 0.1, 0.1, 1)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(self.fov, w / max(h, 1), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    # ---------------- CAMERA ----------------

    def update_camera(self, dt):
        if not self.move_mode:
            return

        rad = math.radians(self.yaw)

        forward = [math.sin(rad), 0, math.cos(rad)]
        right = [math.cos(rad), 0, -math.sin(rad)]

        self.speed = 3.0 if Qt.Key_Shift in self.keys else 1.0

        if Qt.Key_W in self.keys:
            self.pos[0] += forward[0] * self.speed * dt
            self.pos[2] -= forward[2] * self.speed * dt

        if Qt.Key_S in self.keys:
            self.pos[0] -= forward[0] * self.speed * dt
            self.pos[2] += forward[2] * self.speed * dt

        if Qt.Key_A in self.keys:
            self.pos[0] -= right[0] * self.speed * dt
            self.pos[2] += right[2] * self.speed * dt

        if Qt.Key_D in self.keys:
            self.pos[0] += right[0] * self.speed * dt
            self.pos[2] -= right[2] * self.speed * dt

        if Qt.Key_Space in self.keys:
            self.pos[1] += self.speed * dt

        if Qt.Key_Control in self.keys:
            self.pos[1] -= self.speed * dt

    # Render
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        now = time.time()
        self.delta_time = now - self.last_time
        self.last_time = now

        self.update_camera(self.delta_time)

        glLoadIdentity()

        glRotatef(self.pitch, 1, 0, 0)
        glRotatef(self.yaw, 0, 1, 0)
        glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])

        for obj in self.world["actors"]:
            if obj["type"] == "cube":
                Render.draw_cube(obj["pos"], obj["size"], obj["rot"])

                if self.world.get("selected") == obj:
                    Render.draw_cube_wires(obj["pos"], obj["size"], obj["rot"])
        Render.draw_world_grid()