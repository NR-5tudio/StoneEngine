import sys
import math
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QListWidget,
    QDockWidget
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QOpenGLWidget

from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt5.QtGui import QCursor




def draw_cube(pos=[0, 0, 0], size=[1, 1, 1], rotation=[0, 0, 0]):
    glPushMatrix()

    glTranslatef(pos[0], pos[1], pos[2])

    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)

    glScalef(size[0], size[1], size[2])

    glBegin(GL_QUADS)

    # Front
    glColor3f(1, 0, 0)
    glVertex3f(-1, -1, 1)
    glVertex3f(1, -1, 1)
    glVertex3f(1, 1, 1)
    glVertex3f(-1, 1, 1)

    # Back
    glColor3f(0, 1, 0)
    glVertex3f(-1, -1, -1)
    glVertex3f(-1, 1, -1)
    glVertex3f(1, 1, -1)
    glVertex3f(1, -1, -1)

    # Left
    glColor3f(0, 0, 1)
    glVertex3f(-1, -1, -1)
    glVertex3f(-1, -1, 1)
    glVertex3f(-1, 1, 1)
    glVertex3f(-1, 1, -1)

    # Right
    glColor3f(1, 1, 0)
    glVertex3f(1, -1, -1)
    glVertex3f(1, 1, -1)
    glVertex3f(1, 1, 1)
    glVertex3f(1, -1, 1)

    # Top
    glColor3f(0, 1, 1)
    glVertex3f(-1, 1, -1)
    glVertex3f(-1, 1, 1)
    glVertex3f(1, 1, 1)
    glVertex3f(1, 1, -1)

    # Bottom
    glColor3f(1, 0, 1)
    glVertex3f(-1, -1, -1)
    glVertex3f(1, -1, -1)
    glVertex3f(1, -1, 1)
    glVertex3f(-1, -1, 1)

    glEnd()

    glPopMatrix()
def draw_cube_wires(pos=[0, 0, 0], size=[1, 1, 1], rotation=[0, 0, 0]):
    glPushMatrix()

    glTranslatef(pos[0], pos[1], pos[2])

    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)

    glScalef(size[0], size[1], size[2])

    glColor3f(1, 1, 1)

    glBegin(GL_LINES)

    # Front face
    glVertex3f(-1, -1, 1); glVertex3f(1, -1, 1)
    glVertex3f(1, -1, 1); glVertex3f(1, 1, 1)
    glVertex3f(1, 1, 1); glVertex3f(-1, 1, 1)
    glVertex3f(-1, 1, 1); glVertex3f(-1, -1, 1)

    # Back face
    glVertex3f(-1, -1, -1); glVertex3f(1, -1, -1)
    glVertex3f(1, -1, -1); glVertex3f(1, 1, -1)
    glVertex3f(1, 1, -1); glVertex3f(-1, 1, -1)
    glVertex3f(-1, 1, -1); glVertex3f(-1, -1, -1)

    # Connect front and back
    glVertex3f(-1, -1, 1); glVertex3f(-1, -1, -1)
    glVertex3f(1, -1, 1); glVertex3f(1, -1, -1)
    glVertex3f(1, 1, 1); glVertex3f(1, 1, -1)
    glVertex3f(-1, 1, 1); glVertex3f(-1, 1, -1)

    glEnd()

    glPopMatrix()