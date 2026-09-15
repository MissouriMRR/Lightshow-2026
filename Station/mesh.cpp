#include "mesh.h"

#include "shader.h"
#include <cstddef>
#include <vector>
#include <assimp/Importer.hpp>
#include <assimp/scene.h>
#include <assimp/postprocess.h>

Mesh::Mesh(std::vector<Vertex> vertices, std::vector<unsigned int> indices, unsigned int instanceVBO) {
    this->vertices = vertices;
    this->indices = indices;

    setupMesh(instanceVBO);
}

void Mesh::setupMesh(unsigned int instanceVBO) {
    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);
    glGenBuffers(1, &EBO);

    glBindVertexArray(VAO);


    glBindBuffer(GL_ARRAY_BUFFER, VBO);

    glBufferData(GL_ARRAY_BUFFER, vertices.size() * sizeof(Vertex), &vertices[0], GL_STATIC_DRAW);

    glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO);
    glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.size() * sizeof(unsigned int), &indices[0], GL_STATIC_DRAW);

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)0);
    glEnableVertexAttribArray(0);

    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex), (void*)(offsetof(Vertex, Normal)));
    glEnableVertexAttribArray(1);


    glBindBuffer(GL_ARRAY_BUFFER, instanceVBO);

    glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE, sizeof(InstanceDatum), (void*)(offsetof(InstanceDatum, position)));
    glEnableVertexAttribArray(3);
    glVertexAttribDivisor(3, 1);

    glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, sizeof(InstanceDatum), (void*)(offsetof(InstanceDatum, color)));
    glEnableVertexAttribArray(4);
    glVertexAttribDivisor(4, 1);

    glBindVertexArray(0);
}

void Mesh::draw(Shader &shader, int num) {
    glBindVertexArray(VAO);
    glDrawElementsInstanced(GL_TRIANGLES, indices.size(), GL_UNSIGNED_INT, 0, num);
    glBindVertexArray(0);
}
