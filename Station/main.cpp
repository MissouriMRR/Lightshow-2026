#include <cmath>
#include <cstdio>
#include <glad/glad.h>
#include <GLFW/glfw3.h>
#include <iostream>
#include "stb_image.h"

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

#include <ostream>
#include <queue>
#include <string>
#include <thread>
#include <vector>

#include "quader.h"
#include "camera.h"
#include "shader.h"
#include "model.h"
#include "button.h"

const int START_WIDTH = 800;
const int START_HEIGHT = 600;
const int SIDE_PANEL_SIZE = 100;

int width = START_WIDTH;
int height = START_HEIGHT;

void framebufferSizeCallback(GLFWwindow* window, int width, int height);
void proccessInput(GLFWwindow* window);
void mouse_callback(GLFWwindow* window, double xpos, double ypos);
void setupShader(Shader &shader);
void parseInput(Model &model, std::string input);
int setupWindow(GLFWwindow *&window);
void setupInputThread();
void setGlViewport(int width, int height);

float deltaTime = 0.0f;
float lastFrame = 0.0f;

float lastX = 400.0f, lastY = 300.0f;
bool rightMouseDown = false, leftMouseDown = false;

glm::mat4 projection = glm::perspective(glm::radians(45.0f), (float)START_WIDTH / START_HEIGHT, 0.1f, 100.0f);
glm::mat4 model = glm::scale(glm::mat4(1.0f), glm::vec3(0.1f));

glm::mat4 quadProjection = glm::ortho(0.0f, 800.0f, 0.0f, 600.0f);

Camera camera;
std::vector<Button> buttons;

std::queue<std::string> inputQueue;


int main() {
    GLFWwindow *window;
    if (setupWindow(window) == -1) return -1;

    setGlViewport(START_WIDTH, START_HEIGHT);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_CULL_FACE);
    glEnable(GL_MULTISAMPLE);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    glPixelStorei(GL_UNPACK_ALIGNMENT, 1);

    stbi_set_flip_vertically_on_load(true);

    Shader fontShader("shaders/fontVertex.glsl", "shaders/fontFragment.glsl");
    Shader quadShader("shaders/fontVertex.glsl", "shaders/quadFragment.glsl");
    Shader planeShader("shaders/planeVertex.glsl", "shaders/planeFragment.glsl");

    Model droney("droney/droney.obj");
    Shader shader("shaders/vertex.glsl", "shaders/fragment.glsl");

    setupInputThread();

    Quader quader;

    float padding = 0.02f;
    float buttonWidth = 0.9f / 6.0f;
    float buttonHeight = 0.05f;
    int i = 0;

    auto makeButton = [&i, buttonWidth, buttonHeight, padding](std::string name) {
        buttons.push_back(Button(buttonWidth / 2 + buttonWidth * i, 1 - buttonHeight / 2 - padding, buttonWidth - padding, buttonHeight, [name] {std::cout << name + "\n";}, name));
        i++;
    };

    makeButton("Arm");
    makeButton("TakeOff");
    makeButton("Play");
    makeButton("Land");
    makeButton("Step");
    makeButton("Halt");

    float vertices[6][3] = {
        {0, 0, 0},
        {1, 0, 0},
        {1, 0, 1},

        {1, 0, 1},
        {0, 0, 1},
        {0, 0, 0},
    };

    unsigned int VAO, VBO;
    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(float) * 3, (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, sizeof(float) * 4, (void*)0);
    glEnableVertexAttribArray(4);

    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * 6 * 3, &vertices[0], GL_STATIC_DRAW);
    glm::vec4 color(0, 1, 0, 1);

    glBindVertexArray(0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);


    droney.setColor(0, 0, 1, 0, 1);
    while (!glfwWindowShouldClose(window)) {
        float currentFrame = glfwGetTime();
        deltaTime = currentFrame - lastFrame;
        lastFrame = currentFrame;

        proccessInput(window);

        while (!inputQueue.empty()) {
            parseInput(droney, inputQueue.front());
            inputQueue.pop();
        }

        glClearColor(0.2f, 0.3f, 0.3f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

        setupShader(shader);
        droney.draw(shader);

        glDisable(GL_CULL_FACE);

        model = glm::translate(glm::mat4(1.0f), glm::vec3(-.5f, -3, -.5f));
        setupShader(planeShader);
        planeShader.setVec3("color", color);

        glBindVertexArray(VAO);
        glDrawArrays(GL_TRIANGLES, 0, 6);

        glEnable(GL_CULL_FACE);

        quader.setup(&fontShader, &quadShader, glm::vec2(width, height));
        for (Button b : buttons) b.draw(quader);
        quader.renderQuad(glm::vec2(0.9f, 0.0f), glm::vec2(1.0f, 1.0f), glm::vec4(0, 0, 0, 1));
        droney.drawInstances(quader);


        glfwSwapBuffers(window);
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
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
                b.checkClick(xpos / width, ypos / height);
            }
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

void setupShader(Shader &shader) {
    shader.use();

    shader.setVec3("viewPos", camera.pos);
    shader.setMat4("view", camera.getViewMatrix());
    shader.setMat4("projection", projection);

    shader.setMat4("model", model);

    glm::mat3 normal = glm::transpose(glm::inverse(model));
    int normalLoc = glGetUniformLocation(shader.ID, "normal");
    glUniformMatrix3fv(normalLoc, 1, GL_FALSE, glm::value_ptr(normal));
}

void parseInput(Model &model, std::string input) {
    int id;
    float minX, minY, minZ, maxX, maxY, maxZ;
    float x, y, z;
    float r, g, b, a;
    int state;
    char ip[21];

    sscanf(input.c_str(), "%d:", &id);
    input = input.substr(2);

    if (sscanf(input.c_str(), "(%f, %f, %f, %f, %f, %f)", &minX, &minY, &minZ, &maxX, &maxY, &maxZ) == 6) {
        model.minPos = glm::vec3(minX, minY, minZ);
        model.maxPos = glm::vec3(maxX, maxY, maxZ);
    } else if (sscanf(input.c_str(), "(%f, %f, %f, %f)", &r, &g, &b, &a) == 4) {
        model.setColor(id, r, g, b, a);
    } else if (sscanf(input.c_str(), "(%f, %f, %f)", &x, &y, &z) == 3) {
        model.setPos(id, x, y, z);
    } else if (sscanf(input.c_str(), "%d.%d.%d.%d:%d", &state, &state, &state, &state, &state) == 5) {
        sscanf(input.c_str(), "%s", ip);
        model.setIp(id, ip);
    } else if (sscanf(input.c_str(), "%d", &state) == 1) {
        model.setState(id, (DroneState)state);
    }
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

void setupInputThread() {
    std::thread thread([] {
        std::string input;
        for (;;) {
            std::getline(std::cin, input);
            if (input.size() > 0) {
                inputQueue.push(input);
            }
        }
    });
    thread.detach();
}

void setGlViewport(int p_width, int p_height) {
    width = p_width;
    height = p_height;

    glViewport(0, 0, width, height);

    p_width -= SIDE_PANEL_SIZE;
    projection = glm::perspective(glm::radians(45.0f), (float)p_width / height, 0.1f, 100.0f);
}
