#include "main.h"

#include <cmath>
#include <cstdio>
#include <ctime>
#include <iostream>
#include "GLFW/glfw3.h"
#include "mesh.h"
#include "stb_image.h"

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

#include <ostream>
#include <string>
#include <vector>

#include "quader.h"
#include "camera.h"
#include "model.h"
#include "button.h"
#include "ground.h"

const int START_WIDTH = 800;
const int START_HEIGHT = 600;
const int SIDE_PANEL_SIZE = 100;

int width = START_WIDTH;
int height = START_HEIGHT;

float deltaTime = 0.0f;
float lastFrame = 0.0f;

float lastX = 400.0f, lastY = 300.0f;
bool rightMouseDown = false, leftMouseDown = false;
bool shift = false, ctrl = false;

glm::mat4 projection = glm::perspective(glm::radians(45.0f), (float)START_WIDTH / START_HEIGHT, 0.1f, 100.0f);
glm::mat4 model = glm::scale(glm::mat4(1.0f), glm::vec3(0.1f));

glm::mat4 quadProjection = glm::ortho(0.0f, 800.0f, 0.0f, 600.0f);

Camera camera;
std::vector<Button> buttons;

GLFWwindow *window;

Shader *fontShader;
Shader *quadShader;

Model *droney;
Shader *shader;

Quader *quader;

Ground *ground;

LoopReturn currentMessage;

int main() {
    setup();
    droney->setState(1, (DroneState)1);
    droney->setState(2, (DroneState)1);
    droney->setState(3, (DroneState)1);
    droney->setState(4, (DroneState)1);
    droney->setState(5, (DroneState)1);

    while (!shouldClose()) {
        loop();
    }
    cleanup();
}

void setExpanse(glm::vec3 min, glm::vec3 max) {
    droney->minPos = min;
    droney->maxPos = max;
}

void setColor(int id, float r, float g, float b, float a) {
    droney->setColor(id, r, g, b, a);
}

void setPos(int id, float x, float y, float z) {
    droney->setPos(id, x, y, z);
}

void setIp(int id, std::string ip) {
    //TODO maybe not two copies and also having 21 extra bytes for the shaders to eat
    char c_ip[21];
    for (int i = 0; i < 21 && i < ip.length(); i++) {
        c_ip[i] = ip[i];
    }
    droney->setIp(id, c_ip);
}

void setState(int id, DroneState state) {
    droney->setState(id, state);
}

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

    fontShader = new Shader("shaders/fontVertex.glsl", "shaders/fontFragment.glsl");
    quadShader = new Shader("shaders/fontVertex.glsl", "shaders/quadFragment.glsl");

    droney = new Model("droney/droney.obj");
    shader = new Shader("shaders/vertex.glsl", "shaders/fragment.glsl");

    quader = new Quader();
    ground = new Ground();

    float padding = 0.02f;
    float buttonWidth = 0.9f / 6.0f;
    float buttonHeight = 0.05f;
    int i = 0;

    auto makeButton = [&i, buttonWidth, buttonHeight, padding](LoopReturn message, std::string name) {
        buttons.push_back(Button(buttonWidth / 2 + buttonWidth * i, 1 - buttonHeight / 2 - padding, buttonWidth - padding, buttonHeight, [message, name](bool, bool) {currentMessage = message;}, name));
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
    droney->drawInstances(quader);

    glfwSwapBuffers(window);
    glfwPollEvents();

    return currentMessage;
}

void cleanup() {
    glfwTerminate();
}

bool shouldClose() {
    return glfwWindowShouldClose(window);
}

void framebufferSizeCallback(GLFWwindow* window, int width, int height) {
    setGlViewport(width, height);
}

void proccessInput(GLFWwindow* window) {
    if (glfwGetKey(window, GLFW_KEY_ESCAPE) == GLFW_PRESS) glfwSetWindowShouldClose(window, true);

    const float cameraSpeed = 2.5f * deltaTime;

    if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_PRESS) {
        double xpos, ypos;
        glfwGetCursorPos(window, &xpos, &ypos);
        if (leftMouseDown == false) {
            for (Button &b : buttons) {
                b.checkClick(xpos / width, ypos / height, shift, ctrl);
            }
            droney->checkButtons(xpos / width, ypos / height, shift, ctrl);
        }

        leftMouseDown = true;
    } else if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_LEFT) == GLFW_RELEASE) {
        for (Button &b : buttons) {
            b.setClicked(false);
        }

        leftMouseDown = false;
    }

    if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_RIGHT) == GLFW_PRESS) rightMouseDown = true;
    else if (glfwGetMouseButton(window, GLFW_MOUSE_BUTTON_RIGHT) == GLFW_RELEASE) rightMouseDown = false;

    if (glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS || glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_PRESS) shift = true;
    else if (glfwGetMouseButton(window, GLFW_KEY_LEFT_SHIFT) == GLFW_RELEASE || glfwGetKey(window, GLFW_KEY_LEFT_SHIFT) == GLFW_RELEASE) shift = false;

    if (glfwGetKey(window, GLFW_KEY_LEFT_CONTROL) == GLFW_PRESS || glfwGetKey(window, GLFW_KEY_LEFT_CONTROL) == GLFW_PRESS) ctrl = true;
    else if (glfwGetMouseButton(window, GLFW_KEY_LEFT_CONTROL) == GLFW_RELEASE || glfwGetKey(window, GLFW_KEY_LEFT_CONTROL) == GLFW_RELEASE) ctrl = false;
}

void mouse_callback(GLFWwindow* window, double xpos, double ypos) {
    float xOffset = lastX - xpos;
    float yOffset = ypos - lastY;
    lastX = xpos;
    lastY = ypos;

    const float rotSensitivity = 0.005f;
    const float panSensitivity = 0.4f;

    int width, height;
    glfwGetWindowSize(window, &width, &height);

    if (leftMouseDown) {
        camera.rotate(xOffset, yOffset);
    }
    if (rightMouseDown) {
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
    glfwSetCursorPosCallback(window, mouse_callback);

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
