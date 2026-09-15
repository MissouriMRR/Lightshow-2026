#ifndef CAMERA_H
#define CAMERA_H

#include "glm/detail/type_vec.hpp"
#include "glm/glm.hpp"
#include "glm/gtc/matrix_transform.hpp"
#include "glm/gtc/quaternion.hpp"
#include <iostream>

class Camera {
public:
    glm::vec3 pos = glm::vec3(0.0f, 0.0f, 10.0f);
    glm::vec3 cameraUp = glm::vec3(0.0f, 1.0f, 0.0f);
    glm::vec3 pointPos = glm::vec3(0.0f);

    float pitch = 0.0f, yaw = 270.0f;

    glm::vec3 getPos() const {
        glm::vec3 isolated = pos - pointPos;
        return pointPos + glm::vec3(cos(glm::radians(yaw)) * cos(glm::radians(pitch)), sin(glm::radians(pitch)), sin(glm::radians(yaw)) * cos(glm::radians(pitch))) * 10.0f;
    }

    glm::vec3 getCameraFront() const {
        return glm::normalize(pointPos - getPos());
    }

    glm::vec3 getCameraRight() const {
        return glm::normalize(glm::cross(getCameraFront(), cameraUp));
    }

    glm::vec3 getCameraUp() const {
        return glm::normalize(glm::cross(getCameraRight(), getCameraFront()));
    }

    void translate(glm::vec3 transformBy) {
        const float sensitivity = 0.1f;
        glm::vec3 translation = sensitivity * (transformBy.z * getCameraFront()
            + transformBy.x * getCameraRight()
            + transformBy.y * getCameraUp());
        pointPos += translation;
        pos += translation;
    }

    void rotate(float yawBy, float pitchBy) {
        const float sensitivity = 0.25f;

        yaw -= yawBy * sensitivity;
        pitch += pitchBy * sensitivity;

        if (pitch > 89.0f) pitch = 89.0f;
        if (pitch < -89.0f) pitch = -89.0f;
    }

    void translate(float xBy, float yBy) {
        pos += getCameraRight() * xBy + cameraUp * yBy;
    }

    glm::mat4 getViewMatrix() {
        return glm::lookAt(getPos(), getPos() + getCameraFront(), glm::vec3(0, 1, 0));
        // glm::mat4 camera(1.0f);
        // camera = glm::rotate(camera, glm::radians(pitch), getCameraRight());
        // // camera = glm::rotate(camera, glm::radians(-yaw), cameraUp);
        // camera = glm::translate(camera, -pos);
        // return camera;
        // // return glm::lookAt(pos, pos + getCameraFront(), cameraUp);
    }
};

#endif
