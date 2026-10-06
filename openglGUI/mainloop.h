/*
 * mainloop.h
 * Defines mainloop functions
 */

#ifndef MAINLOOP_H
#define MAINLOOP_H

#include "drone.h"
#include "glad/glad.h"
#include <GLFW/glfw3.h>
#include <glm/common.hpp>
#include <string>

#include "shader.h"

extern Drone *droney;

enum class LoopReturn { NOTHING, ARM, TAKEOFF, STEP, LAND, HALT };

void framebufferSizeCallback(GLFWwindow *window, int width, int height);
void proccessInput(GLFWwindow *window);
void mouseCallback(GLFWwindow *window, double xpos, double ypos);
void setupShader(Shader *shader);
void parseInput(std::string input);
int setupWindow(GLFWwindow *&window);
void setGlViewport(int width, int height);
void getScaledCursorPos(GLFWwindow *window, double *xpos, double *ypos);

int setup();
LoopReturn loop();
void cleanup();
bool shouldClose();
void setExpanse(glm::vec3 min, glm::vec3 max);

void setColor(int id, float r, float g, float b, float a);
void setPos(int id, float x, float y, float z);
void setIp(int id, std::string ip);
void setState(int id, DroneState state);

#endif
