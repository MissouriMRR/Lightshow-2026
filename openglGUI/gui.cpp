#include "glad/glad.h"

#include "gui.h"

#include <QCoreApplication>
#include <QCursor>
#include <QDateTime>
#include <QGuiApplication>
#include <QOpenGLContext>
#include <QSurfaceFormat>
#include <QTimer>

#include <iostream>

#include "glm/gtc/type_ptr.hpp"
#include "shader.h"
#include "stb_image.h"

#ifndef ASSET_DIR
#define ASSET_DIR ""
#endif

int GuiReadyEvent::event_number = QEvent::registerEventType();

GuiReadyEvent::GuiReadyEvent() : QEvent((QEvent::Type)event_number) {}

Gui::Gui(QWidget *parent) { setMouseTracking(true); }

void Gui::initializeGL() {
    long time;
    std::time(&time);
    srand(time);

    auto getProcAddr = [](const char *name) -> void * {
        return (void *)QOpenGLContext::currentContext()->getProcAddress(name);
    };

    if (!gladLoadGLLoader((GLADloadproc)getProcAddr)) {
        std::cout << "glad loading failed" << std::endl;
        return;
    }

    glEnable(GL_DEPTH_TEST);
    glEnable(GL_CULL_FACE);
    glEnable(GL_MULTISAMPLE);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);

    stbi_set_flip_vertically_on_load(true);

    std::string assetDir = ASSET_DIR;
    fontShader = new Shader(assetDir + "shaders/fontVertex.glsl", assetDir + "shaders/fontFragment.glsl");
    quadShader = new Shader(assetDir + "shaders/fontVertex.glsl", assetDir + "shaders/quadFragment.glsl");

    droney = new Drone(assetDir + "drone_model/drone_model.obj");
    shader = new Shader(assetDir + "shaders/vertex.glsl", assetDir + "shaders/fragment.glsl");

    quader = new Quader(assetDir + "fonts/arial.ttf");
    ground = new Ground(assetDir);

    QCoreApplication::sendEvent(window(), new GuiReadyEvent());
}

void Gui::resizeGL(int w, int h) {
    glViewport(0, 0, width(), height());

    int adjusted_width = width() - SIDE_PANEL_SIZE;
    projection = glm::perspective(glm::radians(45.0f), (float)adjusted_width / height(), 0.1f, 100.0f);
}

void Gui::paintGL() {
    float currentFrame = QDateTime().currentMSecsSinceEpoch() / 1000.0;
    deltaTime = currentFrame - lastFrame;
    lastFrame = currentFrame;

    glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    ground->draw(projection, &camera);

    setupShader(shader);
    if (droney != nullptr) {
        droney->resetVBO();
        droney->draw(shader);
    }

    quader->setup(fontShader, quadShader, glm::vec2(width(), height()));
    quader->renderQuad(glm::vec2(0.9f, 0.0f), glm::vec2(1.0f, 1.0f), glm::vec4(0, 0, 0, 1));
    if (droney != nullptr) droney->drawInstances(quader, projection, &camera);
}

void Gui::setupShader(Shader *shader) {
    shader->use();

    shader->setVec3("viewPos", camera.pos);
    shader->setMat4("view", camera.getViewMatrix());
    shader->setMat4("projection", projection);

    shader->setMat4("model", model);

    glm::mat3 normal = glm::transpose(glm::inverse(model));
    int normalLoc = glGetUniformLocation(shader->ID, "normal");
    glUniformMatrix3fv(normalLoc, 1, GL_FALSE, glm::value_ptr(normal));
}

void Gui::keyPressEvent(QKeyEvent *event) {
    if (event->key() == Qt::Key_Escape) droney->resetCurrentDrones();
}

void Gui::mousePressEvent(QMouseEvent *event) {
    if (event->button() == Qt::LeftButton) {
        checkButtons(event);
        leftMouseDown = true;
    } else if (event->button() == Qt::RightButton) {
        rightMouseDown = true;
        QGuiApplication::setOverrideCursor(Qt::BlankCursor);
    }
}

void Gui::mouseReleaseEvent(QMouseEvent *event) {
    if (event->button() == Qt::LeftButton) {
        if (click) checkRelease(event);
        leftMouseDown = false;
    } else if (event->button() == Qt::RightButton) {
        rightMouseDown = false;
        QGuiApplication::restoreOverrideCursor();
    }
}

void Gui::checkButtons(QMouseEvent *event) {
    float xpos, ypos;
    getScaledCursorPos(&xpos, &ypos);

    click = true;
    click &= !droney->checkButtons(xpos, ypos, event->modifiers() & Qt::ShiftModifier,
                                   event->modifiers() & Qt::ControlModifier);
    drag = click && xpos < 0.9;
    repaint();
}

void Gui::checkRelease(QMouseEvent *event) {
    float xpos, ypos;
    getScaledCursorPos(&xpos, &ypos);

    if (!droney->checkDrones(xpos, ypos, event->modifiers() & Qt::ShiftModifier,
                             event->modifiers() & Qt::ControlModifier, &camera, projection)) {
        droney->resetCurrentDrones();
        repaint();
    }
}

void Gui::mouseMoveEvent(QMouseEvent *event) {
    float xOffset = xposRaw - event->pos().x();
    float yOffset = event->pos().y() - yposRaw;
    xposRaw = event->pos().x();
    yposRaw = event->pos().y();
    click = false;

    const float rotSensitivity = 0.005f;
    const float panSensitivity = 0.4f;

    if (leftMouseDown && drag) {
        camera.rotate(xOffset, yOffset);
        repaint();
    } else if (rightMouseDown) {
        camera.translate(glm::vec3(xOffset * START_WIDTH / width(), yOffset * START_HEIGHT / height(), 0) *
                         panSensitivity);
        repaint();
    }
}

void Gui::getScaledCursorPos(float *xpos, float *ypos) {
    *xpos = xposRaw / width();
    *ypos = yposRaw / height();
}

void Gui::setExpanse(glm::vec3 min, glm::vec3 max) {
    if (droney == nullptr) {
        std::cout << "droney is uninitialized you idiot" << std::endl;
    } else {
        droney->minPos = min;
        droney->maxPos = max;
    }
}

void Gui::setColor(int id, float r, float g, float b, float a) {
    if (droney == nullptr) std::cout << "droney is uninitialized you idiot" << std::endl;
    else
        droney->setColor(id, r, g, b, a);
    update();
}

void Gui::setPos(int id, float x, float y, float z) {
    if (droney == nullptr) std::cout << "droney is uninitialized you idiot" << std::endl;
    else
        droney->setPos(id, x, y, z);
    update();
}

void Gui::setIp(int id, std::string ip) {
    if (droney == nullptr) std::cout << "droney is uninitialized you idiot" << std::endl;
    else
        droney->setIp(id, ip);
    update();
}

void Gui::setState(int id, DroneState state) {
    if (droney == nullptr) std::cout << "droney is uninitialized you idiot" << std::endl;
    else
        droney->setState(id, state);
    update();
}
