#ifndef MESH_H
#define MESH_H

#include "glm/detail/type_vec.hpp"
#include "glm/glm.hpp"
#include <string>
#include <vector>

#include "shader.h"

enum class DroneState {
    GROUNDED,
    ARMED,
    LIFTED,
    BETWEEN,
    HAPPY
};

struct DroneData {
    glm::vec3 position;
    glm::vec4 color;
    int id;
    DroneState state;
    char ip[21];
};

struct InstanceDatum {
    glm::vec3 position;
    glm::vec4 color;
};

struct Vertex {
    glm::vec3 Position;
    glm::vec3 Normal;
};

class Mesh {
public:
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;

    Mesh(std::vector<Vertex> vertices, std::vector<unsigned int> indices, unsigned int instanceVBO);
    void draw(Shader &shader, int num);

private:
    unsigned int VAO, VBO, EBO;

    void setupMesh(unsigned int instanceVBO);
};

#endif
