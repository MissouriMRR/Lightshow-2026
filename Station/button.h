#ifndef BUTTON_H
#define BUTTON_H

#include <functional>
#include "quader.h"

class Button {
public:
    Button(float xpos, float ypos, float width, float height, std::function<void(void)> function, std::string text) : xpos(xpos), ypos(ypos), width(width), height(height), function(function), text(text), clicked(false) {}

    void checkClick(float mousex, float mousey);
    void draw(Quader q);

    void setClicked(bool clicked);

private:
    float xpos;
    float ypos;
    float width;
    float height;
    std::function<void(void)> function;
    std::string text;

    bool clicked;
};

#endif
