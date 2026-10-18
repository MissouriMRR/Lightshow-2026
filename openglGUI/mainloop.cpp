/*
 * mainloop.cpp
 * Spawns glfw window
 * Manages window messages
 */

#include "mainloop.h"

#include "GLFW/glfw3.h"
#include "mesh.h"
#include "stb_image.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <iostream>

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

#include <ostream>
#include <string>
#include <vector>

#include "button.h"
#include "camera.h"
#include "drone.h"
#include "ground.h"
#include "quader.h"

#ifndef ASSET_DIR
#define ASSET_DIR ""
#endif

const int START_WIDTH = 800;
const int START_HEIGHT = 600;
const int SIDE_PANEL_SIZE = 100;

int width = START_WIDTH;
int height = START_HEIGHT;

float deltaTime = 0.0f;
float lastFrame = 0.0f;

float lastX = 400.0f, lastY = 300.0f;
bool leftMouseDown = false;

glm::mat4 projection = glm::perspective(glm::radians(45.0f), (float)START_WIDTH / START_HEIGHT, 0.1f, 100.0f);
glm::mat4 model = glm::scale(glm::mat4(1.0f), glm::vec3(0.1f));

glm::mat4 quadProjection = glm::ortho(0.0f, 800.0f, 0.0f, 600.0f);

Camera camera;
std::vector<Button> buttons;

GLFWwindow *window;

Shader *fontShader;
Shader *quadShader;

Drone *droney;
Shader *shader;
Quader *quader;
Ground *ground;

LoopReturn currentMessage;
bool click = false, drag = false;

void setExpanse(glm::vec3 min, glm::vec3 max) {
    droney->minPos = min;
    droney->maxPos = max;
}

void setColor(int id, float r, float g, float b, float a) { droney->setColor(id, r, g, b, a); }

void setPos(int id, float x, float y, float z) { droney->setPos(id, x, y, z); }

void setIp(int id, std::string ip) { droney->setIp(id, ip); }

void setState(int id, DroneState state) { droney->setState(id, state); }

int setup() {
    long time;
    std::time(&time);
    srand(time);

    if (setupWindow(window) == -1) return -1;

    setGlViewport(START_WIDTH, START_HEIGHT);
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

    float padding = 0.02f;
    float buttonWidth = 0.9f / 6.0f;
    float buttonHeight = 0.05f;
    int i = 0;

    auto makeButton = [&i, buttonWidth, buttonHeight, padding](LoopReturn message, std::string name) {
        buttons.push_back(Button(
            buttonWidth / 2 + buttonWidth * i, 1 - buttonHeight / 2 - padding, buttonWidth - padding, buttonHeight,
            [message, name](bool, bool) { currentMessage = message; }, name));
        i++;
    };

    makeButton(LoopReturn::ARM, "Arm");
    makeButton(LoopReturn::TAKEOFF, "Take Off");
    makeButton(LoopReturn::STEP, "Step");
    makeButton(LoopReturn::LAND, "Land");
    makeButton(LoopReturn::HALT, "Halt");

    return 0;
}

LoopReturn loop() {
    currentMessage = LoopReturn::NOTHING;

    float currentFrame = glfwGetTime();
    deltaTime = currentFrame - lastFrame;
    lastFrame = currentFrame;

    proccessInput(window);

    glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    ground->draw(projection, &camera);

    setupShader(shader);
    droney->draw(shader);

    quader->setup(fontShader, quadShader, glm::vec2(width, height));
    for (Button b : buttons) b.draw(quader);
    quader->renderQuad(glm::vec2(0.9f, 0.0f), glm::vec2(1.0f, 1.0f), glm::vec4(0, 0, 0, 1));
    droney->drawInstances(quader, projection, &camera);

    glfwSwapBuffers(window);
    glfwPollEvents();

    return currentMessage;
}

void cleanup() { glfwTerminate(); }

bool shouldClose() { return glfwWindowShouldClose(window); }

void framebufferSizeCallback(GLFWwindow *window, int width, int height) { setGlViewport(width, height); }

void checkButtons() {
    double xpos, ypos;
    getScaledCursorPos(window, &xpos, &ypos);

    click = true;
    bool shift = glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) || glfwGetKey(window, GLFW_KEY_RIGHT_SHIFT);
    bool ctrl = glfwGetKey(window, GLFW_KEY_LEFT_CONTROL) || glfwGetKey(window, GLFW_KEY_RIGHT_CONTROL);

    for (Button &b : buttons) {
        click &= !b.checkClick(xpos, ypos, shift, ctrl);
    }
    click &= !droney->checkButtons(xpos, ypos, shift, ctrl);
    drag = click && xpos < 0.9;
}

void checkRelease() {
    double xpos, ypos;
    getScaledCursorPos(window, &xpos, &ypos);
    bool shift = glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) || glfwGetKey(window, GLFW_KEY_RIGHT_SHIFT);
    bool ctrl = glfwGetKey(window, GLFW_KEY_LEFT_CONTROL) || glfwGetKey(window, GLFW_KEY_RIGHT_CONTROL);

    if (!droney->checkDrones(xpos, ypos, shift, ctrl, &camera, projection)) {
        droney->resetCurrentDrones();
    }
}

void getScaledCursorPos(GLFWwindow *window, double *xpos, double *ypos) {
    double xposRaw, yposRaw;
    glfwGetCursorPos(window, &xposRaw, &yposRaw);
    *xpos = xposRaw / width;
    *ypos = yposRaw / height;
}

void proccessInput(GLFWwindow *window) {
    if (glfwGetKey(window, GLFW_KEY_ESCAPE)) droney->resetCurrentDrones();

    if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT)) {
        if (leftMouseDown == false) checkButtons();
        leftMouseDown = true;
    } else {
        if (click) checkRelease();
        leftMouseDown = false;
    }
}

void mouseCallback(GLFWwindow *window, double xpos, double ypos) {
    float xOffset = lastX - xpos;
    float yOffset = ypos - lastY;
    lastX = xpos;
    lastY = ypos;
    click = false;

    const float rotSensitivity = 0.005f;
    const float panSensitivity = 0.4f;

    int width, height;
    glfwGetWindowSize(window, &width, &height);

    if (leftMouseDown && drag) {
        camera.rotate(xOffset, yOffset);
    }
    if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_RIGHT)) {
        camera.translate(glm::vec3(xOffset * START_WIDTH / width, yOffset * START_HEIGHT / height, 0) * panSensitivity);
    }
}

void setupShader(Shader *shader) {
    shader->use();

    shader->setVec3("viewPos", camera.pos);
    shader->setMat4("view", camera.getViewMatrix());
    shader->setMat4("projection", projection);

    shader->setMat4("model", model);

    glm::mat3 normal = glm::transpose(glm::inverse(model));
    int normalLoc = glGetUniformLocation(shader->ID, "normal");
    glUniformMatrix3fv(normalLoc, 1, GL_FALSE, glm::value_ptr(normal));
}

int setupWindow(GLFWwindow *&window) {
    glfwInit();
    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

    glfwWindowHint(GLFW_SAMPLES, 4);

    window = glfwCreateWindow(START_WIDTH, START_HEIGHT, "Station", NULL, NULL);
    if (window == NULL) {
        std::cout << "Failed to create GLFW window" << std::endl;
        return -1;
    }

    glfwMakeContextCurrent(window);
    glfwSetFramebufferSizeCallback(window, framebufferSizeCallback);
    glfwSetInputMode(window, GLFW_CURSOR, GLFW_CURSOR_HIDDEN);
    glfwSetCursorPosCallback(window, mouseCallback);

    if (!gladLoadGLLoader((GLADloadproc)glfwGetProcAddress)) {
        std::cout << "Failed to initialize glad" << std::endl;
        return -1;
    }

    return 0;
}

void setGlViewport(int p_width, int p_height) {
    width = p_width;
    height = p_height;

    glViewport(0, 0, width, height);

    p_width -= SIDE_PANEL_SIZE;
    projection = glm::perspective(glm::radians(45.0f), (float)p_width / height, 0.1f, 100.0f);
}
