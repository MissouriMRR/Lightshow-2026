#include "model.h"
#include "assimp/vector3.h"
#include "glm/detail/type_vec.hpp"

#include <algorithm>
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

const float buttonHeight = 0.02f;
const float buttonWidth = 0.1f;

Model::Model(const char *path) : meshes(), droneDatas(), ipButtons(), currentDrones(), offButton(Button([this](bool, bool) {currentDrones.clear();}, "", 0.0f)) {
    VBO = 0;
    glGenBuffers(1, &VBO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, droneDatas.size() * sizeof(DroneData), &(droneDatas[0]), GL_STATIC_DRAW);

    offButton.xpos = 0.95f;
    offButton.ypos = 0.5f - buttonHeight * 0.5f;
    offButton.width = buttonWidth;
    offButton.height = 1.0f;

    loadModel(path);
}

void Model::draw(Shader *shader) {
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
    ipButtons.push_back(Button(curryButton(droneDatas.size()), droneData.ip, 0.15f));
    droneDatas.push_back(droneData);
    placeButton();
    resetVBO();
}

void Model::addInstance(int id) {
    addInstance(DroneData{
        glm::vec3(0, 0, 0),
        glm::vec4((float)rand() / RAND_MAX, (float)rand() / RAND_MAX, (float)rand() / RAND_MAX, 0.0),
        id,
        DroneState::DISCONNECTED,
        "999.999.999.999:9999",
    });
}

DroneData* Model::getInstance(int id) {
    for (int i = 0; i < droneDatas.size(); i++) {
        if (droneDatas[i].id == id) return &droneDatas[i];
    }
    return nullptr;
}

Button* Model::getButton(int id) {
    for (int i = 0; i < droneDatas.size(); i++) {
        if (droneDatas[i].id == id) return &ipButtons[i];
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

    getInstance(id)->color.a = state != DroneState::DISCONNECTED;
    resetVBO();
    getInstance(id)->state = state;
}

void Model::setIp(int id, char ip[21]) {
    if (getInstance(id) == nullptr) addInstance(id);

    getButton(id)->text = ip;
    for (int i = 0; i < 21; i++) {
        getInstance(id)->ip[i] = ip[i];
    }
}

void Model::resetVBO() {
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, droneDatas.size() * sizeof(DroneData), &droneDatas[0], GL_STATIC_DRAW);
}

void Model::placeButton() {
    int idx = droneDatas.size() - 1;
    Button &toAdd = ipButtons[idx];

    toAdd.priority = 0.1;
    toAdd.xpos = 0.95f;
    toAdd.ypos = 0.98f - idx * 0.02f;
    toAdd.width = buttonWidth;
    toAdd.height = buttonHeight;

    offButton.height -= buttonHeight;
    offButton.ypos -= buttonHeight * 0.5f;
}

void Model::drawInstances(Quader *quader) {
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

int Model::getNum() {
    return droneDatas[0].color.a;
}

std::function<void(bool, bool)> Model::curryButton(int idx) {
    return [this, idx](bool shift, bool ctrl) {setCurrentDrone(idx, shift, ctrl);};
}

std::vector<int>::iterator Model::findCurrentDrone(int idx) {
    return std::find(currentDrones.begin(), currentDrones.end(), idx);
}

void Model::setCurrentDrone(int idx, bool shift, bool ctrl) {
    int lastIdx = currentDrones.size() > 0 ? currentDrones[currentDrones.size() - 1] : -1;

    auto idxLoc = findCurrentDrone(idx);
    bool adding = idxLoc == currentDrones.end() || currentDrones.size() > 0;

    if (!shift) {
        currentDrones.clear();
    }

    if (ctrl && lastIdx != -1) {
        if (lastIdx > idx) {
            int tmp = lastIdx;
            lastIdx = idx;
            idx = tmp;
        }

        for (int i = lastIdx; i < idx; i++) {
            std::vector<int>::iterator it = findCurrentDrone(i);

            if (it == currentDrones.end()) currentDrones.push_back(i);
        }
    }

    if (adding) currentDrones.push_back(idx);
    else if (shift) currentDrones.erase(idxLoc);
}

void Model::checkButtons(float mousex, float mousey, bool shift, bool ctrl) {
    for (Button b : ipButtons) {
        b.setClicked(false);
        b.checkClick(mousex, mousey, shift, ctrl);
    }
    offButton.setClicked(false);
    offButton.checkClick(mousex, mousey, shift, ctrl);
}
