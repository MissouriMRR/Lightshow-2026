#include "ground.h"
#include "glad/glad.h"
#include "glm/glm.hpp"
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtc/type_ptr.hpp>

Ground::Ground() : planeShader("shaders/planeVertex.glsl", "shaders/planeFragment.glsl") {
    float vertices[6][3] = {
        {0, 0, 0},
        {1, 0, 0},
        {1, 0, 1},

        {1, 0, 1},
        {0, 0, 1},
        {0, 0, 0},
    };

    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);

    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(float) * 3, (void*)0);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(4, 3, GL_FLOAT, GL_FALSE, sizeof(float) * 4, (void*)0);
    glEnableVertexAttribArray(4);

    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * 6 * 3, &vertices[0], GL_STATIC_DRAW);

    glBindVertexArray(0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
}

void Ground::draw(glm::mat4 projection, Camera *camera) {
        glDisable(GL_CULL_FACE);

        planeShader.use();

        planeShader.setVec3("color", glm::vec4(0, 1, 0, 1));

        planeShader.setVec3("viewPos", camera->pos);
        planeShader.setMat4("view", camera->getViewMatrix());
        planeShader.setMat4("projection", projection);

        glm::mat4 model = glm::translate(glm::mat4(1.0f), glm::vec3(-.5f, -0.01f, -.5f));
        planeShader.setMat4("model", model);

        glm::mat3 normal = glm::transpose(glm::inverse(model));
        int normalLoc = glGetUniformLocation(planeShader.ID, "normal");
        glUniformMatrix3fv(normalLoc, 1, GL_FALSE, glm::value_ptr(normal));

        glBindVertexArray(VAO);
        glDrawArrays(GL_TRIANGLES, 0, 6);

        glEnable(GL_CULL_FACE);
}
