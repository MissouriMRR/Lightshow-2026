#include "drone.h"
#include "assimp/vector3.h"
#include "glm/detail/type_vec.hpp"

#include <algorithm>
#include <assimp/Importer.hpp>
#include <assimp/postprocess.h>
#include <assimp/scene.h>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <istream>
#include <ostream>
#include <ranges>
#include <string>
#include <tuple>
#include <vector>

#include "glm/gtc/matrix_transform.hpp"
#include "mesh.h"
#include "shader.h"
#include "stb_image.h"
#include "utils.h"

const float buttonHeight = 0.02f;
const float buttonWidth = 0.1f;

Drone::Drone() : meshes(), droneDatas(), ipButtons(), currentDrones() {}

Drone::Drone(std::string path) : meshes(), droneDatas(), ipButtons(), currentDrones() {
    VBO = 0;
    glGenBuffers(1, &VBO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, droneDatas.size() * sizeof(DroneData), &(droneDatas[0]), GL_STATIC_DRAW);

    loadModel(path);
}

void Drone::draw(Shader *shader) {
    for (unsigned int i = 0; i < meshes.size(); i++) {
        meshes[i].draw(shader, droneDatas.size());
    }
}

void Drone::loadModel(std::string path) {
    Assimp::Importer importer;
    const aiScene *scene = importer.ReadFile(path, aiProcess_Triangulate | aiProcess_FlipUVs);

    if (!scene || scene->mFlags & AI_SCENE_FLAGS_INCOMPLETE || !scene->mRootNode) {
        std::cout << "Assimp error\n" << importer.GetErrorString() << std::endl;
        return;
    }

    directory = path.substr(0, path.find_last_of('/'));
    processNode(scene->mRootNode, scene);
}

void Drone::processNode(aiNode *node, const aiScene *scene) {
    for (unsigned int i = 0; i < node->mNumMeshes; i++) {
        aiMesh *mesh = scene->mMeshes[node->mMeshes[i]];
        meshes.push_back(processMesh(mesh, scene));
    }

    for (unsigned int i = 0; i < node->mNumChildren; i++) {
        processNode(node->mChildren[i], scene);
    }
}

Mesh Drone::processMesh(aiMesh *mesh, const aiScene *scene) {
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

void Drone::addInstance(DroneData droneData) {
    ipButtons.push_back(Button(curryButton(droneDatas.size()), droneData.ip, 0.15f));
    droneDatas.push_back(droneData);
    placeButton();
    resetVBO();
}

void Drone::addInstance(int id) {
    addInstance(DroneData{
        glm::vec3(0, 0, 0),
        glm::vec4((float)rand() / RAND_MAX, (float)rand() / RAND_MAX, (float)rand() / RAND_MAX, 0.0),
        id,
        DroneState::DISCONNECTED,
        "999.999.999.999:9999",
    });
}

DroneData *Drone::getInstance(int id) {
    for (int i = 0; i < droneDatas.size(); i++) {
        if (droneDatas[i].id == id) return &droneDatas[i];
    }
    return nullptr;
}

Button *Drone::getButton(int id) {
    for (int i = 0; i < droneDatas.size(); i++) {
        if (droneDatas[i].id == id) return &ipButtons[i];
    }
    return nullptr;
}

void Drone::setPos(int id, float x, float y, float z) {
    if (getInstance(id) == nullptr) addInstance(id);

    getInstance(id)->position = glm::vec3(x, y, z);
    resetVBO();
}

void Drone::setColor(int id, float r, float g, float b, float a) {
    if (getInstance(id) == nullptr) addInstance(id);

    getInstance(id)->color = glm::vec4(r, g, b, a);
    resetVBO();
}

void Drone::setState(int id, DroneState state) {
    if (getInstance(id) == nullptr) addInstance(id);

    getInstance(id)->color.a = state != DroneState::DISCONNECTED;
    resetVBO();
    getInstance(id)->state = state;
}

void Drone::setIp(int id, std::string ip) {
    if (getInstance(id) == nullptr) addInstance(id);

    getButton(id)->text = ip;
    getInstance(id)->ip = ip;
}

void Drone::resetVBO() {
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, droneDatas.size() * sizeof(DroneData), &droneDatas[0], GL_STATIC_DRAW);
}

void Drone::placeButton() {
    int idx = droneDatas.size() - 1;
    Button &toAdd = ipButtons[idx];

    toAdd.priority = 0.1;
    toAdd.xpos = 0.95f;
    toAdd.ypos = 0.98f - idx * 0.02f;
    toAdd.width = buttonWidth;
    toAdd.height = buttonHeight;
}

void Drone::drawInstances(Quader *quader, glm::mat4 projection, Camera *camera) {
    for (int i = 0; i < droneDatas.size(); i++) {
        glm::vec3 color;
        switch (droneDatas[i].state) {
        case DroneState::DISCONNECTED:
            color = glm::vec3(1, 0, 0);
            break;

        case DroneState::CONNECTED:
            color = glm::vec3(1, 1, 0);
            break;

        case DroneState::ARMED:
            color = glm::vec3(0, 1, 0);
            break;
        }
        ipButtons[i].textColor = color;
        ipButtons[i].color = findCurrentDrone(i) == currentDrones.end() ? glm::vec4(0, 0, 0, 1) : glm::vec4(1, 1, 0, 1);
        ipButtons[i].draw(quader);
    }
}

int Drone::getNum() { return droneDatas[0].color.a; }

std::function<void(bool, bool)> Drone::curryButton(int idx) {
    return [this, idx](bool shift, bool ctrl) { setCurrentDrone(idx, shift, ctrl); };
}

std::vector<int>::iterator Drone::findCurrentDrone(int idx) {
    return std::find(currentDrones.begin(), currentDrones.end(), idx);
}

void Drone::setCurrentDrone(int idx, bool shift, bool ctrl) {
    auto idxLoc = findCurrentDrone(idx);

    if (!shift) {
        currentDrones.clear();
    }

    if (ctrl && lastIdx != -1) {
        for (int i = std::min(lastIdx, idx); i <= std::max(lastIdx, idx); i++) {
            std::vector<int>::iterator it = findCurrentDrone(i);

            if (it == currentDrones.end()) currentDrones.push_back(i);
        }
    } else {
        if (idxLoc != currentDrones.end() && shift && !ctrl) currentDrones.erase(idxLoc);
        else
            currentDrones.push_back(idx);
    }

    lastIdx = idx;
}

bool Drone::checkButtons(float mousex, float mousey, bool shift, bool ctrl) {
    bool out = false;

    for (Button b : ipButtons) {
        out |= b.checkClick(mousex, mousey, shift, ctrl);
    }

    return out;
}

bool Drone::checkDrones(float mousex, float mousey, bool shift, bool ctrl, Camera *camera, glm::mat4 projection) {
    bool out = false;

    mousey = 1.0f - mousey;
    glm::mat4 cameraMat = camera->getViewMatrix();
    glm::mat4 rotlessCamera = glm::mat4(1.0f);
    rotlessCamera[3][0] = cameraMat[3][0];
    rotlessCamera[3][1] = cameraMat[3][1];
    rotlessCamera[3][2] = cameraMat[3][2];
    rotlessCamera[3][3] = cameraMat[3][3];

    std::vector<std::tuple<glm::vec4, glm::vec4, int>> positions;
    for (int i = 0; i < droneDatas.size(); i++) {
        glm::vec3 point = camera->getViewMatrix() *
                          glm::translate(glm::scale(glm::mat4(1.0f), glm::vec3(0.1f)), droneDatas[i].position) *
                          glm::vec4(0, 0, 0, 1);

        float boxSize = 0.3;
        glm::vec4 result = projection * (glm::vec4(point, 0) + glm::vec4(-boxSize, -boxSize, 0, 1));
        result /= result.w;
        result += glm::vec4(1.0);
        result *= 0.5f;
        glm::vec4 result2 = projection * (glm::vec4(point, 0) + glm::vec4(boxSize, boxSize, 0, 1));
        result2 /= result2.w;
        result2 += glm::vec4(1.0);
        result2 *= 0.5f;
        positions.push_back(std::make_tuple(result, result2, i));
    }

    std::sort(positions.begin(), positions.end(), [](auto a, auto b) { return std::get<0>(b).z > std::get<0>(a).z; });
    for (auto [result, result2, i] : positions) {
        if (result.x < mousex && mousex < result2.x && result.y < mousey && mousey < result2.y) {
            setCurrentDrone(i, shift, false);
            out = true;
            break;
        }
    }

    return out;
}

void Drone::resetCurrentDrones() { currentDrones.clear(); }
