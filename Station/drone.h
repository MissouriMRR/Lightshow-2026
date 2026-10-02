#ifndef MODEL_H
#define MODEL_H

#include "button.h"
#include "camera.h"
#include "glm/detail/type_mat.hpp"
#include "glm/detail/type_vec.hpp"
#include "mesh.h"
#include "quader.h"
#include <assimp/scene.h>
#include <cmath>
#include <functional>
#include <set>
#include <string>
#include <unordered_set>
#include <vector>

class Drone {
  public:
    Drone();
    Drone(std::string path);
    void draw(Shader *shader);

    void addInstance(DroneData droneData);
    void addInstance(int id);
    void setPos(int id, float x, float y, float z);
    void setColor(int id, float r, float g, float b, float a);
    void setState(int id, DroneState state);
    void setIp(int id, std::string ip);

    void drawInstances(Quader *quader, glm::mat4 projection, Camera *camera);
    int getNum();

    std::function<void(bool, bool)> curryButton(int idx);
    void setCurrentDrone(int idx, bool shift, bool ctrl);
    void resetCurrentDrones();
    bool checkButtons(float mousex, float mousey, bool shift, bool ctrl);
    bool checkDrones(float mousex, float mousey, bool shift, bool ctrl, Camera *camera, glm::mat4 projection);

    glm::vec3 maxPos = glm::vec3(-100000.0f, -100000.0f, -100000.0f);
    glm::vec3 minPos = glm::vec3(100000.0f, 100000.0f, 100000.0f);
    std::vector<int> currentDrones;
    std::vector<DroneData> droneDatas;

  private:
    void loadModel(std::string path);
    void processNode(aiNode *node, const aiScene *scene);
    Mesh processMesh(aiMesh *mesh, const aiScene *scene);
    void resetVBO();

    DroneData *getInstance(int id);
    Button *getButton(int id);
    std::vector<int>::iterator findCurrentDrone(int idx);
    void placeButton();

    unsigned int VBO;

    std::vector<Mesh> meshes;
    std::string directory;
    std::vector<Button> ipButtons;
    int lastIdx = -1;
};

#endif
