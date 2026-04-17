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




def draw_cube(pos=[0, 0, 0], size=[1, 1, 1], rotation=[60, 60, 60], color=[255, 255, 255, 255]):
    sx, sy, sz = size

    glPushMatrix()

    # move to pivot (edge)
    glTranslatef(pos[0], pos[1], pos[2])

    # rotate around that pivot
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)

    glBegin(GL_QUADS)

    glColor3f(color[0]/255, color[1]/255, color[2]/255)

    # Front
    glVertex3f(0,  0,  sz)
    glVertex3f(sx, 0,  sz)
    glVertex3f(sx, sy, sz)
    glVertex3f(0,  sy, sz)

    # Back
    glVertex3f(sx, 0,  0)
    glVertex3f(0,  0,  0)
    glVertex3f(0,  sy, 0)
    glVertex3f(sx, sy, 0)

    # Left
    glVertex3f(0, 0,  0)
    glVertex3f(0, 0,  sz)
    glVertex3f(0, sy, sz)
    glVertex3f(0, sy, 0)

    # Right
    glVertex3f(sx, 0,  sz)
    glVertex3f(sx, 0,  0)
    glVertex3f(sx, sy, 0)
    glVertex3f(sx, sy, sz)

    # Top
    glVertex3f(0,  sy, 0)
    glVertex3f(0,  sy, sz)
    glVertex3f(sx, sy, sz)
    glVertex3f(sx, sy, 0)

    # Bottom
    glVertex3f(0,  0, 0)
    glVertex3f(sx, 0, 0)
    glVertex3f(sx, 0, sz)
    glVertex3f(0,  0, sz)

    glEnd()

    glPopMatrix()

    
def draw_cube_wires(pos=[0, 0, 0], size=[1, 1, 1], rotation=[0, 0, 0]):
    sx, sy, sz = size

    glPushMatrix()

    # move to pivot (edge)
    glTranslatef(pos[0], pos[1], pos[2])

    # rotate around pivot
    glRotatef(rotation[0], 1, 0, 0)
    glRotatef(rotation[1], 0, 1, 0)
    glRotatef(rotation[2], 0, 0, 1)

    glColor3f(255/255, 0, 206/255)
    glLineWidth(3.0)

    glBegin(GL_LINES)

    # Front face
    glVertex3f(0,  0,  sz); glVertex3f(sx, 0,  sz)
    glVertex3f(sx, 0,  sz); glVertex3f(sx, sy, sz)
    glVertex3f(sx, sy, sz); glVertex3f(0,  sy, sz)
    glVertex3f(0,  sy, sz); glVertex3f(0,  0,  sz)

    # Back face
    glVertex3f(0,  0,  0);  glVertex3f(sx, 0,  0)
    glVertex3f(sx, 0,  0);  glVertex3f(sx, sy, 0)
    glVertex3f(sx, sy, 0);  glVertex3f(0,  sy, 0)
    glVertex3f(0,  sy, 0);  glVertex3f(0,  0,  0)

    # Connect front and back
    glVertex3f(0,  0,  sz); glVertex3f(0,  0,  0)
    glVertex3f(sx, 0,  sz); glVertex3f(sx, 0,  0)
    glVertex3f(sx, sy, sz); glVertex3f(sx, sy, 0)
    glVertex3f(0,  sy, sz); glVertex3f(0,  sy, 0)

    glEnd()

    glPopMatrix()

def draw_world_grid(size=50, step=1):
    glPushMatrix()

    glLineWidth(1.0)

    glBegin(GL_LINES)

    for i in range(-size, size + 1, step):
        # darker center lines
        if i == 0:
            glColor3f(0.8, 0.2, 0.2)  # X axis (red-ish)
        else:
            glColor3f(0.3, 0.3, 0.3)

        # lines parallel to Z (X lines)
        glVertex3f(i, 0, -size)
        glVertex3f(i, 0, size)

        # darker center line
        if i == 0:
            glColor3f(0.2, 0.8, 0.2)  # Z axis (green-ish)
        else:
            glColor3f(0.3, 0.3, 0.3)

        # lines parallel to X (Z lines)
        glVertex3f(-size, 0, i)
        glVertex3f(size, 0, i)

    glEnd()

    glPopMatrix()