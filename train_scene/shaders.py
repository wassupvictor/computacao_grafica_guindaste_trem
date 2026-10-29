"""Shaders GLSL para iluminacao, textura e shadow mapping."""

VERTEX_SHADER = """#version 330 core
layout(location = 0) in vec3 aPosition;
layout(location = 1) in vec3 aNormal;
layout(location = 2) in vec2 aTexCoord;
uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProjection;
uniform mat4 uLightSpace;
out vec3 vWorldPosition;
out vec3 vWorldNormal;
out vec2 vTexCoord;
out vec4 vShadowPosition;
void main() {
    vec4 worldPosition = uModel * vec4(aPosition, 1.0);
    vWorldPosition = worldPosition.xyz;
    vWorldNormal = mat3(transpose(inverse(uModel))) * aNormal;
    vTexCoord = aTexCoord;
    vShadowPosition = uLightSpace * worldPosition;
    gl_Position = uProjection * uView * worldPosition;
}
"""

FRAGMENT_SHADER = """#version 330 core
in vec3 vWorldPosition;
in vec3 vWorldNormal;
in vec2 vTexCoord;
in vec4 vShadowPosition;
uniform vec3 uBaseColor;
uniform vec3 uLightDirection;
uniform vec3 uCameraPosition;
uniform float uShininess;
uniform float uEmissive;
uniform float uAlpha;
uniform bool uUseTexture;
uniform sampler2D uColorTexture;
uniform sampler2D uShadowMap;
out vec4 fragColor;
float shadowAmount(vec3 normal, vec3 lightDirection) {
    vec3 projected = vShadowPosition.xyz / vShadowPosition.w;
    projected = projected * 0.5 + 0.5;
    if (projected.z > 1.0 || projected.x < 0.0 || projected.x > 1.0 ||
        projected.y < 0.0 || projected.y > 1.0) return 0.0;
    float bias = max(0.0015 * (1.0 - dot(normal, lightDirection)), 0.00035);
    vec2 texel = 1.0 / vec2(textureSize(uShadowMap, 0));
    float shadow = 0.0;
    for (int x = -1; x <= 1; ++x) {
        for (int y = -1; y <= 1; ++y) {
            float closestDepth = texture(uShadowMap, projected.xy + vec2(x, y) * texel).r;
            shadow += projected.z - bias > closestDepth ? 1.0 : 0.0;
        }
    }
    return shadow / 9.0;
}
void main() {
    vec3 base = uBaseColor;
    if (uUseTexture) base *= texture(uColorTexture, vTexCoord).rgb;
    vec3 normal = normalize(vWorldNormal);
    vec3 lightDirection = normalize(-uLightDirection);
    float diffuse = max(dot(normal, lightDirection), 0.0);
    vec3 viewDirection = normalize(uCameraPosition - vWorldPosition);
    vec3 reflected = reflect(-lightDirection, normal);
    float specular = pow(max(dot(viewDirection, reflected), 0.0), uShininess) * 0.22;
    float shadow = shadowAmount(normal, lightDirection);
    vec3 color = base * (0.24 + (1.0 - shadow) * diffuse * 0.76);
    color += (1.0 - shadow) * specular;
    color += base * uEmissive;
    fragColor = vec4(color, uAlpha);
}
"""

DEPTH_VERTEX_SHADER = """#version 330 core
layout(location = 0) in vec3 aPosition;
uniform mat4 uModel;
uniform mat4 uLightSpace;
void main() {
    gl_Position = uLightSpace * uModel * vec4(aPosition, 1.0);
}
"""

DEPTH_FRAGMENT_SHADER = """#version 330 core
void main() { }
"""
