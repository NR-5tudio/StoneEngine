import sys
import math
import time
import numpy as np

from PyQt5.QtWidgets import QOpenGLWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor

from OpenGL.GL import *

import Core.RenderEngine as Render


VERTEX_SHADER = """
#version 330 core
layout (location = 0) in vec3 aPos;

uniform mat4 projection;
uniform mat4 view;
uniform mat4 model;

void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core
out vec4 FragColor;

uniform vec3 color;

void main()
{
    FragColor = vec4(color, 1.0);
}
"""


def create_shader(type, src):
    s = glCreateShader(type)
    glShaderSource(s, src)
    glCompileShader(s)
    if not glGetShaderiv(s, GL_COMPILE_STATUS):
        raise RuntimeError(glGetShaderInfoLog(s).decode())
    return s


def create_program(vs, fs):
    vs = create_shader(GL_VERTEX_SHADER, vs)
    fs = create_shader(GL_FRAGMENT_SHADER, fs)

    p = glCreateProgram()
    glAttachShader(p, vs)
    glAttachShader(p, fs)
    glLinkProgram(p)

    if not glGetProgramiv(p, GL_LINK_STATUS):
        raise RuntimeError(glGetProgramInfoLog(p).decode())

    glDeleteShader(vs)
    glDeleteShader(fs)
    return p


def perspective(fov, aspect, near, far):
    import math
    import numpy as np

    f = 1.0 / math.tan(math.radians(fov) / 2)

    return np.array([
        [f/aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far+near)/(near-far), (2*far*near)/(near-far)],
        [0, 0, -1, 0]
    ], dtype=np.float32)


def look_at(pos, yaw, pitch):
    yaw = math.radians(yaw)
    pitch = math.radians(pitch)

    front = np.array([
        math.cos(yaw)*math.cos(pitch),
        math.sin(pitch),
        math.sin(yaw)*math.cos(pitch)
    ], dtype=np.float32)

    front /= np.linalg.norm(front)

    right = np.cross(front, np.array([0,1,0], dtype=np.float32))
    right /= np.linalg.norm(right)

    up = np.cross(right, front)

    view = np.identity(4, dtype=np.float32)
    view[0,:3] = right
    view[1,:3] = up
    view[2,:3] = -front

    view[0,3] = -np.dot(right, pos)
    view[1,3] = -np.dot(up, pos)
    view[2,3] = np.dot(front, pos)

    return view


class Viewport(QOpenGLWidget):
    def __init__(self, world):
        super().__init__()

        self.world = world
        self.last_time = time.time()

        self.pos = np.array([0,0,5], dtype=np.float32)
        self.yaw = 0
        self.pitch = 0

        self.keys = set()
        self.move_mode = False

        self.setFocusPolicy(Qt.StrongFocus)
        self.setMouseTracking(True)

    # INPUT

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
        self.keys.add(e.key())

    def keyReleaseEvent(self, e):
        self.keys.discard(e.key())

    def mouseMoveEvent(self, e):
        if not self.move_mode:
            return

        c = self.rect().center()
        dx = e.x() - c.x()
        dy = e.y() - c.y()

        self.yaw += dx * 0.15
        self.pitch -= dy * 0.15
        self.pitch = max(-89, min(89, self.pitch))

        self.lock_mouse()

    def lock_mouse(self):
        QCursor.setPos(self.mapToGlobal(self.rect().center()))


    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)
        self.program = create_program(VERTEX_SHADER, FRAGMENT_SHADER)

        Render.init()

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        self.projection = perspective(90, w/max(h,1), 0.1, 100)

    def update_camera(self, dt):
        speed = 5 if Qt.Key_Shift in self.keys else 2.5

        yaw = math.radians(self.yaw)
        pitch = math.radians(self.pitch)

        forward = np.array([
            math.cos(yaw) * math.cos(pitch),
            math.sin(pitch),
            math.sin(yaw) * math.cos(pitch)
        ], dtype=np.float32)

        forward /= np.linalg.norm(forward)

        right = np.cross(forward, np.array([0,1,0], dtype=np.float32))
        right /= np.linalg.norm(right)

        # movement
        if Qt.Key_W in self.keys:
            self.pos += forward * dt * speed
        if Qt.Key_S in self.keys:
            self.pos -= forward * dt * speed
        if Qt.Key_A in self.keys:
            self.pos -= right * dt * speed
        if Qt.Key_D in self.keys:
            self.pos += right * dt * speed

        if Qt.Key_Space in self.keys:
            self.pos[1] += dt * speed
        if Qt.Key_Control in self.keys:
            self.pos[1] -= dt * speed

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        self.update_camera(dt)

        view = look_at(self.pos, self.yaw, self.pitch)

        glUseProgram(self.program)

        glUniformMatrix4fv(glGetUniformLocation(self.program,"projection"),1,GL_TRUE,self.projection)
        glUniformMatrix4fv(glGetUniformLocation(self.program,"view"),1,GL_TRUE,view)

        Render.draw_grid(self.program)

        for obj in self.world["actors"]:
            if obj["type"] == "cube":
                Render.draw_cube(self.program, obj["pos"], obj["size"], obj["rot"], obj["color"])

                if self.world.get("selected") == obj:
                    bigger = [obj["size"][0]+0.01,
                            obj["size"][1]+0.01,
                            obj["size"][2]+0.01]

                    Render.draw_cube_wires(self.program, obj["pos"], bigger, obj["rot"])
        glUseProgram(0)