#include "button.h"
#include "quader.h"

bool Button::checkClick(float mousex, float mousey, bool shift, bool ctrl) {
    mousey = 1 - mousey;
    if (xpos - width / 2 < mousex && mousex < xpos + width / 2 && ypos - height / 2 < mousey &&
        mousey < ypos + height / 2) {
        function(shift, ctrl);
        return true;
    } else {
        return false;
    }
}

void Button::draw(Quader *q) {
    q->renderQuad(glm::vec2(xpos - width / 2, ypos - height / 2), glm::vec2(xpos + width / 2, ypos + height / 2), color,
                  priority);
    q->renderText(text, xpos, ypos, textSize, textColor, HCentering::CENTER, VCentering::CENTER, priority + 0.1);
}
