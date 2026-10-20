#ifndef GUI_H
#define GUI_H

#include "button.h"
#include "camera.h"
#include "drone.h"
#include "glm/glm.hpp"
#include "ground.h"
#include <QEvent>
#include <QKeyEvent>
#include <QMainWindow>
#include <QOpenGLContext>
#include <QOpenGLWidget>
#include <QWindow>

class GuiReadyEvent : public QEvent {
  public:
    GuiReadyEvent();

    static int event_number;
};

class Gui : public QOpenGLWidget {
  public:
    Gui(QWidget *parent = nullptr);

    void setupShader(Shader *shader);
    void checkButtons(QMouseEvent *event);
    void checkRelease(QMouseEvent *event);
    void getScaledCursorPos(float *xpos, float *ypos);

    void setExpanse(glm::vec3 min, glm::vec3 max);
    void setColor(int id, float r, float g, float b, float a);
    void setPos(int id, float x, float y, float z);
    void setIp(int id, std::string ip);
    void setState(int id, DroneState state);

    Drone *droney = nullptr;

  protected:
    void keyPressEvent(QKeyEvent *event) override;
    void mousePressEvent(QMouseEvent *event) override;
    void mouseReleaseEvent(QMouseEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void paintGL() override;
    void resizeGL(int w, int h) override;
    void initializeGL() override;

  private:
    const int START_WIDTH = 800;
    const int START_HEIGHT = 600;
    const int SIDE_PANEL_SIZE = 100;

    QTimer *timer;

    float deltaTime = 0.0f;
    float lastFrame = 0.0f;

    bool leftMouseDown = false, rightMouseDown = false;

    glm::mat4 projection = glm::perspective(glm::radians(45.0f), (float)START_WIDTH / START_HEIGHT, 0.1f, 100.0f);
    glm::mat4 model = glm::scale(glm::mat4(1.0f), glm::vec3(0.1f));

    glm::mat4 quadProjection = glm::ortho(0.0f, 800.0f, 0.0f, 600.0f);

    Camera camera;

    Shader *fontShader = nullptr;
    Shader *quadShader = nullptr;
    Shader *shader = nullptr;
    Quader *quader = nullptr;
    Ground *ground = nullptr;

    bool click = false, drag = false;

    float xposRaw = START_WIDTH / 2.0, yposRaw = START_HEIGHT / 2.0;
};

#endif
