#ifndef MODEL_H
#define MODEL_H

#include "button.h"
#include "glm/detail/type_vec.hpp"
#include "mesh.h"
#include "quader.h"
#include <cmath>
#include <functional>
#include <set>
#include <string>
#include <unordered_set>
#include <vector>
#include <assimp/scene.h>

class Model {
public:
    Model(const char *path);
    void draw(Shader *shader);

    void addInstance(DroneData droneData);
    void addInstance(int id);
    void setPos(int id, float x, float y, float z);
    void setColor(int id, float r, float g, float b, float a);
    void setState(int id, DroneState state);
    void setIp(int id, char ip[21]);

    void drawInstances(Quader *quader);
    int getNum();

    std::function<void(bool, bool)> curryButton(int idx);
    void setCurrentDrone(int idx, bool shift, bool ctrl);
    void checkButtons(float mousex, float mousey, bool shift, bool ctrl);

    glm::vec3 maxPos = glm::vec3(-100000.0f, -100000.0f, -100000.0f);
    glm::vec3 minPos = glm::vec3(100000.0f, 100000.0f, 100000.0f);
private:

    void loadModel(std::string path);
    void processNode(aiNode *node, const aiScene *scene);
    Mesh processMesh(aiMesh *mesh, const aiScene *scene);
    void resetVBO();

    DroneData* getInstance(int id);
    Button* getButton(int id);
    std::vector<int>::iterator findCurrentDrone(int idx);
    void placeButton();

    unsigned int VBO;

    std::vector<Mesh> meshes;
    std::string directory;
    std::vector<DroneData> droneDatas;
    std::vector<Button> ipButtons;
    std::vector<int> currentDrones;
    Button offButton;
};

#endif
