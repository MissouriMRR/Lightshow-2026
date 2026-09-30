#ifndef BUTTON_H
#define BUTTON_H

#include <functional>
#include "quader.h"

class Button {
public:
    Button(float xpos, float ypos, float width, float height, std::function<void(bool, bool)> function, std::string text) : xpos(xpos), ypos(ypos), width(width), height(height), function(function), text(text), color(0.5, 0.5, 0.5, 1), textSize(0.3f), textColor(1, 1, 1), priority(0) {}
    Button(std::function<void(bool, bool)> function, std::string text, float textSize) : xpos(0), ypos(0), width(0), height(0), function(function), text(text), color(0.5, 0.5, 0.5, 1), textSize(textSize), textColor(1, 1, 1), priority(0) {}

    bool checkClick(float mousex, float mousey, bool shift, bool ctrl);
    void draw(Quader *q);

    float xpos;
    float ypos;
    float width;
    float height;
    std::function<void(bool, bool)> function;
    std::string text;
    glm::vec4 color;
    float textSize;
    glm::vec3 textColor;
    float priority;
};

#endif
