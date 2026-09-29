#ifndef MAIN_H
#define MAIN_H

#include <glm/common.hpp>
#include <string>
#include "glad/glad.h"
#include <GLFW/glfw3.h>

#include "shader.h"

enum class LoopReturn {
    NOTHING,
    ARM,
    TAKEOFF,
    STEP,
    LAND,
    HALT
};

void framebufferSizeCallback(GLFWwindow* window, int width, int height);
void proccessInput(GLFWwindow* window);
void mouse_callback(GLFWwindow* window, double xpos, double ypos);
void setupShader(Shader *shader);
void parseInput(std::string input);
int setupWindow(GLFWwindow *&window);
void setGlViewport(int width, int height);


int setup();
LoopReturn loop();
void cleanup();
bool shouldClose();
void setExpanse(glm::vec3 min, glm::vec3 max);

void setColor(int id, float r, float g, float b, float a);
void setPos(int id, float x, float y, float z);
void setIp(int id, std::string ip);
void setState(int id, int state);

#endif
