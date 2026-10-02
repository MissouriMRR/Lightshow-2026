#version 330 core

out vec4 FragColor;

in vec2 TexCoords;
in vec3 Normal;
in vec3 FragPos;
in vec4 Color;

uniform vec3 viewPos;

const vec3 lightDir = normalize(vec3(1.0));
const float ambientStrength = 0.2;
const float diffuseStrength = 0.5;
const float specularStrength = 1.0;
const float shininess = 32.0;

void main()
{
    vec3 color = Color.xyz;

    vec3 ambient = ambientStrength * color;

    vec3 norm = normalize(Normal);
    float diff = max(dot(norm, lightDir), 0.0);
    vec3 diffuse = diffuseStrength * diff * color;

    vec3 viewDir = normalize(viewPos - FragPos);
    vec3 reflectDir = reflect(-lightDir, norm);
    float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
    vec3 specular = vec3(spec * specularStrength);

    vec3 result = ambient + diffuse + specular;
    FragColor = vec4(result, Color.a);
};
