#include "quader.h"

#include <GLFW/glfw3.h>
#include "shader.h"
#include <iostream>

#include <glad/glad.h>
#include <iterator>
#include "glm/gtc/matrix_transform.hpp"

#include "ft2build.h"
#include FT_FREETYPE_H

std::map<char, Character> characters;
std::map<char, Character> smallCharacters;
unsigned int VAO, VBO;

const static int smallSize = 9;
const static int largeSize = 48;

Quader::Quader() {
    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);

    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindVertexArray(0);

    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * 6 * 4, NULL, GL_DYNAMIC_DRAW);
    glBindBuffer(GL_ARRAY_BUFFER, 0);

    FT_Library ft;
    if (FT_Init_FreeType(&ft)) {
        std::cout << "Failed to init freetype\n";
    }

    FT_Face face;
    if (FT_New_Face(ft, "fonts/arial.ttf", 0, &face)) {
        std::cout << "Failed to load font\n";
    }

    FT_Set_Pixel_Sizes(face, 0, largeSize);

    for (unsigned char c = 0; c < 128; c++) {
        if (FT_Load_Char(face, c, FT_LOAD_RENDER)) {
            std::cout << "Failed to load glyph " << c << "\n";
            continue;
        }

        unsigned int texture;
        glGenTextures(1, &texture);
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RED,
            face->glyph->bitmap.width,
            face->glyph->bitmap.rows,
            0,
            GL_RED,
            GL_UNSIGNED_BYTE,
            face->glyph->bitmap.buffer
        );

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

        characters.insert(std::pair<char, Character>(c, Character{
            texture,
            glm::ivec2(face->glyph->bitmap.width, face->glyph->bitmap.rows),
            glm::ivec2(face->glyph->bitmap_left, face->glyph->bitmap_top),
            (unsigned int)face->glyph->advance.x
        }));
    }

    FT_Set_Pixel_Sizes(face, 0, smallSize);

    for (unsigned char c = 0; c < 128; c++) {
        if (FT_Load_Char(face, c, FT_LOAD_RENDER)) {
            std::cout << "Failed to load glyph " << c << "\n";
            continue;
        }

        unsigned int texture;
        glGenTextures(1, &texture);
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RED,
            face->glyph->bitmap.width,
            face->glyph->bitmap.rows,
            0,
            GL_RED,
            GL_UNSIGNED_BYTE,
            face->glyph->bitmap.buffer
        );

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

        smallCharacters.insert(std::pair<char, Character>(c, Character{
            texture,
            glm::ivec2(face->glyph->bitmap.width, face->glyph->bitmap.rows),
            glm::ivec2(face->glyph->bitmap_left, face->glyph->bitmap_top),
            (unsigned int)face->glyph->advance.x
        }));
    }

    FT_Done_Face(face);
    FT_Done_FreeType(ft);

    glGenVertexArrays(1, &VAO);
    glGenBuffers(1, &VBO);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferData(GL_ARRAY_BUFFER, sizeof(float) * 6 * 4, NULL, GL_DYNAMIC_DRAW);
    glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * sizeof(float), (void*)0);
    glEnableVertexAttribArray(0);

    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glBindVertexArray(0);
}

void Quader::setup(Shader *fontShader, Shader *quadShader, glm::vec2 windowSize) {
    this->windowSize = windowSize;
    this->fontShader = fontShader;
    this->quadShader = quadShader;
}

void Quader::renderQuad(glm::vec2 bottomCorner, glm::vec2 topCorner, glm::vec4 color, float priority) {
    quadShader->use();
    quadShader->setMat4("projection", glm::ortho(0.0f, windowSize.x, 0.0f, windowSize.y));
    quadShader->setFloat("z", priority);

    bottomCorner *= windowSize;
    topCorner *= windowSize;

    float vertices[6][4] = {
        {bottomCorner.x, topCorner.y},
        {bottomCorner.x, bottomCorner.y},
        {topCorner.x, bottomCorner.y},

        {bottomCorner.x, topCorner.y},
        {topCorner.x, bottomCorner.y},
        {topCorner.x, topCorner.y},
    };

    quadShader->setVec4("textColor", color);

    glBindVertexArray(VAO);
    glBindBuffer(GL_ARRAY_BUFFER, VBO);
    glBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(vertices), vertices);
    glBindBuffer(GL_ARRAY_BUFFER, 0);

    glDrawArrays(GL_TRIANGLES, 0, 6);
}

void Quader::renderText(std::string text, float x, float y, float scale, glm::vec3 color, HCentering hCenterType, VCentering vCenterType, float priority) {
    fontShader->use();
    fontShader->setMat4("projection", glm::ortho(0.0f, windowSize.x, 0.0f, windowSize.y));
    fontShader->setVec3("textColor", color);
    fontShader->setFloat("z", priority);
    glActiveTexture(GL_TEXTURE0);
    glBindVertexArray(VAO);

    x *= windowSize.x;
    y *= windowSize.y;
    scale *= windowSize.x / 800.0f;

    std::map<char, Character> chars = characters;
    if (scale <= 0.3) {
        scale *= (float)largeSize / smallSize;
        chars = smallCharacters;
    }

    if (hCenterType == HCentering::CENTER) {
        float width = 0;
        for (std::string::const_iterator c = text.begin(); c != text.end(); c++) {
            width += (chars[*c].advance >> 6) * scale;
        }
        x -= width / 2;
    }
    if (vCenterType == VCentering::CENTER) {
        float height = 0;
        for (std::string::const_iterator c = text.begin(); c != text.end(); c++) {
            height += (chars[*c].advance >> 6) * scale;
        }
        height /= text.size();
        y -= height / 2;
    }

    std::string::const_iterator c = hCenterType == HCentering::RIGHT ? text.end() - 1 : text.begin();
    auto end = hCenterType == HCentering::RIGHT ? text.begin() - 1 : text.end();
    int hCenterSign = hCenterType == HCentering::RIGHT ? -1 : 1;
    int vCenterSign = vCenterType == VCentering::TOP ? -1 : 1;

    for (; c != end; c += hCenterSign) {
        Character ch = chars[*c];

        float xPos = x + ch.bearing.x * scale * hCenterSign;
        float yPos = y - (ch.size.y - ch.bearing.y) * scale * vCenterSign;

        float w = ch.size.x * scale;
        float h = ch.size.y * scale;

        float vertices[6][4] = {
            {xPos, yPos + h, 0.0f, 0.0f},
            {xPos, yPos, 0.0f, 1.0f},
            {xPos + w, yPos, 1.0f, 1.0f},

            {xPos, yPos + h, 0.0f, 0.0f},
            {xPos + w, yPos, 1.0f, 1.0f},
            {xPos + w, yPos + h, 1.0f, 0.0f},
        };

        glBindTexture(GL_TEXTURE_2D, ch.textureID);
        glBindBuffer(GL_ARRAY_BUFFER, VBO);
        glBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(vertices), vertices);
        glBindBuffer(GL_ARRAY_BUFFER, 0);

        glDrawArrays(GL_TRIANGLES, 0, 6);

        x += (ch.advance >> 6) * scale * hCenterSign;
    }
    glBindVertexArray(0);
}
