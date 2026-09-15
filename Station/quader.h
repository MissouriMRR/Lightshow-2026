#ifndef QUADER_H
#define QUADER_H

#include "glm/glm.hpp"
#include "shader.h"

#include "glm/detail/type_vec.hpp"
#include <string>

#include <map>
#include "glm/glm.hpp"
#include "shader.h"

struct Character {
    unsigned int textureID;
    glm::ivec2 size;
    glm::ivec2 bearing;
    unsigned int advance;
};

enum class HCentering {
    CENTER,
    LEFT,
    RIGHT
};

enum class VCentering {
    CENTER,
    TOP,
    BOTTOM
};

class Quader {
public:
    Quader();
    void setup(Shader *fontShader, Shader *quadShader, glm::vec2 windowSize);
    void renderQuad(glm::vec2 bottomCorner, glm::vec2 topCorner, glm::vec4 color = glm::vec4(1, 1, 1, 1), float priority = 0);
    void renderText(std::string text, float x, float y, float scale, glm::vec3 color, HCentering centerType = HCentering::LEFT, VCentering vCenterType = VCentering::BOTTOM, float priority = 0);

private:
    unsigned int VAO, VBO, EBO;
    glm::vec2 windowSize;
    Shader *fontShader;
    Shader *quadShader;
};

#endif
