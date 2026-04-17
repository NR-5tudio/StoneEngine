import numpy as np
import math
from OpenGL.GL import *

vao_cube = None
cube_count = 0

vao_grid = None
grid_count = 0


def init():
    init_cube()
    init_grid()


# ---------- MODEL MATRIX ----------

def mat_model(pos, size, rot):
    def I(): return np.identity(4, dtype=np.float32)

    def T(v):
        m = I()
        m[0,3], m[1,3], m[2,3] = v
        return m

    def S(v):
        m = I()
        m[0,0], m[1,1], m[2,2] = v
        return m

    def Rx(a):
        c,s = math.cos(math.radians(a)), math.sin(math.radians(a))
        m = I()
        m[1,1], m[1,2], m[2,1], m[2,2] = c,-s,s,c
        return m

    def Ry(a):
        c,s = math.cos(math.radians(a)), math.sin(math.radians(a))
        m = I()
        m[0,0], m[0,2], m[2,0], m[2,2] = c,s,-s,c
        return m

    def Rz(a):
        c,s = math.cos(math.radians(a)), math.sin(math.radians(a))
        m = I()
        m[0,0], m[0,1], m[1,0], m[1,1] = c,-s,s,c
        return m

    return T(pos) @ Rx(rot[0]) @ Ry(rot[1]) @ Rz(rot[2]) @ S(size)


# ---------- CUBE ----------

def init_cube():
    global vao_cube, cube_count

    vertices = np.array([
        # FRONT
        0,0,1, 1,0,1, 1,1,1,
        1,1,1, 0,1,1, 0,0,1,

        # BACK
        1,0,0, 0,0,0, 0,1,0,
        0,1,0, 1,1,0, 1,0,0,

        # LEFT
        0,0,0, 0,0,1, 0,1,1,
        0,1,1, 0,1,0, 0,0,0,

        # RIGHT
        1,0,1, 1,0,0, 1,1,0,
        1,1,0, 1,1,1, 1,0,1,

        # TOP
        0,1,1, 1,1,1, 1,1,0,
        1,1,0, 0,1,0, 0,1,1,

        # BOTTOM
        0,0,0, 1,0,0, 1,0,1,
        1,0,1, 0,0,1, 0,0,0,
    ], dtype=np.float32)

    cube_count = len(vertices)//3

    vao_cube = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao_cube)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
    glEnableVertexAttribArray(0)

    glBindVertexArray(0)


def draw_cube(program, pos, size, rot, color):
    model = mat_model(pos, size, rot)

    glUniformMatrix4fv(glGetUniformLocation(program,"model"),1,GL_TRUE,model)
    glUniform3f(glGetUniformLocation(program,"color"), color[0]/255, color[1]/255, color[2]/255)

    glBindVertexArray(vao_cube)
    glDrawArrays(GL_TRIANGLES, 0, cube_count)
    glBindVertexArray(0)

def draw_cube_wires(program, pos, size, rot):
    glUseProgram(program)

    glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
    glLineWidth(2.0)

    loc = glGetUniformLocation(program, "color")
    glUniform3f(loc, 1.0, 0.0, 0.8)
    color = [1.0*255, 0.0*255, 0.8*255]
    draw_cube(program, pos, size, rot, color)

    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
# GRID

def init_grid(size=50):
    global vao_grid, grid_count

    lines = []

    for i in range(-size, size+1):
        lines += [i,0,-size, i,0,size]
        lines += [-size,0,i, size,0,i]

    data = np.array(lines, dtype=np.float32)
    grid_count = len(data)//3

    vao_grid = glGenVertexArrays(1)
    vbo = glGenBuffers(1)

    glBindVertexArray(vao_grid)
    glBindBuffer(GL_ARRAY_BUFFER, vbo)
    glBufferData(GL_ARRAY_BUFFER, data.nbytes, data, GL_STATIC_DRAW)

    glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,0,None)
    glEnableVertexAttribArray(0)

    glBindVertexArray(0)


def draw_grid(program):
    glUniformMatrix4fv(
        glGetUniformLocation(program,"model"),
        1,
        GL_TRUE,
        np.identity(4, dtype=np.float32)
    )

    glUniform3f(glGetUniformLocation(program,"color"),0.3,0.3,0.3)

    glBindVertexArray(vao_grid)
    glDrawArrays(GL_LINES, 0, grid_count)
    glBindVertexArray(0)