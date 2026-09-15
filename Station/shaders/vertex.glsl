#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoords;
layout (location = 3) in vec3 offset;
layout (location = 4) in vec4 aColor;

out vec3 Normal;
out vec3 FragPos;
out vec2 TexCoords;
out vec4 Color;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat3 normal;

void main() {
    gl_Position = projection * view * model * vec4(aPos + offset, 1.0);
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = normal * aNormal;
    TexCoords = aTexCoords;
    Color = aColor;
}
