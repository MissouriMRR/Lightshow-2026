#include "camera.h"
#include "shader.h"

#ifndef GROUND_H
#define GROUND_H

class Ground {
public:

    Ground();
    void draw(glm::mat4 projection, Camera *camera);
private:
    unsigned int VAO, VBO;
    Shader planeShader;
};

#endif
