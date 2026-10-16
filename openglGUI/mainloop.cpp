/*
 * mainloop.cpp
 * Spawns glfw window
 * Manages window messages
 */

#include "mainloop.h"

#include <QApplication>
#include <QWidget>
#include <QSurfaceFormat>
#include <QOpenGLContext>
#include <QTime>
#include <QEvent>

#include "mesh.h"
#include "qdatetime.h"
#include "stb_image.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <ctime>

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

#include <string>
#include <vector>

#include "button.h"
#include "camera.h"
#include "drone.h"
#include "ground.h"
#include "quader.h"
#include "gui.h"

#ifndef ASSET_DIR
#define ASSET_DIR ""
#endif

int setup() {
    return 0;
}
