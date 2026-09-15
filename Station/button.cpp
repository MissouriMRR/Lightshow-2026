#include "button.h"
#include "glm/glm.hpp"
#include "quader.h"
#include <iostream>

void Button::checkClick(float mousex, float mousey) {
    mousey = 1 - mousey;
    if (!clicked 
            && xpos - width / 2 < mousex && mousex < xpos + width / 2
            && ypos - height / 2 < mousey && mousey < ypos + height / 2) {
        function();
        clicked = true;
    }
}

void Button::draw(Quader q) {
    const float brightness = 0.5f;
    q.renderQuad(glm::vec2(xpos - width / 2, ypos - height / 2), glm::vec2(xpos + width / 2, ypos + height / 2), glm::vec4(brightness, brightness, brightness, 1));
    q.renderText(text, xpos, ypos, 0.3f, glm::vec3(1, 1, 1), HCentering::CENTER, VCentering::CENTER, 1);
}

void Button::setClicked(bool clicked) {
    this->clicked = clicked;
}
