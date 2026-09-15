#include "model.h"
#include "assimp/vector3.h"
#include "glm/detail/type_vec.hpp"

#include <assimp/Importer.hpp>
#include <assimp/scene.h>
#include <assimp/postprocess.h>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <istream>
#include <ostream>
#include <string>
#include <vector>

#include "mesh.h"
#include "shader.h"
#include "stb_image.h"
#include "utils.h"

Model::Model(const char *path) : meshes(), droneDatas() {
    VBO = 0;
    glGenBuffers(1, &VBO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, droneDatas.size() * sizeof(DroneData), &(droneDatas[0]), GL_STATIC_DRAW);

    loadModel(path);
}

void Model::draw(Shader& shader) {
    for (unsigned int i = 0; i < meshes.size(); i++) {
        meshes[i].draw(shader, droneDatas.size());
    }
}

void Model::loadModel(std::string path) {
    Assimp::Importer importer;
    const aiScene *scene = importer.ReadFile(path, aiProcess_Triangulate | aiProcess_FlipUVs);

    if (!scene || scene->mFlags & AI_SCENE_FLAGS_INCOMPLETE || !scene->mRootNode) {
        std::cout << "Assimp error\n" << importer.GetErrorString() << std::endl;
        return;
    }

    directory = path.substr(0, path.find_last_of('/'));
    processNode(scene->mRootNode, scene);
}

void Model::processNode(aiNode *node, const aiScene *scene) {
    for (unsigned int i = 0; i < node->mNumMeshes; i++) {
        aiMesh *mesh = scene->mMeshes[node->mMeshes[i]];
        meshes.push_back(processMesh(mesh, scene));
    }

    for (unsigned int i = 0; i < node->mNumChildren; i++) {
        processNode(node->mChildren[i], scene);
    }
}

Mesh Model::processMesh(aiMesh *mesh, const aiScene *scene) {
    std::vector<Vertex> vertices;
    std::vector<unsigned int> indices;

    for (unsigned int i = 0; i < mesh->mNumVertices; i++) {
        Vertex vertex;

        aiVector3D vertexPositions = mesh->mVertices[i];
        vertex.Position = glm::vec3(vertexPositions.x, vertexPositions.y, vertexPositions.z);

        if (mesh->HasNormals()) {
            aiVector3D vertexNormals = mesh->mNormals[i];
            vertex.Normal = glm::vec3(vertexNormals.x, vertexNormals.y, vertexNormals.z);
        }

        vertices.push_back(vertex);
    }

    for (unsigned int i = 0; i < mesh->mNumFaces; i++) {
        aiFace face = mesh->mFaces[i];
        for (unsigned int j = 0; j < face.mNumIndices; j++) indices.push_back(face.mIndices[j]);
    }

    return Mesh(vertices, indices, VBO);
}

void Model::addInstance(DroneData droneData) {
    droneDatas.push_back(droneData);
    resetVBO();
}

void Model::addInstance(int id) {
    addInstance(DroneData{
        glm::vec3(0, 0, 0),
        glm::vec4((float)rand() / RAND_MAX, (float)rand() / RAND_MAX, (float)rand() / RAND_MAX, 1),
        id,
        DroneState::GROUNDED,
        "999.999.999.999:9999",
    });
}

DroneData* Model::getInstance(int id) {
    for (int i = 0; i < droneDatas.size(); i++) {
        if (droneDatas[i].id == id) return &droneDatas[i];
    }
    return nullptr;
}

void Model::setPos(int id, float x, float y, float z) {
    if (getInstance(id) == nullptr) addInstance(id);

    getInstance(id)->position = glm::vec3(x, y, z);
    resetVBO();
}

void Model::setColor(int id, float r, float g, float b, float a) {
    if (getInstance(id) == nullptr) addInstance(id);

    getInstance(id)->color = glm::vec4(r, g, b, a);
    resetVBO();
}

void Model::setState(int id, DroneState state) {
    if (getInstance(id) == nullptr) addInstance(id);

    getInstance(id)->state = state;
}

void Model::setIp(int id, char ip[16]) {
    if (getInstance(id) == nullptr) addInstance(id);

    for (int i = 0; i < 16; i++) {
        getInstance(id)->ip[i] = ip[i];
    }
}

void Model::resetVBO() {
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, droneDatas.size() * sizeof(DroneData), &droneDatas[0], GL_STATIC_DRAW);
}

void Model::drawInstances(Quader quader) {
    for (int i = 0; i < droneDatas.size(); i++) {
        glm::vec3 color;
        switch (droneDatas[i].state) {
            case DroneState::GROUNDED:
                color = glm::vec3(1, 0, 0);
            break;

            case DroneState::ARMED:
                color = glm::vec3(1, 1, 0);
            break;

            default:
                color = glm::vec3(0, 1, 0);
            break;
        }

        quader.renderText(droneDatas[i].ip, 0.95f, 0.98f - i * 0.02f, 0.15f, color, HCentering::CENTER, VCentering::BOTTOM, 1.0f);
    }
}

